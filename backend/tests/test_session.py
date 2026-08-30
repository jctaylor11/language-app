from sqlalchemy import text


def test_create_session(client, access_token):
    client.cookies.set("access_token", access_token)
    response = client.post(f"/sessions", json={"bound_type": "time", "bound_value": 120, "session_type": "vocab"})
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert isinstance(response.json()["session_id"], int)


def test_get_session_overview_includes_cheated_but_not_skipped(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    cheated_word_id = seed_user_words[0]
    skipped_word_id = seed_user_words[1]

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :cheated_word_id, 1500, '2026-08-30T10:00:00', 'cheated', 1),
               (:user_id, :session_id, :skipped_word_id, 800, '2026-08-30T10:00:05', 'skipped', 2)
    """), {"user_id": seed_user, "session_id": seed_session, "cheated_word_id": cheated_word_id, "skipped_word_id": skipped_word_id})

    targets = conn.execute(text("SELECT id, target FROM words WHERE id IN (:cheated_word_id, :skipped_word_id)"), {"cheated_word_id": cheated_word_id, "skipped_word_id": skipped_word_id})
    target_by_id = {row.id: row.target for row in targets.fetchall()}

    response = client.get(f"/sessions/overview/{seed_session}")
    data = response.json()

    assert response.status_code == 200
    assert target_by_id[cheated_word_id] in data["session_overview"]  # Cheated words are present in the overview of the words done 
    assert target_by_id[skipped_word_id] not in data["session_overview"]


def test_get_session_log_excludes_cheated_from_total_reviewed(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :cheated_word_id, 1500, '2026-08-30T10:00:00', 'cheated', 1),
               (:user_id, :session_id, :recalled_word_id, 900, '2026-08-30T10:00:05', 'correct_first_try', 2)
    """), {"user_id": seed_user, "session_id": seed_session, "cheated_word_id": seed_user_words[0], "recalled_word_id": seed_user_words[1]})

    response = client.get("/sessions/log")
    data = response.json()

    assert response.status_code == 200
    session_row = data["session_log"][0]
    assert session_row["total_reviewed"] == 1  # The cheated word is excluded, only the recalled one counts
