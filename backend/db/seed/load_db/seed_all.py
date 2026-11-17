from backend.db.connection import get_engine
from backend.db.seed.load_db.seed_words import seed_words
from backend.db.seed.load_db.seed_word_glosses import seed_word_glosses

if __name__ == "__main__":
    engine = get_engine()
    seed_words(engine)
    seed_word_glosses(engine)     # After seed_words, since it looks up each word's ID
