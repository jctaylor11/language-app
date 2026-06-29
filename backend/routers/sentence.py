from fastapi import APIRouter, Depends
from sqlalchemy import text, insert, Connection
from typing import Annotated

from backend.db.connection import get_read_connection, get_write_connection
from backend.llm import generate_sentences
from backend.lemmatiser import extract_lemmas
from backend.db.models import Sentence
from backend.enums import SentenceResultStatus
from backend.schemas import SentenceResult, SentenceBatchRequest, SentencePair

router = APIRouter()


def sample_user_words(conn: Connection, user_id: int, num_words: int) -> list[str]:
    result = conn.execute(text("""
        SELECT target
        FROM words
        JOIN user_words ON user_words.word_id = words.id
        WHERE user_id = :user_id
        ORDER BY RANDOM()
        LIMIT :num_words
    """), {"user_id": user_id, "num_words": num_words})

    rows = result.fetchall()

    user_words = [row.target for row in rows]

    return user_words


def get_eligible_sentences(conn: Connection, user_id: int, user_words: list[str]) -> list[SentencePair]:      # TODO: User user_words logic to find suitable words, rather than taking any
    eligible_sentences = conn.execute(text("""
    SELECT s.id, s.target, s.source
    FROM sentences s
    WHERE NOT EXISTS (
        SELECT 1
        FROM sentence_results sr
        WHERE sr.sentence_id = s.id
        AND sr.user_id = :user_id
    )
    LIMIT 50    -- Fetch many eligible in one batch for the session since free from database (rather than LLM)
    """), {"user_id": user_id}).fetchall()

    sentences = [SentencePair(id=row.id, target=row.target, source=row.source) for row in eligible_sentences]

    return sentences    


def lemmatise_sentences(sentences: list[SentencePair]) -> list[SentencePair]:
    for sentence in sentences:
        sentence.lemmas = extract_lemmas(sentence.target)

    return sentences


def insert_sentences(conn: Connection, sentences: list[SentencePair]) -> list[SentencePair]:
    result = conn.execute(insert(Sentence).returning(Sentence.id),    # Core with expression language used to handle multi-rows
        [{"target": sentence.target, "source": sentence.source, "lemma_count": len(sentence.lemmas)} for sentence in sentences])

    sentence_ids = result.fetchall()

    for sentence, row in zip(sentences, sentence_ids):  # Positional order of sentences in matching sentences out is guaranteed by the insert() statement with the list of dicts and returning statement
        sentence.id = row.id

    return sentences


def insert_sentences_words(conn: Connection, sentences: list[SentencePair]) -> None:
    all_lemmas_in_sentence = set()
    for sentence in sentences:
        for lemma in sentence.lemmas:
            all_lemmas_in_sentence.add(lemma)
    all_lemmas_in_sentence = list(all_lemmas_in_sentence)

    # Word IDs are queried so the words corresponding to each sentence can be inserted into sentence_words table
    result = conn.execute(text("""
        SELECT id, target FROM words
        WHERE target = ANY(:lemmas)
        """), {"lemmas": all_lemmas_in_sentence})

    # Mapping lemmas to the word ID so we can map which words are in each sentence, reference in citation form
    lemma_to_word_id = {row.target: row.id for row in result}

    # Assembling list of row objects to insert in sentence_words table
    sentence_word_mappings = []
    for sentence in sentences: 
        for lemma in sentence.lemmas:           
            if lemma in lemma_to_word_id:       # Sentence lemmas may not all be in vocab table (hence will have no ID)
                sentence_word_mappings.append({"sentence_id": sentence.id, "word_id": lemma_to_word_id[lemma]})

    # Record which word IDs are in each sentence to track which words have been reviewed by the user when they review each sentence
    if sentence_word_mappings:
        conn.execute(text("""
            INSERT INTO sentence_words (sentence_id, word_id)
            VALUES (:sentence_id, :word_id)
            ON CONFLICT DO NOTHING
        """), sentence_word_mappings)


@router.post("/sentences")
def get_sentence_batch(
    user_id: int,
    payload: SentenceBatchRequest,
    read_conn: Annotated[Connection, Depends(get_read_connection)],
    write_conn: Annotated[Connection, Depends(get_write_connection)],
):
    """Returns a batch of sentences for the user.

    First serves any applicable sentences that already exist in the cached sentences. If none applicable exist, it generates new sentences via LLM API,
    lemmatises them, and inserts the sentences and associated data into the sentences cache.
    """
    user_words = sample_user_words(read_conn, user_id, payload.num_words)
    eligible_sentences = get_eligible_sentences(read_conn, user_id, user_words)   # TODO: Add logic for finding sentences having user_words. Current fetches any not-done

    if len(eligible_sentences) > 3:
        return {"sentences": [{"id": sentence.id, "target": sentence.target, "source": sentence.source} for sentence in eligible_sentences]}    # Early return since sentences from db are already lemmatised

    sentences = generate_sentences(user_words)  # If no eligible sentences already exist in the sentences cache

    sentences = lemmatise_sentences(sentences)  # Lemmatisation allows sentence words to be matched against the words table by standardised citation form. Needed for sentence_words inserts and lemma_count

    sentences = insert_sentences(write_conn, sentences)  # Returns with IDs
    insert_sentences_words(write_conn, sentences)

    return {"sentences": [{"id": row.id, "target": row.target, "source": row.source} for row in sentences]}


def insert_sentence_result(conn: Connection, user_id: int, sentence_id: int, status: SentenceResultStatus) -> None:
    conn.execute(text("""
        INSERT INTO sentence_results (user_id, sentence_id, status)
        VALUES (:user_id, :sentence_id, :status)
    """), {"user_id": user_id, "sentence_id": sentence_id, "status": status.value})


@router.post("/sentence-results")
def create_sentence_result(user_id: int, payload: SentenceResult, conn: Annotated[Connection, Depends(get_write_connection)]):      # TODO: batch these and send via beacon on page close
    """Records the user's result for a single reviewed sentence."""
    insert_sentence_result(conn, user_id, payload.sentence_id, payload.status)

    return {"saved_sentence_id": payload.sentence_id}
