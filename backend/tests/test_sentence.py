from sqlalchemy import text


# TODO: add test_get_sentence_batch once POST /sentences is refactored to inject
# read_conn and write_conn instead of engine (see TODO in sentence.py)


def test_create_sentence_result(client, conn, seed_user):
    result = conn.execute(text(
        "INSERT INTO sentences (target, source, lemma_count) VALUES ('테스트', 'test', 1) RETURNING id"
    ))
    sentence_id = result.scalar()

    response = client.post(f"/sentence-results?user_id=1", json={"sentence_id": sentence_id, "status": "correct"})

    assert response.status_code == 200
    assert response.json()["saved_sentence_id"] == sentence_id
