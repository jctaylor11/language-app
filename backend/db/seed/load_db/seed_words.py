import csv
from sqlalchemy import text

from backend.db.connection import get_engine

CSV_PATH = "backend/db/seed/data/words.csv"

def seed_words(engine):
    with open(CSV_PATH, newline="", encoding="utf-8") as csv_file:
        csv_rows = list(csv.DictReader(csv_file))

    word_rows = []
    for csv_row in csv_rows:
        word_row = dict(csv_row)
        if word_row["nikl_freq_rank"] == "":    # Some NIKL words have no frequency rank, and "" is not a valid integer
            word_row["nikl_freq_rank"] = None
        word_rows.append(word_row)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO words (target, nikl_freq_rank, nikl_difficulty)
            VALUES (:target, :nikl_freq_rank, :nikl_difficulty)
            ON CONFLICT (target) DO NOTHING
        """), word_rows)

if __name__ == "__main__":
    engine = get_engine()
    seed_words(engine)