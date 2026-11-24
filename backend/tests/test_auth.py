from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from sqlalchemy import text


@pytest.fixture
def mock_google():
    google_result = {"status": True, "user_infos": {"google_sub": "waitlist-sub", "email": "waitlist@email.com"}}
    with patch("backend.routers.auth.get_user_infos_from_google_token", return_value=google_result):
        yield


def test_unapproved_email_is_waitlisted_not_signed_in(client, conn, mock_google):
    response = client.post("/auth-google", json={"credential": "fake-google-credential"})

    users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
    waitlist = conn.execute(text("SELECT COUNT(*) FROM waitlist WHERE email = 'waitlist@email.com'")).scalar()

    assert response.json()["status"] == "waitlisted"
    assert "access_token" not in response.cookies
    assert users == 0
    assert waitlist == 1


def test_waitlisted_email_signs_in_once_approved(client, conn, mock_google):
    client.post("/auth-google", json={"credential": "fake-google-credential"})
    client.post("/auth-google", json={"credential": "fake-google-credential"})   # Repeat attempt shouldn't duplicate the row
    waitlist = conn.execute(text("SELECT COUNT(*) FROM waitlist")).scalar()

    conn.execute(text("UPDATE waitlist SET approved = true"))
    response = client.post("/auth-google", json={"credential": "fake-google-credential"})

    assert waitlist == 1
    assert response.json()["status"] == "ok"
    assert "access_token" in response.cookies


def test_refresh_rotates_token(client, refresh_token):
    client.cookies.set("refresh_token", refresh_token)
    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert response.cookies["refresh_token"] != refresh_token


def test_refresh_issues_a_working_access_token(client, refresh_token):
    client.cookies.set("refresh_token", refresh_token)
    client.post("/auth/refresh")

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["authenticated"] is True


def test_refresh_rejects_reused_token(client, refresh_token):
    client.cookies.set("refresh_token", refresh_token)
    first_response = client.post("/auth/refresh")
    client.cookies.set("refresh_token", refresh_token)  # Reset to the rotated-out token
    second_response = client.post("/auth/refresh")

    assert first_response.status_code == 200
    assert second_response.status_code == 401


def test_concurrent_refresh_with_same_token_only_succeeds_once(concurrent_clients, concurrent_refresh_token):
    # Two real connections hitting /auth/refresh with the same token at once. The FOR UPDATE should serialise them: one wins (200), the other sees the token already rotated away (401)
    first_client, second_client = concurrent_clients
    first_client.cookies.set("refresh_token", concurrent_refresh_token)
    second_client.cookies.set("refresh_token", concurrent_refresh_token)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_call = executor.submit(first_client.post, "/auth/refresh")
        second_call = executor.submit(second_client.post, "/auth/refresh")
        first_response = first_call.result()
        second_response = second_call.result()        

    status_codes = {first_response.status_code, second_response.status_code}
    assert status_codes == {200, 401}   # Intentionally order-agnostic otherwise may occassionally fail
