import pytest 
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.main import app
from backend.db.connection import get_write_connection
from backend.config import TEST_DATABASE_URL

test_engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture
def client(): 

    with test_engine.begin() as conn:
        conn.execute(text("INSERT INTO users (id, username) VALUES (1, 'test') ON CONFLICT DO NOTHING"))

    def get_test_write_connection(): 
        with test_engine.begin() as conn:
            yield conn

    app.dependency_overrides[get_write_connection] = get_test_write_connection
    yield TestClient(app)
    app.dependency_overrides.clear()