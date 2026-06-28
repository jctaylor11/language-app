from backend.tests.conftest import TEST_USER_WORD_COUNT, TEST_USER_ID

def test_get_dashboard_words(client, seed_user_words):
    expected_keys = ["id", "target", "source", "times_reviewed", "av_s_per_syllable", "accuracy"]

    response = client.get(f"/dashboard/words?user_id={TEST_USER_ID}")
    assert response.status_code == 200
    data = response.json()
    words = data["words"]
    word = words[0]

    for key in expected_keys:
        assert key in word
    assert len(words) == TEST_USER_WORD_COUNT
    assert word["times_reviewed"] == 0
    assert word["accuracy"] is None


def test_get_dashboard_words_for_empty_user(client, seed_user):
    response = client.get(f"/dashboard/words?user_id={TEST_USER_ID}")
    assert response.status_code == 200
    data = response.json()
    words = data["words"]

    assert len(words) == 0


def test_get_dashboard_hero_metrics(client, seed_user_words):
    response = client.get(f"/dashboard/hero-metrics?user_id={TEST_USER_ID}")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    assert metrics["total_words"] == TEST_USER_WORD_COUNT
    assert metrics["words_reviewed"] == 0


def test_get_dashboard_hero_metrics_for_empty_user(client, seed_user):
    response = client.get(f"/dashboard/hero-metrics?user_id={TEST_USER_ID}")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    assert metrics["total_words"] == 0
    assert metrics["words_reviewed"] == 0


def test_get_word_chart_data(client, seed_user_words):
    response = client.get(f"/dashboard/word-chart-data?user_id={TEST_USER_ID}")
    assert response.status_code == 200
    data = response.json()
    cumulative_words = data["cumulative_words"]

    assert len(cumulative_words) == 30
    assert cumulative_words[-1]["cum_words"] == TEST_USER_WORD_COUNT


def test_get_word_chart_data_for_empty_user(client, seed_user):
    response = client.get(f"/dashboard/word-chart-data?user_id={TEST_USER_ID}")
    assert response.status_code == 200
    data = response.json()
    cumulative_words = data["cumulative_words"]

    assert len(cumulative_words) == 30
    assert all(day["cum_words"] == 0 for day in cumulative_words)
