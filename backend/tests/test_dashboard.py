from sqlalchemy import text

from backend.tests.conftest import TEST_USER_WORD_COUNT, seed_sentence

def test_get_dashboard_words(client, access_token, seed_user_words):
    expected_keys = ["id", "target", "source", "times_reviewed", "av_s_per_syllable", "accuracy"]

    client.cookies.set("access_token", access_token)
    response = client.get(f"/dashboard/words")
    assert response.status_code == 200
    data = response.json()
    words = data["words"]
    word = words[0]

    for key in expected_keys:
        assert key in word
    assert len(words) == TEST_USER_WORD_COUNT
    assert word["times_reviewed"] == 0
    assert word["accuracy"] is None


def test_get_dashboard_words_for_empty_user(client, access_token):
    client.cookies.set("access_token", access_token)
    response = client.get(f"/dashboard/words")
    assert response.status_code == 200
    data = response.json()
    words = data["words"]

    assert len(words) == 0


def test_get_dashboard_hero_metrics(client, access_token, seed_user_words):
    client.cookies.set("access_token", access_token)
    response = client.get(f"/dashboard/hero-metrics")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    assert metrics["total_words"] == TEST_USER_WORD_COUNT
    assert metrics["words_reviewed"] == 0


def test_get_dashboard_hero_metrics_for_empty_user(client, access_token):
    client.cookies.set("access_token", access_token)
    response = client.get(f"/dashboard/hero-metrics")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    assert metrics["total_words"] == 0
    assert metrics["words_reviewed"] == 0


def test_get_dashboard_hero_metrics_excludes_skipped_and_cheated_words(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :cheated_word_id, 1500, '2026-08-30T10:00:00', 'cheated', 1),
               (:user_id, :session_id, :skipped_word_id, 400, '2026-08-30T10:00:03', 'skipped', 2),
               (:user_id, :session_id, :recalled_word_id, 900, '2026-08-30T10:00:05', 'correct_first_try', 3)
    """), {"user_id": seed_user, "session_id": seed_session, "cheated_word_id": seed_user_words[0], "skipped_word_id": seed_user_words[1], "recalled_word_id": seed_user_words[2]})

    response = client.get(f"/dashboard/hero-metrics")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    assert metrics["words_reviewed"] == 1  # Would be 3 if the cheated and skipped words counted, only the recalled one is earned


def test_get_dashboard_hero_metrics_excludes_skipped_and_cheated_sentences(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    answered_sentence_id = seed_sentence(conn, "물을 마십니다.", 2, seed_user_words[:2])
    skipped_sentence_id = seed_sentence(conn, "집에 갑니다.", 3, seed_user_words[2:5])
    cheated_sentence_id = seed_sentence(conn, "오늘 밥을 먹습니다.", 3, seed_user_words[3:6])

    conn.execute(text("""
        INSERT INTO sentence_results (user_id, session_id, sentence_id, status)
        VALUES (:user_id, :session_id, :sentence_id, :status)
    """), [
        {"user_id": seed_user, "session_id": seed_session, "sentence_id": answered_sentence_id, "status": "correct"},
        {"user_id": seed_user, "session_id": seed_session, "sentence_id": skipped_sentence_id, "status": "skipped"},
        {"user_id": seed_user, "session_id": seed_session, "sentence_id": cheated_sentence_id, "status": "cheated"},
    ])

    response = client.get(f"/dashboard/hero-metrics")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    assert metrics["words_reviewed"] == 2  # Would be 8 if the skipped and cheated sentences' words counted


def test_get_dashboard_words_times_reviewed_excludes_skipped_and_cheated(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    reviewed_word_id = seed_user_words[0]   # Same word three times, so the count isolates the status filter rather than the word
    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :word_id, 900, '2026-08-30T10:00:00', 'correct_first_try', 1),
               (:user_id, :session_id, :word_id, 400, '2026-08-30T10:00:03', 'skipped', 2),
               (:user_id, :session_id, :word_id, 1500, '2026-08-30T10:00:06', 'cheated', 3)
    """), {"user_id": seed_user, "session_id": seed_session, "word_id": reviewed_word_id})

    response = client.get(f"/dashboard/words")
    assert response.status_code == 200
    data = response.json()
    word = next(word for word in data["words"] if word["id"] == reviewed_word_id)

    assert word["times_reviewed"] == 1  # Would be 3 if the skipped and cheated results counted as reviews
    assert word["accuracy"] == 1 / 3    # Denominator intentionally stays every result, so skipping and cheating count against accuracy rather than raising it


def test_get_word_chart_data(client, access_token, seed_user_words):
    client.cookies.set("access_token", access_token)
    response = client.get(f"/dashboard/word-chart-data")
    assert response.status_code == 200
    data = response.json()
    cumulative_words = data["cumulative_words"]

    assert len(cumulative_words) == 2   # Range starts the day before the earliest added_at, so today's words show a zero-indexed jump
    assert cumulative_words[0]["cum_words"] == 0
    assert cumulative_words[-1]["cum_words"] == TEST_USER_WORD_COUNT


def test_get_word_chart_data_for_empty_user(client, access_token):
    client.cookies.set("access_token", access_token)
    response = client.get(f"/dashboard/word-chart-data")
    assert response.status_code == 200
    data = response.json()
    cumulative_words = data["cumulative_words"]

    assert cumulative_words == []   # No user_words rows means no MIN(added_at) to anchor the range
