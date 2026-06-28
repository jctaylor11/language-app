from backend.tests.conftest import TEST_USER_ID

def test_create_session(client, seed_user):
    response = client.post(f"/sessions?user_id={TEST_USER_ID}")
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert isinstance(response.json()["session_id"], int)
