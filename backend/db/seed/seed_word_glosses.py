import csv
from sqlalchemy import text

from backend.db.connection import get_engine

CSV_PATH = "backend/db/seed/data/word_glosses.csv"

def seed_word_glosses(engine):
    with open(CSV_PATH, newline="", encoding="utf-8") as csv_file:
        gloss_rows = list(csv.DictReader(csv_file))

    with engine.begin() as conn:
        result = conn.execute(text("SELECT id, target FROM words"))     # So we can match the words in glosses to the IDs in the database
        rows = result.fetchall()
        word_ids_by_target = {row.target: row.id for row in rows}

        insert_rows = []
        skipped_targets = set()
        for gloss_row in gloss_rows:
            word_id = word_ids_by_target.get(gloss_row["word"])
            if word_id is None:     # Words table can hold fewer words than the gloss CSV (e.g. placeholder words in prod)
                skipped_targets.add(gloss_row["word"])
                continue

            insert_row = {
                "word_id": word_id,
                "gloss": gloss_row["gloss"],
                "pos": gloss_row["pos"],
                "gloss_type": gloss_row["gloss_type"],
            }
            insert_rows.append(insert_row)

        conn.execute(text("""
            INSERT INTO word_glosses (word_id, gloss, pos, gloss_type)
            VALUES (:word_id, :gloss, :pos, :gloss_type)
            ON CONFLICT (word_id, gloss) DO NOTHING
        """), insert_rows)

    print(f"Sent {len(insert_rows)} gloss rows to insert, skipped {len(skipped_targets)} words not in the words table")

if __name__ == "__main__":
    engine = get_engine()
    seed_word_glosses(engine)
