import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import text, Connection

from backend.config import REFRESH_TOKEN_EXPIRES_DAYS


def get_user_id_from_valid_refresh_token(conn: Connection, refresh_token: str) -> int | None:
    hashed_refresh_token = hash_token(refresh_token)

    result = conn.execute(text("""
        SELECT user_id FROM refresh_tokens
        WHERE refresh_token_hash = :refresh_token_hash
            AND refresh_token_expires_at > now()
    """), {"refresh_token_hash": hashed_refresh_token})

    row = result.fetchone()

    if row is None:
        return None

    return row.user_id


def delete_refresh_token(conn: Connection, refresh_token: str) -> None:
    hashed_refresh_token = hash_token(refresh_token)

    conn.execute(text("""
        DELETE FROM refresh_tokens WHERE refresh_token_hash = :refresh_token_hash
    """), {"refresh_token_hash": hashed_refresh_token})


def hash_token(token: str) -> str:
    hash_object = hashlib.sha256(token.encode())    # Unsalted, not needed since token is 256 random bits anyway
    hashed_token = hash_object.hexdigest()

    return hashed_token

def create_refresh_token(conn: Connection, user_id: int, refresh_token_expiry_days = REFRESH_TOKEN_EXPIRES_DAYS) -> str:
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=int(refresh_token_expiry_days))

    hashed_refresh_token = hash_token(refresh_token)

    conn.execute(text("""
        INSERT INTO refresh_tokens (user_id, refresh_token_hash, refresh_token_expires_at)
        VALUES (:user_id, :refresh_token_hash, :refresh_token_expires_at)
    """), {
        "user_id": user_id,
        "refresh_token_hash": hashed_refresh_token,
        "refresh_token_expires_at": expires_at,
    })

    return refresh_token
