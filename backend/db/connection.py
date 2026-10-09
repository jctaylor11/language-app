from sqlalchemy import create_engine, Engine

from backend.config import DATABASE_URL, SQL_ECHO

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)


def get_read_connection():
    with engine.connect() as conn:
        yield conn


def get_write_connection():
    with engine.begin() as conn:
        yield conn


def get_engine() -> Engine:  # Wrapped so it can be used as a dependency. POST /sentences manages its own transaction boundaries to avoid an open connection over slow LLM API call
    return engine

