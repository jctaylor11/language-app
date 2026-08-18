from fastapi import APIRouter, Depends
from sqlalchemy import Connection, text
from typing import Annotated

from backend.auth.access_token import decode_access_token
from backend.db.connection import get_write_connection, get_read_connection
from backend.schemas import SessionRequest

router = APIRouter()


def insert_session(conn: Connection, user_id: int, session_request: SessionRequest) -> int:
    params = {"user_id": user_id, "bound_type": session_request.bound_type.value, "bound_value": session_request.bound_value, "session_type": session_request.session_type.value}
    result = conn.execute(text("""
        INSERT INTO sessions (user_id, bound_type, bound_value, session_type)
        VALUES (:user_id, :bound_type, :bound_value, :session_type)
        RETURNING id
    """), params)

    return result.scalar()

def get_session_log_data(conn: Connection, user_id: int) -> list[dict]:
    result = conn.execute(text("""
        SELECT sessions.id AS session_id, sessions.started_at AS started_at, sessions.session_type AS session_type, COUNT(*) AS total_reviewed
        FROM sessions
        JOIN vocab_results ON sessions.id = vocab_results.session_id
        WHERE sessions.user_id = :user_id
        AND vocab_results.status != 'skipped'
        GROUP BY sessions.id, sessions.session_type, sessions.started_at
        UNION ALL (
            SELECT sentence_results.session_id, sessions.started_at, sessions.session_type, COUNT(*)
            FROM sentence_results
            JOIN sentence_words ON sentence_words.sentence_id = sentence_results.sentence_id
            JOIN sessions ON sessions.id = sentence_results.session_id
            WHERE sessions.user_id = :user_id
            AND sentence_results.status != 'skipped'
            GROUP BY sentence_results.session_id, sessions.session_type, sessions.started_at
        ) 
        ORDER BY started_at DESC, session_id;
    """), {"user_id": user_id})

    rows = result.fetchall()

    return [row._asdict() for row in rows]

def get_session_overview_data(conn: Connection, user_id: int, session_id: int) -> list[str]:
    params = {"user_id": user_id, "session_id": session_id}
    result = conn.execute(text("""
        SELECT target
        FROM vocab_results vr
        JOIN words w ON vr.word_id = w.id
        WHERE user_id = :user_id
            AND session_id = :session_id
            AND status != 'skipped'
        UNION ALL (
            SELECT target
            FROM sentence_results sr
            JOIN sentences s ON sr.sentence_id = s.id
            WHERE user_id = :user_id
                AND session_id = :session_id
                AND status != 'skipped'
            );
    """), params)

    rows = result.fetchall()

    return [row.target for row in rows]

@router.post("/sessions")
def create_session(conn: Annotated[Connection, Depends(get_write_connection)], user_id: Annotated[int, Depends(decode_access_token)], session_request: SessionRequest) -> dict:
    session_id = insert_session(conn, user_id, session_request)

    return {"session_id": session_id}

@router.get("/sessions/log")
def get_session_log(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)]) -> dict:
    session_log = get_session_log_data(conn, user_id)

    return {"session_log": session_log}

@router.get("/sessions/overview/{session_id}")
def get_session_overview(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)], session_id: int) -> dict:
    session_overview = get_session_overview_data(conn, user_id, session_id)

    return {"session_overview": session_overview}
