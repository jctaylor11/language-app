import csv
import re

NIKL_ENTRIES_PATH = "backend/db/seed/data/nikl_entries.csv"
WORDS_PATH = "backend/db/seed/data/words_new.csv"

REJECTED_WORD_POS = ['의', '보', '고', '불']

def build_words():
    with open(NIKL_ENTRIES_PATH, 'r', newline="", encoding="utf-8") as nikl_entries:
        nikl_rows = list(csv.DictReader(nikl_entries))

    entries_by_word = {}
    rejections = []

    for row in nikl_rows:
        if (row["pos"] in REJECTED_WORD_POS):
            rejections.append(row)
        else:
            word = re.sub(r"\d+$", "", row["word"])     # The NIKL list number homographs at the end of the word string. E.g this converts all homographs to the same spelling: 가구04 → 가구 for them to be grouped

            if word not in entries_by_word:
                entries_by_word[word] = [] 

            entries_by_word[word].append({              # Appending each row to a list keyed on the word groups the homographs, so they can be collapsed into one entry
                "nikl_freq_rank": row["freq_rank"],
                "nikl_difficulty": row["level"]
            })

    words = []
    for word, entries in entries_by_word.items():
        # Decision to condense ranks of homographs into the minimum value, as per 2026-10-16 log entry
        ranks = []
        for entry in entries: 
            if entry["nikl_freq_rank"] == "":
                continue
            
            ranks.append(int(entry["nikl_freq_rank"]))     

        if ranks: 
            nikl_freq_rank = min(ranks)
        else:
            nikl_freq_rank = ""

        # Decision to condense homographs difficulties into their minimum value
        difficulties = [entry["nikl_difficulty"] for entry in entries]
        nikl_difficulty = min(difficulties)    

        words.append({
            "word": word,
            "nikl_freq_rank": nikl_freq_rank,
            "nikl_difficulty": nikl_difficulty
        })

    with open(WORDS_PATH, 'w', newline="", encoding="utf-8") as words_csv:
        writer = csv.DictWriter(words_csv, fieldnames=['word', 'nikl_freq_rank', 'nikl_difficulty'])
        writer.writeheader()
        writer.writerows(words)

    print(f"Wrote {len(words)} words to {WORDS_PATH}\n")
    print(f"Rejected entries: {len(rejections)}")
    print(f"Kept entries: {len(nikl_rows) - len(rejections)} merged into {len(words)}")

if __name__ == "__main__":
    build_words()