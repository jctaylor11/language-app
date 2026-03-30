from sqlalchemy import text
from fastapi import FastAPI

from db.connection import get_engine


app = FastAPI()

engine = get_engine()


@app.post("/session")
async def create_session():
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
    # Hardcode for now, update after auth
    user_id = 1

    # Fetch a batch of 5 words from database
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT id as word_id, target_word, native_word
            FROM words
            JOIN user_words ON user_words.word_id = words.id
            WHERE user_id = :user_id
            ORDER BY RANDOM()
            LIMIT 5
        """), {"user_id": user_id})

        rows = result.fetchall()    
        word_batch = [row._asdict() for row in rows]

    return {"word_batch": word_batch}