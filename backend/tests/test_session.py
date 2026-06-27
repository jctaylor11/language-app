def test_create_session(client, seed_user):
    response = client.post("/sessions?user_id=1")
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert isinstance(response.json()["session_id"], int)
