from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.engine import Connection

from backend.db.connection import engine
from backend.schemas import VocabResults


router = APIRouter()


def insert_session(conn: Connection, user_id: int) -> int:
    result = conn.execute(text("""
        INSERT INTO sessions (user_id, started_at)
        VALUES (:user_id, CURRENT_TIMESTAMP)
        RETURNING id
    """), {"user_id": user_id})

    return result.scalar()


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


@router.post("/sessions")
def create_session(user_id: int):
    """Create new session and return session ID to client"""
    with engine.begin() as conn:
        session_id = insert_session(conn, user_id)

    return {"session_id": session_id}


@router.get("/words")
def get_word_batch(user_id: int):
    """Fetch batch of words to show to user"""
    with engine.connect() as conn:
        word_batch = sample_word_batch(conn, user_id)

    return {"word_batch": word_batch}


@router.post("/vocab-results")
def create_vocab_results(user_id: int, vocab_results: VocabResults):
    """Save user's response data for each word in the session batch"""
    with engine.begin() as conn:
        results_saved = insert_vocab_results(conn, user_id, vocab_results)

    return {"results_saved": results_saved}
