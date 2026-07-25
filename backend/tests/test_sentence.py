from unittest.mock import patch
from sqlalchemy import text, insert

from backend.db.models import Sentence
from backend.schemas import SentencePair
from backend.tests.conftest import TEST_USER_ID


def test_get_sentence_batch(client, access_token, seed_user_words):
    mock_sentences = [SentencePair(target="우리는 매일 물을 마십니다.", source="We drink water every day.")]
    client.cookies.set("access_token", access_token)

    with patch("backend.routers.sentence.generate_sentences", return_value=mock_sentences):
        response = client.post(f"/sentences", json={"known_proportion": 80})

    assert response.status_code == 200
    data = response.json()
    assert "sentences" in data
    assert len(data["sentences"]) == 1
    sentence = data["sentences"][0]
    assert isinstance(sentence["id"], int)
    assert sentence["target"] == mock_sentences[0].target
    assert sentence["source"] == mock_sentences[0].source


def test_create_sentence_result(client, access_token, conn):
    client.cookies.set("access_token", access_token)

    result = conn.execute(text(
        "INSERT INTO sentences (target, source, lemma_count) VALUES ('테스트', 'test', 1) RETURNING id"
    ))
    sentence_id = result.scalar()

    response = client.post(f"/sentence-results", json={"sentence_id": sentence_id, "status": "correct"})

    assert response.status_code == 200
    data = response.json()
    assert data["saved_sentence_id"] == sentence_id


def test_get_sentence_batch_excludes_completed_sentences(client, access_token, seed_user_words, conn):
    known_word_id = seed_user_words[0]  # One known word is all the coverage maths needs - each sentence has lemma_count 1 and that word as its only lemma

    result = conn.execute(insert(Sentence).returning(Sentence.id), [
        {"target": "물을 마십니다.", "source": "I drink water.", "lemma_count": 1},
        {"target": "밥을 먹습니다.", "source": "I eat a meal.", "lemma_count": 1},
        {"target": "물을 마셔요.", "source": "I drink water.", "lemma_count": 1},
        {"target": "밥을 먹어요.", "source": "I eat a meal.", "lemma_count": 1},
    ])
    sentence_ids = [row.id for row in result.fetchall()]

    # One known word per sentence == 100% coverage which clears the HAVING threshold
    conn.execute(text("""
        INSERT INTO sentence_words (sentence_id, word_id)
        VALUES (:sentence_id, :word_id)
    """), [{"sentence_id": sentence_id, "word_id": known_word_id} for sentence_id in sentence_ids])

    completed_sentence_id = sentence_ids[0]
    conn.execute(text("""
        INSERT INTO sentence_results (user_id, sentence_id, status)
        VALUES (:user_id, :sentence_id, 'correct')
    """), {"user_id": TEST_USER_ID, "sentence_id": completed_sentence_id})

    client.cookies.set("access_token", access_token)

    # 3 sentences stay eligible >= NUM_SENTENCES_IN_BATCH so that cache path is taken instead of LLM path
    response = client.post("/sentences", json={"known_proportion": 80})

    assert response.status_code == 200
    data = response.json()
    returned_ids = [sentence["id"] for sentence in data["sentences"]]
    assert completed_sentence_id not in returned_ids
    for sentence_id in sentence_ids[1:]:
        assert sentence_id in returned_ids

