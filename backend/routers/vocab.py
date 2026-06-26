from fastapi import APIRouter, Depends
from sqlalchemy import text, Connection
from typing import Annotated

from backend.db.connection import get_read_connection, get_write_connection
from backend.schemas import VocabResults

router = APIRouter()


def sample_word_batch(conn: Connection, user_id: int) -> list[dict]:
    result = conn.execute(text("""
        SELECT id, target, source
        FROM words
        JOIN user_words ON user_words.word_id = words.id
        WHERE user_id = :user_id
        ORDER BY RANDOM()
        LIMIT 5
    """), {"user_id": user_id})

    rows = result.fetchall()

    return [row._asdict() for row in rows]


def insert_vocab_results(conn: Connection, user_id: int, vocab_results: VocabResults) -> int:
    params = [{"user_id": user_id, "session_id": vocab_results.session_id, **word_result.model_dump(mode="json")} for word_result in vocab_results.word_results]

    # All response data for each word in the session batch saved
    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, raw_keystrokes, status, session_position)
        VALUES (:user_id, :session_id, :word_id, :response_time_ms, :answered_at, :raw_keystrokes, :status, :session_position)
    """), params)

    # Session's completed_at value is updated each flush - final update accurate logs completion
    conn.execute(text("""
        UPDATE sessions
        SET completed_at = NOW()
        WHERE id = :session_id
    """), {"session_id": vocab_results.session_id})

    return len(vocab_results.word_results)


@router.get("/words")
def get_word_batch(user_id: int, conn: Annotated[Connection, Depends(get_read_connection)]) -> dict:
    """Fetch batch of words to show to user"""
    word_batch = sample_word_batch(conn, user_id)

    return {"word_batch": word_batch}


@router.post("/vocab-results")
def create_vocab_results(user_id: int, vocab_results: VocabResults, conn: Annotated[Connection, Depends(get_write_connection)]) -> dict:
    """Save user's response data for each word in the session batch"""
    results_saved = insert_vocab_results(conn, user_id, vocab_results)

    return {"results_saved": results_saved}
