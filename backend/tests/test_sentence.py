from unittest.mock import patch
from sqlalchemy import text, insert

from backend.db.models import Sentence
from backend.schemas import SentencePair


def seed_sentence(conn, target: str, lemma_count: int, known_word_ids: list[int]) -> int:
    # Mirrors what the generation pipeline stores: the sentence carries its full lemma count, but only lemmas matching the words table get a sentence_words row
    result = conn.execute(text("""
        INSERT INTO sentences (target, source, lemma_count)
        VALUES (:target, 'test sentence', :lemma_count)
        RETURNING id
    """), {"target": target, "lemma_count": lemma_count})   # sentences.target is unique, so each seeded sentence needs its own
    sentence_id = result.scalar()

    if known_word_ids:
        conn.execute(text("""
            INSERT INTO sentence_words (sentence_id, word_id)
            VALUES (:sentence_id, :word_id)
        """), [{"sentence_id": sentence_id, "word_id": word_id} for word_id in known_word_ids])

    return sentence_id


def test_get_sentence_batch(client, access_token, seed_user_words):
    # Must be at least 3 sentence, since 3 in a batch, and they must clear the known-word floor to be returned
    mock_sentences = [
        SentencePair(target="사람이 집에 갑니다.", source="The person goes home."),  # 3/3 lemmas known (사람, 집, 가다) = 100%
        SentencePair(target="사람이 집에서 물을 먹습니다.", source="The person drinks water at home."),  # 4/4 lemmas known (사람, 집, 물, 먹다) = 100%
        SentencePair(target="사람이 물을 먹고 집에 갔습니다.", source="The person drank water and went home."),  # 5/5 lemmas known (사람, 물, 먹다, 집, 가다) = 100%
    ]
    client.cookies.set("access_token", access_token)

    # Patched to avoid LLM API call
    with patch("backend.routers.sentence.generate_sentences", return_value=mock_sentences):
        response = client.post(f"/sentences", json={})

    assert response.status_code == 200
    data = response.json()
    assert "sentences" in data
    assert len(data["sentences"]) == 3
    returned_pairs = {(sentence["target"], sentence["source"]) for sentence in data["sentences"]}
    expected_pairs = {(mock_sentence.target, mock_sentence.source) for mock_sentence in mock_sentences}
    assert returned_pairs == expected_pairs  # Order isn't guaranteed since the eligibility query has no ORDER BY
    assert all(isinstance(sentence["id"], int) for sentence in data["sentences"])


def test_create_sentence_result(client, access_token, seed_session, conn):
    client.cookies.set("access_token", access_token)

    result = conn.execute(text(
        "INSERT INTO sentences (target, source, lemma_count) VALUES ('테스트', 'test', 1) RETURNING id"
    ))
    sentence_id = result.scalar()

    response = client.post(f"/sentence-results", json={"sentence_id": sentence_id, "session_id": seed_session, "status": "correct"})

    assert response.status_code == 200
    data = response.json()
    assert data["saved_sentence_id"] == sentence_id


def test_get_sentence_batch_excludes_completed_sentences(client, access_token, seed_user, seed_user_words, conn):
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
    """), {"user_id": seed_user, "sentence_id": completed_sentence_id})

    client.cookies.set("access_token", access_token)

    # 3 sentences stay eligible >= NUM_SENTENCES_IN_BATCH so that cache path is taken instead of LLM path
    response = client.post("/sentences", json={})

    assert response.status_code == 200
    data = response.json()
    returned_ids = [sentence["id"] for sentence in data["sentences"]]
    assert completed_sentence_id not in returned_ids
    for sentence_id in sentence_ids[1:]:
        assert sentence_id in returned_ids


def test_get_session_summary_excludes_skipped(client, access_token, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    answered_sentence_id = seed_sentence(conn, "물을 마십니다.", 2, seed_user_words[:2])
    skipped_sentence_id = seed_sentence(conn, "집에 갑니다.", 3, seed_user_words[2:5])

    client.post("/sentence-results", json={"sentence_id": answered_sentence_id, "session_id": seed_session, "status": "correct"})
    client.post("/sentence-results", json={"sentence_id": skipped_sentence_id, "session_id": seed_session, "status": "skipped"})

    response = client.get(f"/sentence-sessions/{seed_session}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 2  # Would be 5 if the skipped sentence's words were counted


def test_get_session_summary_counts_shared_word_once_per_sentence(client, access_token, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    shared_word_id = seed_user_words[0]
    first_sentence_id = seed_sentence(conn, "물을 마십니다.", 1, [shared_word_id])
    second_sentence_id = seed_sentence(conn, "물을 마셔요.", 1, [shared_word_id])

    client.post("/sentence-results", json={"sentence_id": first_sentence_id, "session_id": seed_session, "status": "correct"})
    client.post("/sentence-results", json={"sentence_id": second_sentence_id, "session_id": seed_session, "status": "correct"})

    response = client.get(f"/sentence-sessions/{seed_session}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 2  # The same word in two sentences is two reviews of it, matching how the vocab summary treats a repeated word


def test_get_session_summary_excludes_sentences_reviewed_in_an_earlier_session(client, access_token, seed_user, seed_session, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    result = conn.execute(text(
        "INSERT INTO sessions (user_id, bound_type, bound_value, session_type) VALUES (:user_id, 'count', 5, 'sentence') RETURNING id"
    ), {"user_id": seed_user})
    earlier_session_id = result.scalar()

    earlier_sentence_id = seed_sentence(conn, "어제 물을 마셨습니다.", 3, seed_user_words[:3])
    conn.execute(text("""
        INSERT INTO sentence_results (user_id, session_id, sentence_id, status)
        VALUES (:user_id, :session_id, :sentence_id, 'correct')
    """), {"user_id": seed_user, "session_id": earlier_session_id, "sentence_id": earlier_sentence_id})

    current_sentence_id = seed_sentence(conn, "밥을 먹습니다.", 1, seed_user_words[3:4])
    client.post("/sentence-results", json={"sentence_id": current_sentence_id, "session_id": seed_session, "status": "correct"})

    response = client.get(f"/sentence-sessions/{seed_session}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 1  # Would be 4 if the earlier session's sentence leaked into this session's count


def test_get_session_summary_excludes_other_users_data(client, access_token, seed_user_words, conn):
    client.cookies.set("access_token", access_token)

    result = conn.execute(text(
        "INSERT INTO users (google_sub, email) VALUES ('other-sub', 'other@email.com') RETURNING id"
    ))
    other_user_id = result.scalar()

    result = conn.execute(text(
        "INSERT INTO sessions (user_id, bound_type, bound_value, session_type) VALUES (:user_id, 'count', 5, 'sentence') RETURNING id"
    ), {"user_id": other_user_id})
    other_session_id = result.scalar()

    other_sentence_id = seed_sentence(conn, "물을 마십니다.", 2, seed_user_words[:2])
    conn.execute(text("""
        INSERT INTO sentence_results (user_id, session_id, sentence_id, status)
        VALUES (:user_id, :session_id, :sentence_id, 'correct')
    """), {"user_id": other_user_id, "session_id": other_session_id, "sentence_id": other_sentence_id})

    response = client.get(f"/sentence-sessions/{other_session_id}/summary")
    data = response.json()

    assert response.status_code == 200
    assert data["summary"]["total_reviewed"] == 0  # Session belongs to another user, not the authenticated one. There is no explicit check that session belongs to the requester, however it filters for the requester's user_id
