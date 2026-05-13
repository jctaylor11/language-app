from sqlalchemy import text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.db.connection import get_engine

app = FastAPI()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

engine = get_engine()


class WordResult(BaseModel):
    word_id: int
    response_time_ms: Optional[int] = None
    answered_at: Optional[datetime] = None
    raw_keystrokes: Optional[str] = None
    status: str  # TODO: Configure enum in enum file for single source of truth and replace with Enum
    session_position: int


# For insert_session_data input
class SessionResults(BaseModel):
    session_id: int
    word_results: list[WordResult]


@app.post("/sessions")
async def create_session():
    """Create new session and return session ID to client"""
    # Hardcode the user_id for now until auth added later
    user_id = 1

    # Create new entry in sessions
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO sessions (user_id, started_at)
            VALUES (:user_id, CURRENT_TIMESTAMP)
            RETURNING id             
        """), {"user_id": user_id})

        session_id = result.scalar()

    return {"session_id": session_id}


@app.get("/words")
async def get_word_batch():
    """Fetch batch of words to show to user"""
    # Hardcode for now, update after auth
    user_id = 1

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


@app.post("/session-results")
async def create_session_results(session_results: SessionResults):
    """Save user's response data for each word in the session batch"""
    # Hardcoded for now
    user_id = 1

    params = [{"user_id": user_id, "session_id": session_results.session_id, **word_result.model_dump()} for word_result in session_results.word_results]

    with engine.begin() as conn:
        # All response data for each word in the session batch saved
        conn.execute(text("""
            INSERT INTO session_results (user_id, session_id, word_id, response_time_ms, answered_at, raw_keystrokes, status, session_position)
            VALUES (:user_id, :session_id, :word_id, :response_time_ms, :answered_at, :raw_keystrokes, :status, :session_position)
        """), params)

        # Session's completed_at value is updated each flush - final update accurate logs completion
        conn.execute(text("""
            UPDATE sessions
            SET completed_at = NOW()
            WHERE id = :session_id
        """), {"session_id": session_results.session_id})
    
    return {"results_saved": len(session_results.word_results)} 


@app.get("/generate-sentences")
def get_sentences(num_words: int):

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT target
            FROM words
            JOIN user_words ON user_words.word_id = words.id
            WHERE user_id = 1
            ORDER BY RANDOM()
            LIMIT :num_words
        """), {"num_words": num_words})
    
    rows = result.fetchall()
    sentence_words = [row.target for row in rows]

    return {"sentence_words": sentence_words}
