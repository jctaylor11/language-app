import pytest 
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.main import app
from backend.db.connection import get_write_connection
from backend.config import TEST_DATABASE_URL

test_engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture
def conn():     # Handles connection manually - anything that needs conn will have it passed from this manager
    conn = test_engine.connect()
    conn.begin()
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def client(conn):
    conn.execute(text("INSERT INTO users (id, username) VALUES (1, 'test') ON CONFLICT DO NOTHING"))

    def get_test_write_connection(): 
        yield conn      # Uses same connection so we can rollback

    app.dependency_overrides[get_write_connection] = get_test_write_connection
    yield TestClient(app)
    app.dependency_overrides.clear()
