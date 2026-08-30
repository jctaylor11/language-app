from sqlalchemy import text

from backend.tests.conftest import TEST_USER_WORD_COUNT

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


def test_get_dashboard_hero_metrics_excludes_cheated(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :cheated_word_id, 1500, '2026-08-30T10:00:00', 'cheated', 1),
               (:user_id, :session_id, :recalled_word_id, 900, '2026-08-30T10:00:05', 'correct_first_try', 2)
    """), {"user_id": seed_user, "session_id": seed_session, "cheated_word_id": seed_user_words[0], "recalled_word_id": seed_user_words[1]})

    response = client.get(f"/dashboard/hero-metrics")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    assert metrics["words_reviewed"] == 1  # The cheated word is excluded, only the recalled one counts


def test_get_word_chart_data(client, access_token, seed_user_words):
    client.cookies.set("access_token", access_token)
    response = client.get(f"/dashboard/word-chart-data")
    assert response.status_code == 200
    data = response.json()
    cumulative_words = data["cumulative_words"]

    assert len(cumulative_words) == 30
    assert cumulative_words[-1]["cum_words"] == TEST_USER_WORD_COUNT


def test_get_word_chart_data_for_empty_user(client, access_token):
    client.cookies.set("access_token", access_token)
    response = client.get(f"/dashboard/word-chart-data")
    assert response.status_code == 200
    data = response.json()
    cumulative_words = data["cumulative_words"]

    assert len(cumulative_words) == 30
    assert all(day["cum_words"] == 0 for day in cumulative_words)
