from fastapi import APIRouter, Depends
from sqlalchemy import Connection, text
from typing import Annotated

from backend.auth.access_token import decode_access_token
from backend.db.connection import get_write_connection
from backend.schemas import SessionBounds

router = APIRouter()


def insert_session(conn: Connection, user_id: int, session_bounds: SessionBounds) -> int:
    params = {"user_id": user_id, "bound_type": session_bounds.bound_type.value, "bound_value": session_bounds.bound_value}
    result = conn.execute(text("""
        INSERT INTO sessions (user_id, bound_type, bound_value)
        VALUES (:user_id, :bound_type, :bound_value)
        RETURNING id
    """), params)

    return result.scalar()


@router.post("/sessions")
def create_session(conn: Annotated[Connection, Depends(get_write_connection)], user_id: Annotated[int, Depends(decode_access_token)], session_bounds: SessionBounds) -> dict:
    session_id = insert_session(conn, user_id, session_bounds)

    return {"session_id": session_id}
