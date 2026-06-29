import pytest 
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.main import app
from backend.db.connection import get_write_connection, get_read_connection
from backend.config import TEST_DATABASE_URL

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
    result = conn.execute(text("INSERT INTO users (id, username) VALUES (:test_user_id, 'test') RETURNING id"), {"test_user_id": TEST_USER_ID})
    return result.scalar()


@pytest.fixture
def seed_session(conn, seed_user):
    result = conn.execute(text("INSERT INTO sessions (id, user_id) VALUES (:session_id, :user_id) RETURNING id"), {"session_id": TEST_SESSION_ID, "user_id": TEST_USER_ID})
    return result.scalar()


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

