from backend.db.connection import get_engine
from backend.db.schema import create_tables
from backend.db.seed_words import seed_words


if __name__ == "__main__":
    engine = get_engine()
    create_tables(engine)
    seed_words(engine)