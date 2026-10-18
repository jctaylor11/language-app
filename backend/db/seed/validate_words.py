import csv

from backend.lemmatiser import extract_lemmas

WORDS_PATH = "backend/db/seed/data/words_new.csv"
LEMMA_FAILURES_PATH = "backend/db/seed/data/lemma_failures.csv"


def validate_words():
    """It's important that every word in the words database is an output of the lemmatiser function, otherwise when the word appears in-sentence it will not have an ID.
    This is particularly relevant when seeing which words have been reviewed in the sentence, e.g via 'sentence_words'.
    As per 2026-06-02 and 2026-10-17 log entries, around lemma form for words, and the scope of the lemmas included"""
    with open(WORDS_PATH, 'r', newline="", encoding="utf-8") as words_csv:
        word_rows = list(csv.DictReader(words_csv))

    failures = []
    for row in word_rows:
        word = row["word"]
        lemmas = extract_lemmas(word)

        # A word is valid if the lemmatiser returns it unchanged, so sentence lemmas can match it, as per 2026-10-17 log entry
        if lemmas == [word]:
            continue

        failures.append({
            "word": word,
            "lemmatiser_output": " ".join(lemmas)     # Joined since a csv cell can't hold a list
        })

    with open(LEMMA_FAILURES_PATH, 'w', newline="", encoding="utf-8") as lemma_failures_csv:
        writer = csv.DictWriter(lemma_failures_csv, fieldnames=['word', 'lemmatiser_output'])
        writer.writeheader()
        writer.writerows(failures)

    total = len(word_rows)
    passed = total - len(failures)
    print(f"{passed}/{total} words passed ({passed / total:.1%})")
    print(f"Wrote {len(failures)} failures to {LEMMA_FAILURES_PATH}")


if __name__ == "__main__":
    validate_words()
