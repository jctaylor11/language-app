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
