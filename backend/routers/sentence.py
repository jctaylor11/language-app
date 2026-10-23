from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text, insert, Connection
from typing import Annotated

from backend.auth.access_token import decode_access_token
from backend.db.connection import get_read_connection, get_write_connection
from backend.llm import generate_sentences
from backend.lemmatiser import extract_lemmas
from backend.db.models import Sentence
from backend.enums import SentenceResultStatus
from backend.routers.session import session_belongs_to_user
from backend.schemas import SentenceResult, SentencePair, SentenceRequest

router = APIRouter()

NUM_WORDS_SAMPLED = 10
NUM_SENTENCES_IN_BATCH = 3
MIN_KNOWN_PERCENT = 60    # Should be 80, however temporarily lowered to 60 for development while logic is tightened
GENERATION_KNOWN_PERCENT = 80    # Comprehensible input research puts the optimal known proportion at 80%, the remaining 20% inferred from context
MIN_INTRODUCED_WORDS = NUM_WORDS_SAMPLED    # Fewer and the generation sample is short of what the prompt is built around


def count_introduced_words(conn: Connection, user_id: int) -> int:
    result = conn.execute(text("""
        SELECT COUNT(*) AS introduced_words_count
        FROM introduced_words       -- One row per word, and only counts words answered correctly, so peeked and skipped words don't unlock sentences
        WHERE user_id = :user_id
    """), {"user_id": user_id})

    row = result.fetchone()

    introduced_words_count = row.introduced_words_count

    return introduced_words_count


def sample_introduced_words_for_generation(conn: Connection, user_id: int, num_words_sampled: int) -> list[str]:
    # Words for LLM prompt - should only be a small sample, since excessive words wastes tokens without improving results
    # TODO: constrain the sample: docs/sentences.md#constraint-aware-eligibility-query
    result = conn.execute(text("""
        SELECT target
        FROM words
        JOIN introduced_words ON introduced_words.word_id = words.id
        WHERE introduced_words.user_id = :user_id
        ORDER BY RANDOM()
        LIMIT :num_words
    """), {"user_id": user_id, "num_words": num_words_sampled})

    rows = result.fetchall()

    sampled_words = [row.target for row in rows]

    return sampled_words


def get_eligible_sentences(conn: Connection, user_id: int, sentences_already_queued: list[int] = []) -> list[SentencePair]:
    """Fetch existing sentences from the cache that the user has not already done, whose proportion of known words from their vocab vault meets the minimum."""
    eligible_sentences = conn.execute(text("""
        WITH user_introduced_words AS (
            SELECT word_id FROM introduced_words WHERE user_id = :user_id
            )
        SELECT s.id, s.target, s.source
        FROM sentences s
        JOIN sentence_words sw ON s.id = sw.sentence_id
        JOIN user_introduced_words uiw ON sw.word_id = uiw.word_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM sentence_results sr
            WHERE sr.user_id = :user_id
                AND sr.sentence_id = s.id   -- Includes skipped sentences, they will not reappear after skipped
            )
        AND NOT (s.id = ANY(:sentences_already_queued))     -- Exclude sentences already queued from the last fetch, so that the user doesn't see duplicates
        GROUP BY s.id, s.target, s.source, s.lemma_count
        HAVING 100 * COUNT(s.id) >= :min_known_percent * s.lemma_count      -- Scaled by 100 rather than dividing, so the threshold compares as exact integers
        LIMIT 3
        """), {"user_id": user_id, "min_known_percent": MIN_KNOWN_PERCENT, "sentences_already_queued": sentences_already_queued})

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

    Rejects users with too few introduced words to build sentences from, before any LLM call. Otherwise first serves sentences already in the cache that meet the minimum known-word proportion. If the cache holds fewer than a full batch, new sentences
    are generated via LLM API, lemmatised, and inserted into the sentences cache.
    """
    introduced_words_count = count_introduced_words(read_conn, user_id)

    if introduced_words_count < MIN_INTRODUCED_WORDS:      # Checked first rather than only before generation, so the user isn't served cached sentences then locked out mid-session
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not enough introduced words to build sentences - do a vocab session first")

    eligible_sentences_in_cache = get_eligible_sentences(read_conn, user_id, payload.sentences_already_queued)  # Sentences already queued for the user are excluded from the eligible sentences returned, so that the user doesn't see duplicates in a single session

    if len(eligible_sentences_in_cache) >= NUM_SENTENCES_IN_BATCH:    # Sufficient sentences already fetched, can return them rather than generate any
        eligible_sentences = {"sentences": [{"id": sentence.id, "target": sentence.target, "source": sentence.source} for sentence in eligible_sentences_in_cache]}    # Early return since no need to lemmatise etc - sentences from db are already lemmatised
        return eligible_sentences
    
    introduced_words_sample = sample_introduced_words_for_generation(read_conn, user_id, NUM_WORDS_SAMPLED)   # Introduced words needed to get sentences bespoke for the user

    generated_sentences = generate_sentences(introduced_words_sample, NUM_SENTENCES_IN_BATCH, GENERATION_KNOWN_PERCENT)  # If no eligible sentences already exist in the sentences cache

    generated_sentences = lemmatise_sentences(generated_sentences)  # Lemmatisation allows sentence words to be matched against the words table by standardised citation form. Needed for sentence_words inserts and lemma_count

    generated_sentences = insert_sentences(write_conn, generated_sentences)  # Returns with IDs

    insert_sentences_words(write_conn, generated_sentences)

    eligible_sentences = get_eligible_sentences(write_conn, user_id, payload.sentences_already_queued)

    if len(eligible_sentences) < NUM_SENTENCES_IN_BATCH:  
        return {"sentences": [{"id": 0, "target": "Failed to get eligible sentences", "source": "Failed to get eligible sentences"}]}  

    return {"sentences": [{"id": row.id, "target": row.target, "source": row.source} for row in eligible_sentences]}


def insert_sentence_result(conn: Connection, user_id: int, sentence_result: SentenceResult) -> int:
    # Session ID is provided by client, therefore cannot be trusted
    if session_belongs_to_user(conn, user_id, sentence_result.session_id) is False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    conn.execute(text("""
        INSERT INTO sentence_results (user_id, session_id, sentence_id, status)
        VALUES (:user_id, :session_id, :sentence_id, :status)
    """), {"user_id": user_id, "session_id": sentence_result.session_id, "sentence_id": sentence_result.sentence_id, "status": sentence_result.status.value})

    # Session's last_result_at value is updated each flush - final update logs the last activity
    conn.execute(text("""
        UPDATE sessions
        SET last_result_at = NOW()
        WHERE id = :session_id
            AND user_id = :user_id      -- Session id comes from the client, so scoped to the requester
    """), {"user_id": user_id, "session_id": sentence_result.session_id})

    # Different return than the vocab equivalent since shape is different (vocab's payload is a list of results, sentences is just one)
    return sentence_result.sentence_id


def get_session_summary(conn: Connection, user_id: int, session_id: int):
    result = conn.execute(text("""
        SELECT COUNT(*) AS total_reviewed
        FROM sentence_results
        JOIN sentence_words
        ON sentence_results.sentence_id = sentence_words.sentence_id
        WHERE user_id = :user_id
        AND session_id = :session_id
        AND status NOT IN ('skipped', 'peeked')        -- Intentionally doesn't count as reviewed if skipped or peeked, mirroring the vocab summary
    """), {"user_id": user_id, "session_id": session_id})

    row = result.fetchone()

    return row._asdict()


@router.post("/sentence-results")
def create_sentence_result(conn: Annotated[Connection, Depends(get_write_connection)], user_id: Annotated[int, Depends(decode_access_token)], payload: SentenceResult) -> dict:      # TODO: Consider batching these and send via beacon on page close
    """Records the user's result for a single reviewed sentence."""
    saved_sentence_id = insert_sentence_result(conn, user_id, payload)

    return {"saved_sentence_id": saved_sentence_id}


@router.get("/sentence-sessions/{session_id}/summary")
def get_sentence_session_summary(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)], session_id: int) -> dict:
    """Fetch summary metrics for the given sentence session"""
    session_summary = get_session_summary(conn, user_id, session_id)

    return {"summary": session_summary}
