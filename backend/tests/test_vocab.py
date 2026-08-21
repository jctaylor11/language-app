from sqlalchemy import text


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
        "session_id": seed_session,
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


def test_get_session_summary_excludes_skipped(client, access_token, seed_session, seed_user_words):
    client.cookies.set("access_token", access_token)
    body = {
        "session_id": seed_session,
        "word_results": [
            {
                "word_id": seed_user_words[0],
                "response_time_ms": 1500,
                "answered_at": "2026-06-27T10:00:00",
                "raw_keystrokes": None,
                "status": "correct_first_try",
                "session_position": 1
            },
            {
                "word_id": seed_user_words[1],
                "response_time_ms": 2000,
                "answered_at": "2026-06-27T10:00:05",
                "raw_keystrokes": None,
                "status": "skipped",
                "session_position": 2
            }
        ]
    }
    client.post(f"/vocab-results", json=body)

    response = client.get(f"/vocab-sessions/{seed_session}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 1  # Would be 2 if the skipped result were counted
    assert data["summary"]["new_words"] == 1  # Would be 2 if the skipped word were counted


def test_get_session_summary_counts_repeat_word_as_two_reviews(client, access_token, seed_session, seed_user_words):
    client.cookies.set("access_token", access_token)
    body = {
        "session_id": seed_session,
        "word_results": [
            {
                "word_id": seed_user_words[0],
                "response_time_ms": 1500,
                "answered_at": "2026-06-27T10:00:00",
                "raw_keystrokes": None,
                "status": "correct_first_try",
                "session_position": 1
            },
            {
                "word_id": seed_user_words[0],
                "response_time_ms": 1800,
                "answered_at": "2026-06-27T10:00:05",
                "raw_keystrokes": None,
                "status": "correct_first_try",
                "session_position": 2
            }
        ]
    }
    client.post(f"/vocab-results", json=body)

    response = client.get(f"/vocab-sessions/{seed_session}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 2  # Same word twice still counts as two reviews
    assert data["summary"]["new_words"] == 1  # But only one distinct word, so only one new word


def test_get_session_summary_excludes_words_answered_in_an_earlier_session(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    earlier_session_id = conn.execute(text(
        "INSERT INTO sessions (user_id, bound_type, bound_value, session_type) VALUES (:user_id, 'time', 120, 'vocab') RETURNING id"
    ), {"user_id": seed_user}).scalar()

    # Word answered correctly in an earlier session, well before the current session started
    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :word_id, 1500, '2020-01-01T00:00:00', 'correct_first_try', 1)
    """), {"user_id": seed_user, "session_id": earlier_session_id, "word_id": seed_user_words[0]})

    # Same word answered again in the current session
    body = {
        "session_id": seed_session,
        "word_results": [
            {
                "word_id": seed_user_words[0],
                "response_time_ms": 1200,
                "answered_at": "2026-06-27T10:00:00",
                "raw_keystrokes": None,
                "status": "correct_first_try",
                "session_position": 1
            }
        ]
    }
    client.post(f"/vocab-results", json=body)

    response = client.get(f"/vocab-sessions/{seed_session}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 1
    assert data["summary"]["new_words"] == 0  # Already answered correctly in an earlier session, so not new this time


def test_get_session_summary_excludes_other_users_data(client, access_token, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    other_user_id = conn.execute(text(
        "INSERT INTO users (google_sub, email) VALUES ('other-sub', 'other@email.com') RETURNING id"
    )).scalar()

    other_session_id = conn.execute(text(
        "INSERT INTO sessions (user_id, bound_type, bound_value, session_type) VALUES (:user_id, 'time', 120, 'vocab') RETURNING id"
    ), {"user_id": other_user_id}).scalar()

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :word_id, 1500, '2026-06-27T10:00:00', 'correct_first_try', 1)
    """), {"user_id": other_user_id, "session_id": other_session_id, "word_id": seed_user_words[0]})

    response = client.get(f"/vocab-sessions/{other_session_id}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 0  # Session belongs to another user, not the authenticated one. There is no explicit check that session belongs to the requester, however it filters for the requester's user_id
    assert data["summary"]["new_words"] == 0


def test_get_session_summary_counts_previously_skipped_word_as_new(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    earlier_session_id = conn.execute(text(
        "INSERT INTO sessions (user_id, bound_type, bound_value, session_type) VALUES (:user_id, 'time', 120, 'vocab') RETURNING id"
    ), {"user_id": seed_user}).scalar()

    # Word only skipped in an earlier session - a skip shouldn't count as "already known"
    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :word_id, 1500, '2020-01-01T00:00:00', 'skipped', 1)
    """), {"user_id": seed_user, "session_id": earlier_session_id, "word_id": seed_user_words[0]})

    # Same word answered correctly for the first time in the current session
    body = {
        "session_id": seed_session,
        "word_results": [
            {
                "word_id": seed_user_words[0],
                "response_time_ms": 1200,
                "answered_at": "2026-06-27T10:00:00",
                "raw_keystrokes": None,
                "status": "correct_first_try",
                "session_position": 1
            }
        ]
    }
    client.post(f"/vocab-results", json=body)

    response = client.get(f"/vocab-sessions/{seed_session}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 1
    assert data["summary"]["new_words"] == 1  # A prior skip doesn't count as already known, so it's still new
    