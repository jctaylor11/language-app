from fastapi import APIRouter, Depends
from sqlalchemy import text, insert, Connection
from typing import Annotated

from backend.auth.access_token import decode_access_token
from backend.db.connection import get_read_connection, get_write_connection
from backend.llm import generate_sentences
from backend.lemmatiser import extract_lemmas
from backend.db.models import Sentence
from backend.enums import SentenceResultStatus
from backend.schemas import SentenceResult, SentencePair, SentenceRequest

router = APIRouter()

NUM_WORDS_SAMPLED = 10
NUM_SENTENCES_IN_BATCH = 3

def sample_user_words_for_generation(conn: Connection, user_id: int, num_words_sampled: int) -> list[str]:
    # Words for LLM prompt - should only be a small sample, since excessive words wastes tokens without improving results
    # TODO: constrain the sample: docs/sentences.md#constraint-aware-eligibility-query
    result = conn.execute(text("""
        SELECT target
        FROM words
        JOIN user_words ON user_words.word_id = words.id
        WHERE user_id = :user_id
        ORDER BY RANDOM()
        LIMIT :num_words
    """), {"user_id": user_id, "num_words": num_words_sampled})

    rows = result.fetchall()

    user_words = [row.target for row in rows]

    return user_words


def get_eligible_sentences(conn: Connection, user_id: int, known_words_proportion: float = 0.7) -> list[SentencePair]:
    """Fetch existing sentences from the cache that the user has not already done, which have the desired proportion of known words from their vocab vault.

    Args:
        known_words_proportion: The desired proportion of the sentence's lemmas that matches the user's known words. ie 0.8 means 20% of the sentence would be new words

    Returns:
        A list of eligible sentence pairs from the cache with the desired proportion of known words : unknown words

    """

    print(f"KNOWN WORDS PROPORTION: {known_words_proportion}")
    lower_bound = known_words_proportion - 0.1
    upper_bound = known_words_proportion + 0.1

    eligible_sentences = conn.execute(text("""
        WITH users_words AS (
            SELECT * FROM user_words WHERE user_id = :user_id
            )
        SELECT s.id, s.target, s.source
        FROM sentences s
        JOIN sentence_words sw ON s.id = sw.sentence_id
        JOIN users_words uw ON sw.word_id = uw.word_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM sentence_results sr
            WHERE sr.user_id = :user_id
                AND sr.sentence_id = s.id
            )
        GROUP BY s.id, s.target, s.source, s.lemma_count
        HAVING COUNT(s.id) >= :lower_bound * s.lemma_count 
            AND COUNT(s.id) <= :upper_bound * s.lemma_count
        LIMIT 50
        """), {"user_id": user_id, "lower_bound": lower_bound, "upper_bound": upper_bound})

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
    read_conn: Annotated[Connection, Depends(get_read_connection)],     # Two connections so that a single conn isn't kept open over slow LLM call
    write_conn: Annotated[Connection, Depends(get_write_connection)],
    user_id: Annotated[int, Depends(decode_access_token)],
    payload: SentenceRequest
):
    """Returns a batch of sentences for the user.

    First serves any applicable sentences that already exist in the cached sentences. If none applicable exist, it generates new sentences via LLM API,
    lemmatises them, and inserts the sentences and associated data into the sentences cache.
    """
    known_words_proportion = payload.known_proportion / 100   # The frontend slider is 0 - 100, but this must be converted to decimal
    eligible_sentences_in_cache = get_eligible_sentences(read_conn, user_id, known_words_proportion)

    if len(eligible_sentences_in_cache) >= NUM_SENTENCES_IN_BATCH:    # Sufficient sentences already fetched, can return them rather than generate any
        eligible_sentences = {"sentences": [{"id": sentence.id, "target": sentence.target, "source": sentence.source} for sentence in eligible_sentences_in_cache]}    # Early return since no need to lemmatise etc - sentences from db are already lemmatised
        return eligible_sentences
    
    user_words = sample_user_words_for_generation(read_conn, user_id, NUM_WORDS_SAMPLED)   # User words needed to get sentences bespoke for the user

    sentences = generate_sentences(user_words, NUM_SENTENCES_IN_BATCH)  # If no eligible sentences already exist in the sentences cache

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
def create_sentence_result(conn: Annotated[Connection, Depends(get_write_connection)], user_id: Annotated[int, Depends(decode_access_token)], payload: SentenceResult):      # TODO: batch these and send via beacon on page close
    """Records the user's result for a single reviewed sentence."""
    insert_sentence_result(conn, user_id, payload.sentence_id, payload.status)

    return {"saved_sentence_id": payload.sentence_id}
