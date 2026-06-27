from fastapi import APIRouter, Depends
from sqlalchemy import Connection, text
from typing import Annotated

from backend.db.connection import get_write_connection

router = APIRouter()


def insert_session(conn: Connection, user_id: int) -> int:
    result = conn.execute(text("""
        INSERT INTO sessions (user_id)
        VALUES (:user_id)
        RETURNING id
    """), {"user_id": user_id})

    return result.scalar()


@router.post("/sessions")
def create_session(user_id: int, conn: Annotated[Connection, Depends(get_write_connection)]) -> dict:
    session_id = insert_session(conn, user_id)

    return {"session_id": session_id}
