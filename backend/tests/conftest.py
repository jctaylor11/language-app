import pytest 
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.main import app
from backend.db.connection import get_write_connection, get_read_connection
from backend.config import TEST_DATABASE_URL
from backend.auth.refresh_token import create_refresh_token
from backend.auth.access_token import create_access_token

test_engine = create_engine(TEST_DATABASE_URL)

TEST_USER_ID = 1
TEST_SESSION_ID = 1
TEST_USER_WORD_COUNT = 6


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
    # Single-user test setup with rollback isolation, so user_id always 1
    result = conn.execute(text("INSERT INTO users (id, google_sub, email) VALUES (:test_user_id, :test_sub, :test_email) RETURNING id"), {"test_user_id": TEST_USER_ID, "test_sub": "123", "test_email": "test@email.com"})
    return result.scalar()


@pytest.fixture
def access_token(seed_user) -> str:
    access_token = create_access_token(TEST_USER_ID)
    return access_token


@pytest.fixture
def seed_session(conn, seed_user):
    result = conn.execute(text("INSERT INTO sessions (id, user_id, bound_type, bound_value) VALUES (:session_id, :user_id, :bound_type, :bound_value) RETURNING id"), {"session_id": TEST_SESSION_ID, "user_id": TEST_USER_ID, "bound_type": "time", "bound_value": 120})
    return result.scalar()


@pytest.fixture
def refresh_token(conn, seed_user) -> str:
    return create_refresh_token(conn, TEST_USER_ID)


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
def seed_user_words(conn, seed_user):
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

    word_ids = [row.id for row in result.fetchall()][:TEST_USER_WORD_COUNT] # So that user_words < words, to differentiate between returning words vs user_words

    conn.execute(text("""
        INSERT INTO user_words (user_id, word_id) 
        VALUES (:user_id, :word_id)  
        """), [{"user_id": TEST_USER_ID, "word_id": word_id} for word_id in word_ids])
    
    return word_ids

