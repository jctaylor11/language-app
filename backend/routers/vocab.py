from fastapi import APIRouter
from sqlalchemy import text

from backend.db.connection import engine
from backend.schemas import WordResult, VocabResults

router = APIRouter()


@router.post("/sessions")
async def create_session(user_id: int):
    """Create new session and return session ID to client"""
    # Create new entry in sessions
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO sessions (user_id, started_at)
            VALUES (:user_id, CURRENT_TIMESTAMP)
            RETURNING id             
        """), {"user_id": user_id})

        session_id = result.scalar()

    return {"session_id": session_id}

@router.get("/words")
async def get_word_batch(user_id: int):
    """Fetch batch of words to show to user"""
    # Fetch a batch of 5 words from database
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT id, target, source
            FROM words
            JOIN user_words ON user_words.word_id = words.id
            WHERE user_id = :user_id
            ORDER BY RANDOM()
            LIMIT 5
        """), {"user_id": user_id})

        rows = result.fetchall()    
        word_batch = [row._asdict() for row in rows]

    return {"word_batch": word_batch}


@router.post("/vocab-results")
async def create_vocab_results(user_id: int, vocab_results: VocabResults):
    """Save user's response data for each word in the session batch"""

    params = [{"user_id": user_id, "session_id": vocab_results.session_id, **word_result.model_dump(mode="json")} for word_result in vocab_results.word_results]

    with engine.begin() as conn:
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
    
    return {"results_saved": len(vocab_results.word_results)} 
