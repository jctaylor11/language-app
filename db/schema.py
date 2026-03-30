from sqlalchemy import text


def create_tables(engine):
    with engine.begin() as conn: 
        # Check if result_status type already exists
        result_status_exists = conn.execute(text("SELECT 1 FROM pg_type WHERE typname = 'result_status'"))
        if not result_status_exists.fetchone():
            # Defines result_status type for the session_results table, where the can only be one of three outcomes
            conn.execute(text("CREATE TYPE result_status AS ENUM ('correct_first_try', 'corrected', 'skipped');"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS words (
                id SERIAL PRIMARY KEY,
                target_word text NOT NULL,
                native_word text NOT NULL,
                part_of_speech text NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username text NOT NULL UNIQUE,
                created_at timestamptz NOT NULL DEFAULT NOW()
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id integer NOT NULL REFERENCES users(id),
                started_at timestamptz NOT NULL,
                completed_at timestamptz
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS session_results (
                id SERIAL PRIMARY KEY,
                user_id integer NOT NULL REFERENCES users(id),
                session_id integer NOT NULL REFERENCES sessions(id),
                word_id integer NOT NULL REFERENCES words(id),
                response_time_ms int,
                answered_at timestamptz,
                pre_correction_input text,
                status result_status NOT NULL,
                session_position int NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_words (
                user_id int NOT NULL REFERENCES users(id),
                word_id int NOT NULL REFERENCES words(id),
                added_at timestamptz NOT NULL DEFAULT NOW(),
                PRIMARY KEY (user_id, word_id)
            );
        """))
