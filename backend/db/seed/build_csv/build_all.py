from backend.db.seed.build_csv.ingest_nikl_entries import ingest_nikl_entries
from backend.db.seed.build_csv.build_words import build_words
from backend.db.seed.build_csv.validate_words import validate_words

if __name__ == "__main__":
    ingest_nikl_entries()   # Converts the NIKL raw list into csv with custom columns
    build_words()       # Builds the csv to load into words table, from the NIKL entries
    validate_words()    # Only reports any failures
