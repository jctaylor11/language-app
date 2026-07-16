from concurrent.futures import ThreadPoolExecutor


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
