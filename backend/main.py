from sqlalchemy import text, insert
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from backend.db.connection import get_engine
from backend.db.models import Sentence
from backend.llm import generate_sentences
from backend.enums import ResultStatus
from backend.lemmatiser import extract_lemmas

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
    response_time_ms: int | None = None
    answered_at: datetime | None = None
    raw_keystrokes: str | None = None
    status: ResultStatus
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

    params = [{"user_id": user_id, "session_id": session_results.session_id, **word_result.model_dump(mode="json")} for word_result in session_results.word_results]

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


@app.get("/sentences")
def generate_sentences_endpoint(num_words: int):
    # Hardcoded for now
    user_id = 1

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT target
            FROM words
            JOIN user_words ON user_words.word_id = words.id
            WHERE user_id = :user_id
            ORDER BY RANDOM()
            LIMIT :num_words
        """), {"user_id": user_id, "num_words": num_words})
    
        rows = result.fetchall()

    sentence_words = [row.target for row in rows]

    # API request
    sentences = generate_sentences(sentence_words)

    # Lemmas are needed as a standard form to reference vocab table (citation form)
    for sentence in sentences:
        sentence.lemmas = extract_lemmas(sentence.target)

    with engine.begin() as conn:
        result = conn.execute(insert(Sentence).returning(Sentence.id, Sentence.target, Sentence.source),    # Core with expression language used to handle multi-rows
            [{"target": s.target, "source": s.source} for s in sentences])

        rows = result.fetchall()

        # Query database for set of lemmas that exist in vocab database (citation form) - get their IDs
        # Map the setnence words to the valid word IDs (ignoring lemma words which do not have an ID - they are not in vocab vault)
        # As a batch - insert the word IDs in setnence_words: all word_ids for each sentence_id

    return {"sentences": [{"id": row.id, "target": row.target, "source": row.source} for row in rows]}
