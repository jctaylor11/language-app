import csv
from sqlalchemy import text

from backend.db.connection import get_engine

CSV_PATH = "backend/db/seed/words.csv"

def seed_words(engine):
    with open(CSV_PATH, newline="", encoding="utf-8") as csv_file:
        word_rows = list(csv.DictReader(csv_file))

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO words (target, source, part_of_speech) 
            VALUES (:target, :source, :part_of_speech)
            ON CONFLICT (target) DO NOTHING
        """), word_rows)

if __name__ == "__main__":
    engine = get_engine()
    seed_words(engine)