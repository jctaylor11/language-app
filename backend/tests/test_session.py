from fastapi.testclient import TestClient

def test_create_session(client):
    response = client.post("/sessions?user_id=1")
    assert response.status_code == 200
    assert "session_id" in response.json()