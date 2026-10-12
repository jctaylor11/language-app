import csv

NIKL_LIST_PATH = "resources/nikl_list.txt"
NIKL_WORDS_CSV_PATH = "backend/db/seed/nikl_words.csv"
WORD_LIMIT = 100


def ingest_nikl_words() -> None:
    with open(NIKL_LIST_PATH, newline="", encoding="cp949") as nikl_file:      # NIKL publishes the list in the legacy Korean encoding, not UTF-8
        nikl_rows = list(csv.DictReader(nikl_file, delimiter="\t"))

    ranked_nikl_list = []
    for nikl_row in nikl_rows:
        # Some entries have no rank, and therefore excluded 
        if nikl_row["순위"] == "":   
            continue

        ranked_nikl_list.append(nikl_row)

    ranked_nikl_list.sort(key=lambda ranked_row: int(ranked_row["순위"]))     # Published in alphabetical order, so sorted to take the most frequent words first
    selected_nikl_rows = ranked_nikl_list[:WORD_LIMIT]

    nikl_words = []
    for nikl_row in selected_nikl_rows:
        nikl_words.append({
            "freq_rank": nikl_row["순위"],
            "word": nikl_row["단어"],
            "pos": nikl_row["품사"],
            "explanation": nikl_row["풀이"],
            "level": nikl_row["등급"],
        })

    with open(NIKL_WORDS_CSV_PATH, "w", newline="", encoding="utf-8") as nikl_words_file:
        writer = csv.DictWriter(nikl_words_file, fieldnames=["freq_rank", "word", "pos", "explanation", "level"])
        writer.writeheader()
        writer.writerows(nikl_words)

    print(f"Wrote {len(nikl_words)} words to {NIKL_WORDS_CSV_PATH}")


if __name__ == "__main__":
    ingest_nikl_words()
