from unittest.mock import patch
from sqlalchemy import text

from backend.schemas import SentencePair


def test_get_sentence_batch(client, access_token, seed_user_words):
    mock_sentences = [SentencePair(target="우리는 매일 물을 마십니다.", source="We drink water every day.")]
    client.cookies.set("access_token", access_token)

    with patch("backend.routers.sentence.generate_sentences", return_value=mock_sentences):
        response = client.post(f"/sentences", json={"num_words": 3})

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
