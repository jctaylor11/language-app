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
