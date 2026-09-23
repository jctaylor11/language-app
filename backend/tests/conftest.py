import pytest 
import subprocess
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.main import app
from backend.db.connection import get_write_connection, get_read_connection
from backend.config import TEST_DATABASE_URL
from backend.auth.refresh_token import create_refresh_token
from backend.auth.access_token import create_access_token

test_engine = create_engine(TEST_DATABASE_URL)

TEST_USER_WORD_COUNT = 6
TEST_INTRODUCED_WORDS_COUNT = 6


@pytest.fixture(scope="session", autouse=True)
def apply_migration():      # So it's auomatically kept in sync with migrations
    subprocess.run(
        ["alembic", "-c", "backend/alembic.ini", "-x", "db=test", "upgrade", "head"],
        check=True,
    )


@pytest.fixture
def conn():     # Handles connection manually for single connection with rollback
    conn = test_engine.connect()
    conn.begin()
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def client(conn):
    def get_test_write_connection(): 
        yield conn

    def get_test_read_connection():
        yield conn

    app.dependency_overrides[get_write_connection] = get_test_write_connection
    app.dependency_overrides[get_read_connection] = get_test_read_connection
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seed_user(conn) -> int:
    # Id comes from the sequence rather than being hardcoded, since an explicit id doesn't advance it and collides on a fresh database
    result = conn.execute(text("INSERT INTO users (google_sub, email) VALUES (:test_sub, :test_email) RETURNING id"), {"test_sub": "123", "test_email": "test@email.com"})
    return result.scalar()


@pytest.fixture
def access_token(seed_user) -> str:
    access_token = create_access_token(seed_user)
    return access_token


@pytest.fixture
def seed_session(conn, seed_user):
    result = conn.execute(text("INSERT INTO sessions (user_id, bound_type, bound_value, session_type) VALUES (:user_id, :bound_type, :bound_value, :session_type) RETURNING id"), {"user_id": seed_user, "bound_type": "time", "bound_value": 120, "session_type": "vocab"})
    return result.scalar()


@pytest.fixture
def refresh_token(conn, seed_user) -> str:
    return create_refresh_token(conn, seed_user)


@pytest.fixture
def concurrent_clients():
    # Concurrent transactions rather than one shared conn. Two separate TestClient instances each thread has its own client's cookies. 
    def get_test_write_connection():
        with test_engine.begin() as conn:   # Independently manages its own  connection lifestyle, unlike the shared and manual connection with client
            yield conn

    def get_test_read_connection():
        with test_engine.connect() as conn:
            yield conn

    app.dependency_overrides[get_write_connection] = get_test_write_connection
    app.dependency_overrides[get_read_connection] = get_test_read_connection
    yield TestClient(app), TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def concurrent_refresh_token():
    # Committed for real (not rolled back) so both concurrent connections can see it
    with test_engine.begin() as conn:
        user_id = conn.execute(text("INSERT INTO users (google_sub, email) VALUES (:sub, :email) RETURNING id"), {"sub": "concurrent-test-sub", "email": "concurrent-test@email.com"}).scalar()
        token = create_refresh_token(conn, user_id)

    yield token

    with test_engine.begin() as conn:   # Manually delete for teardown since it's committed, not rolled back
        conn.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})


@pytest.fixture
def seed_words(conn):
    result = conn.execute(text("""
        INSERT INTO words (target, source, part_of_speech) VALUES
            ('물', 'water', 'noun'),
            ('사람', 'person', 'noun'),
            ('집', 'house', 'noun'),
            ('먹다', 'to eat', 'verb'),
            ('가다', 'to go', 'verb'),
            ('좋다', 'good', 'adjective'),
            ('오늘', 'today', 'noun')
        RETURNING id
    """))

    word_ids = [row.id for row in result.fetchall()]

    return word_ids


@pytest.fixture
def seed_user_words(conn, seed_user, seed_words):
    word_ids = seed_words[:TEST_USER_WORD_COUNT] # user_words < words to differentiate between returning words vs user_words

    conn.execute(text("""
        INSERT INTO user_words (user_id, word_id)
        VALUES (:user_id, :word_id)
        """), [{"user_id": seed_user, "word_id": word_id} for word_id in word_ids])

    return word_ids


@pytest.fixture
def seed_introduced_words(conn, seed_user, seed_session, seed_words):
    word_ids = seed_words[:TEST_INTRODUCED_WORDS_COUNT]    # A subset of seeded words to differentiate between returning words vs introduced_words

    conn.execute(text("""
        INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, status, session_position)
        VALUES (:user_id, :session_id, :word_id, 1000, NOW(), 'correct_first_try', :session_position)
    """), [{"user_id": seed_user, "session_id": seed_session, "word_id": word_id, "session_position": position} for position, word_id in enumerate(word_ids, start=1)])

    return word_ids


# Not a fixture since each seeded sentence takes different arguments
def seed_sentence(conn, target: str, lemma_count: int, known_word_ids: list[int]) -> int:
    # Caller picks the values to suit their assertion - only requirement is that the word IDs exist actually exist
    # The word IDs don't need to match the actual words, nor the actual number of words in the sentence (can be less due to what's actually in database). What's important is shape/quantity for assertions
    result = conn.execute(text("""
        INSERT INTO sentences (target, source, lemma_count)
        VALUES (:target, 'test sentence', :lemma_count)
        RETURNING id
    """), {"target": target, "lemma_count": lemma_count})   # sentences.target is unique, so each seeded sentence needs its own
    sentence_id = result.scalar()

    if known_word_ids:
        conn.execute(text("""
            INSERT INTO sentence_words (sentence_id, word_id)
            VALUES (:sentence_id, :word_id)
        """), [{"sentence_id": sentence_id, "word_id": word_id} for word_id in known_word_ids])

    return sentence_id

