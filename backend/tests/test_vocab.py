from backend.tests.conftest import TEST_SESSION_ID

def test_get_word_batch(client, access_token, seed_user_words):
    client.cookies.set("access_token", access_token)  # access token is sent over httpOnly cookie
    response = client.get(f"/words")
    data = response.json()
    assert response.status_code == 200
    assert "word_batch" in data
    assert all("id" in word and "target" in word and "source" in word for word in data["word_batch"])
    assert len(data["word_batch"]) == 5 # Limited to 5 by endpoint query's LIMIT
    

def test_create_vocab_results(client, access_token, seed_session, seed_user_words):
    client.cookies.set("access_token", access_token)
    body = {
        "session_id": TEST_SESSION_ID,
        "word_results": [
            {
                "word_id": seed_user_words[0],
                "response_time_ms": 1500,
                "answered_at": "2026-06-27T10:00:00",
                "raw_keystrokes": "hello",
                "status": "correct_first_try",
                "session_position": 1
            }
        ]
    }

    response = client.post(f"/vocab-results", json=body)
    data = response.json()

    assert response.status_code == 200
    assert data["results_saved"] == 1