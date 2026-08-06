def test_create_session(client, access_token):
    client.cookies.set("access_token", access_token)
    response = client.post(f"/sessions", json={"bound_type": "time", "bound_value": 120})
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert isinstance(response.json()["session_id"], int)
