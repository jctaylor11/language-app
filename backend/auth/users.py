from sqlalchemy import text, Connection


def get_or_create_user_id(conn: Connection, user_infos) -> int:
    google_sub = user_infos["google_sub"]
    email = user_infos["email"]

    result = conn.execute(text("""
        INSERT INTO users (google_sub, email)
        VALUES (:google_sub, :email)
        ON CONFLICT (google_sub) DO UPDATE
            SET email = EXCLUDED.email
        RETURNING id
    """), {"google_sub": google_sub, "email": email})

    row = result.fetchone()

    user_id = row.id

    return user_id
