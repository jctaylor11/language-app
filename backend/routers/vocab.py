from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text, Connection
from typing import Annotated

from backend.auth.access_token import decode_access_token
from backend.db.connection import get_read_connection, get_write_connection
from backend.routers.session import session_belongs_to_user
from backend.schemas import VocabResults

router = APIRouter()


def sample_word_batch(conn: Connection, user_id: int) -> list[dict]:
    # TODO: placeholder - replace with selection algorithm driven by the user's results
    result = conn.execute(text("""
        SELECT id, target, source
        FROM words
        ORDER BY RANDOM()
        LIMIT 5
    """))

    rows = result.fetchall()

    return [row._asdict() for row in rows]


def insert_vocab_results(conn: Connection, user_id: int, vocab_results: VocabResults) -> int:
    # Session is provided by the client, and therefore cannot be trusted
    if session_belongs_to_user(conn, user_id, vocab_results.session_id) is False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    params = [{"user_id": user_id, "session_id": vocab_results.session_id, **word_result.model_dump(mode="json")} for word_result in vocab_results.word_results]

    # All response data for each word in the session batch saved
    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, raw_keystrokes, status, session_position)
        VALUES (:user_id, :session_id, :word_id, :response_time_ms, :answered_at, :raw_keystrokes, :status, :session_position)
    """), params)

    # Session's last_result_at value is updated each flush - final update logs the last activity
    conn.execute(text("""
        UPDATE sessions
        SET last_result_at = NOW()
        WHERE id = :session_id
            AND user_id = :user_id      -- Session id comes from the client, so scoped to the requester
    """), {"user_id": user_id, "session_id": vocab_results.session_id})

    return len(vocab_results.word_results)


def get_session_summary(conn: Connection, user_id: int, session_id: int) -> dict:
    result = conn.execute(text("""
        WITH session_results AS (
            SELECT word_id, started_at 
            FROM vocab_results vr
            JOIN sessions s ON s.id = vr.session_id
            WHERE session_id = :session_id
            AND vr.user_id = :user_id       -- Isolates between users despite no checking that the session belongs to the requester - since it filters for that user
            AND status NOT IN ('skipped', 'cheated'))		-- Intentionally doesn't count as reviewed if skipped or cheated in the count
        SELECT 
            (SELECT COUNT(*) FROM session_results) AS total_reviewed,
            (SELECT COUNT(DISTINCT(word_id))
                FROM session_results sr
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM vocab_results vr2
                    WHERE vr2.user_id = :user_id
                    AND vr2.session_id != :session_id				-- Kept in addition to time filter to ensure integrity, in case of potential server/browser clock mismatch
                    AND sr.word_id = vr2.word_id
                    AND vr2.answered_at < sr.started_at  	-- Defensive, otherwise if called in future it won't be accurate if later session covered the word
                    AND vr2.status != 'skipped')			-- Otherwise words that have previously been skipped won't be considered new
            ) AS new_words;
    """), {"user_id": user_id, "session_id": session_id})

    row = result.fetchone()

    return row._asdict()


@router.get("/words")
def get_word_batch(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)]) -> dict:
    """Fetch batch of words to show to user"""
    word_batch = sample_word_batch(conn, user_id)

    return {"word_batch": word_batch}


@router.post("/vocab-results")
def create_vocab_results(conn: Annotated[Connection, Depends(get_write_connection)], user_id: Annotated[int, Depends(decode_access_token)], vocab_results: VocabResults) -> dict:
    """Save user's response data for each word in the session batch"""
    results_saved = insert_vocab_results(conn, user_id, vocab_results)

    return {"results_saved": results_saved}


@router.get("/vocab-sessions/{session_id}/summary")
def get_vocab_session_summary(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)], session_id: int) -> dict:
    """Fetch summary metrics for the given vocab session"""
    session_summary = get_session_summary(conn, user_id, session_id)

    return {"summary": session_summary}
