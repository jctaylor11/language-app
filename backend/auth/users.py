from sqlalchemy import text, Connection


def authenticate_or_waitlist(conn: Connection, user_infos) -> int | None:
    user_email = user_infos["email"]

    result = conn.execute(text("""
        INSERT INTO waitlist (email)
        VALUES (:email)
        ON CONFLICT (email) DO UPDATE   -- Just so we can get the satus back
            SET email = EXCLUDED.email
        RETURNING approved
    """), {"email": user_email})

    row = result.fetchone()

    if row.approved is False:
        return None

    user_id = get_or_create_user_id(conn, user_infos)

    return user_id


def get_or_create_user_id(conn: Connection, user_infos) -> int:
    google_sub = user_infos["google_sub"]
    user_email = user_infos["email"]

    result = conn.execute(text("""
        INSERT INTO users (google_sub, email)
        VALUES (:google_sub, :email)
        ON CONFLICT (google_sub) DO UPDATE
            SET email = EXCLUDED.email
        RETURNING id
    """), {"google_sub": google_sub, "email": user_email})

    row = result.fetchone()

    user_id = row.id

    return user_id
