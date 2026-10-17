import csv

NIKL_LIST_PATH = "resources/nikl_list.txt"
NIKL_ENTRIES_CSV_PATH = "backend/db/seed/nikl_entries.csv"


def ingest_nikl_entries() -> None:
    with open(NIKL_LIST_PATH, newline="", encoding="cp949") as nikl_file:      # NIKL publishes list in the legacy Korean encoding, not UTF-8
        nikl_rows = list(csv.DictReader(nikl_file, delimiter="\t"))

    nikl_entries = []
    for nikl_row in nikl_rows:      # Keeps every entry so scope can be filtered when building the actual words csv
        nikl_entries.append({
            "freq_rank": nikl_row["순위"],
            "word": nikl_row["단어"],
            "pos": nikl_row["품사"],
            "explanation": nikl_row["풀이"],
            "level": nikl_row["등급"],
        })

    with open(NIKL_ENTRIES_CSV_PATH, "w", newline="", encoding="utf-8") as nikl_entries_file:
        writer = csv.DictWriter(nikl_entries_file, fieldnames=["freq_rank", "word", "pos", "explanation", "level"])
        writer.writeheader()
        writer.writerows(nikl_entries)

    print(f"Wrote {len(nikl_entries)} entries to {NIKL_ENTRIES_CSV_PATH}")


if __name__ == "__main__":
    ingest_nikl_entries()
