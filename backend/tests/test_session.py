from sqlalchemy import text

from backend.tests.conftest import seed_sentence


def test_create_session(client, access_token):
    client.cookies.set("access_token", access_token)
    response = client.post(f"/sessions", json={"bound_type": "time", "bound_value": 120, "session_type": "vocab"})
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert isinstance(response.json()["session_id"], int)


def test_get_session_overview_includes_peeked_but_not_skipped(client, access_token, seed_user, seed_session, seed_words, conn):
    client.cookies.set("access_token", access_token)

    peeked_word_id = seed_words[0]
    skipped_word_id = seed_words[1]

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :peeked_word_id, 1500, '2026-08-30T10:00:00', 'peeked', 1),
               (:user_id, :session_id, :skipped_word_id, 800, '2026-08-30T10:00:05', 'skipped', 2)
    """), {"user_id": seed_user, "session_id": seed_session, "peeked_word_id": peeked_word_id, "skipped_word_id": skipped_word_id})

    targets = conn.execute(text("SELECT id, target FROM words WHERE id IN (:peeked_word_id, :skipped_word_id)"), {"peeked_word_id": peeked_word_id, "skipped_word_id": skipped_word_id})
    target_by_id = {row.id: row.target for row in targets.fetchall()}

    response = client.get(f"/sessions/overview/{seed_session}")
    data = response.json()

    assert response.status_code == 200
    assert target_by_id[peeked_word_id] in data["session_overview"]  # Peeked words are present in the overview of the words done 
    assert target_by_id[skipped_word_id] not in data["session_overview"]


def test_get_session_log_excludes_peeked_from_total_reviewed(client, access_token, seed_user, seed_session, seed_words, conn):
    client.cookies.set("access_token", access_token)

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :peeked_word_id, 1500, '2026-08-30T10:00:00', 'peeked', 1),
               (:user_id, :session_id, :recalled_word_id, 900, '2026-08-30T10:00:05', 'correct_first_try', 2)
    """), {"user_id": seed_user, "session_id": seed_session, "peeked_word_id": seed_words[0], "recalled_word_id": seed_words[1]})

    response = client.get("/sessions/log")
    data = response.json()

    assert response.status_code == 200
    session_row = data["session_log"][0]
    assert session_row["total_reviewed"] == 1  # The peeked word is excluded, only the recalled one counts


def test_get_session_log_excludes_another_users_results_in_own_session(client, access_token, seed_user, seed_session, seed_words, conn):
    client.cookies.set("access_token", access_token)

    other_user_id = conn.execute(text(
        "INSERT INTO users (google_sub, email) VALUES ('other-sub', 'other@email.com') RETURNING id"
    )).scalar()

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:other_user_id, :session_id, :foreign_word_id, 1500, '2026-08-30T10:00:00', 'correct_first_try', 1),
               (:user_id, :session_id, :own_word_id, 900, '2026-08-30T10:00:05', 'correct_first_try', 2)
    """), {"user_id": seed_user, "other_user_id": other_user_id, "session_id": seed_session, "foreign_word_id": seed_words[0], "own_word_id": seed_words[1]})

    response = client.get("/sessions/log")
    data = response.json()

    assert response.status_code == 200
    session_row = next(row for row in data["session_log"] if row["session_id"] == seed_session)
    assert session_row["total_reviewed"] == 1  # Joining on the session alone would count the other user's result too


def test_get_session_log_excludes_peeked_sentences_from_total_reviewed(client, access_token, seed_user, seed_words, conn):
    client.cookies.set("access_token", access_token)

    result = conn.execute(text(
        "INSERT INTO sessions (user_id, bound_type, bound_value, session_type) VALUES (:user_id, 'count', 5, 'sentence') RETURNING id"
    ), {"user_id": seed_user})
    sentence_session_id = result.scalar()

    answered_sentence_id = seed_sentence(conn, "물을 마십니다.", 2, seed_words[:2])  # lemma count as literals as it doesn't need to be accurate for test - not what's tested. Could be anything - but written to match the number of word IDs inserts    
    peeked_sentence_id = seed_sentence(conn, "집에 갑니다.", 3, seed_words[:3])

    # Uses conn instead of client to tap directly into SQL for arrangement, since we're not testing that endpoint
    conn.execute(text("""
        INSERT INTO sentence_results (user_id, session_id, sentence_id, status)
        VALUES (:user_id, :session_id, :sentence_id, :status)
    """), [
        {"user_id": seed_user, "session_id": sentence_session_id, "sentence_id": answered_sentence_id, "status": "correct"},
        {"user_id": seed_user, "session_id": sentence_session_id, "sentence_id": peeked_sentence_id, "status": "peeked"},
    ])

    response = client.get("/sessions/log")
    data = response.json()

    assert response.status_code == 200
    session_row = next(row for row in data["session_log"] if row["session_id"] == sentence_session_id)
    assert session_row["total_reviewed"] == 2  # Would be 5 if the peeked sentence's words counted, matching how the vocab branch treats a peeked word
