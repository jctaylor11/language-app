from fastapi import APIRouter
from sqlalchemy import Connection, text

from backend.db.connection import engine

router = APIRouter()


def insert_session(conn: Connection, user_id: int) -> int:
    result = conn.execute(text("""
        INSERT INTO sessions (user_id, started_at)
        VALUES (:user_id, CURRENT_TIMESTAMP)
        RETURNING id
    """), {"user_id": user_id})

    return result.scalar()


@router.post("/sessions")
def create_session(user_id: int):
    """Create new session and return session ID to client"""
    with engine.begin() as conn:
        session_id = insert_session(conn, user_id)

    return {"session_id": session_id}
