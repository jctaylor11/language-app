import argparse
import csv
import itertools
import json
import os

from backend.db.seed.build_words import NIKL_ENTRIES_PATH, group_and_filter_words_list

EVAL_WORDS_PATH = "backend/evals/word_glosses/eval_words.txt"
ANSWER_KEY_PATH = "backend/evals/word_glosses/answer_key.csv"
ROUNDS_DIRECTORY = "backend/evals/word_glosses/rounds"

PRIMARY_WEIGHT = 0.6
TOLERATED_WEIGHT = 0.4
MUST_NOT_PENALTY = 0.5      # Per hit: a loose gloss lets a wrong answer pass for the whole word

NIKL_POS_LABELS = {     # Copied rather than imported, since importing build_word_glosses creates an Anthropic client
    "명": "noun", "동": "verb", "형": "adjective", "부": "adverb",
    "관": "determiner", "대": "pronoun", "수": "numeral", "감": "interjection",
}


def normalise_gloss(gloss: str) -> str:
    lowered = gloss.lower().replace("’", "'")
    normalised = " ".join(lowered.split())
    return normalised


def normalise_tolerant(gloss: str) -> str:
    """Also drops a leading "to ", which the app's own answer check will fold."""
    normalised = normalise_gloss(gloss)
    if normalised.startswith("to "):
        normalised = normalised[3:]
    return normalised


def split_key_cell(cell: str) -> list[str]:
    glosses = []
    for gloss in cell.split("|"):
        if gloss.strip() == "":
            continue
        glosses.append(gloss.strip())
    return glosses


def load_answer_key() -> dict[str, list[dict]]:
    key_entries_by_word = {}
    with open(ANSWER_KEY_PATH, "r", newline="", encoding="utf-8") as key_file:
        for row in csv.DictReader(key_file):
            key_entry = {
                "word": row["word"],
                "entry_number": int(row["entry_number"]),
                "pos": row["pos"],
                "explanation": row["explanation"],
                "acceptable_primaries": split_key_cell(row["acceptable_primaries"]),
                "must_tolerate": split_key_cell(row["must_tolerate"]),
                "must_not_include": split_key_cell(row["must_not_include"]),
            }

            if row["word"] not in key_entries_by_word:
                key_entries_by_word[row["word"]] = []
            key_entries_by_word[row["word"]].append(key_entry)

    return key_entries_by_word


def validate_answer_key(key_entries_by_word: dict[str, list[dict]]) -> None:
    """
    The key is matched to generated glosses by entry number, which is only a position in the NIKL entries.
    So the key must cover exactly the entries the generator sends, in the same order, or scores are meaningless.
    """
    with open(NIKL_ENTRIES_PATH, "r", newline="", encoding="utf-8") as nikl_file:
        nikl_rows = list(csv.DictReader(nikl_file))
    nikl_entries_by_word, rejections = group_and_filter_words_list(nikl_rows)

    with open(EVAL_WORDS_PATH, "r", encoding="utf-8") as words_file:
        eval_words = words_file.read().split()

    problems = []
    for word in eval_words:
        expected_entries = []
        for entry in nikl_entries_by_word.get(word, []):
            expected_entries.append((NIKL_POS_LABELS[entry["pos"]], entry["explanation"]))

        key_entries = sorted(key_entries_by_word.get(word, []), key=lambda key_entry: key_entry["entry_number"])
        actual_entries = [(key_entry["pos"], key_entry["explanation"]) for key_entry in key_entries]
        entry_numbers = [key_entry["entry_number"] for key_entry in key_entries]

        if actual_entries != expected_entries or entry_numbers != list(range(1, len(expected_entries) + 1)):
            problems.append(f"{word}: key entries do not match the NIKL entries")

    for word in key_entries_by_word:
        if word not in eval_words:
            problems.append(f"{word}: in the key but not in {EVAL_WORDS_PATH}")

    for key_entries in key_entries_by_word.values():
        for key_entry in key_entries:
            entry_label = f"{key_entry['word']}#{key_entry['entry_number']}"
            if key_entry["acceptable_primaries"] == []:
                problems.append(f"{entry_label}: no acceptable_primaries")

            accepted = set()
            for gloss in key_entry["acceptable_primaries"] + key_entry["must_tolerate"]:
                accepted.add(normalise_tolerant(gloss))

            for gloss in key_entry["must_not_include"]:
                if normalise_tolerant(gloss) in accepted:
                    problems.append(f"{entry_label}: '{gloss}' is both accepted and must_not_include")

    if problems:
        raise ValueError("Answer key is invalid:\n" + "\n".join(problems))


def load_generated_glosses(generated_csv_path: str) -> dict[tuple[str, int], dict]:
    generated_entries = {}
    with open(generated_csv_path, "r", newline="", encoding="utf-8") as generated_file:
        for row in csv.DictReader(generated_file):
            entry_id = (row["word"], int(row["entry_number"]))
            if entry_id not in generated_entries:
                generated_entries[entry_id] = {"entry_number": entry_id[1], "primary": None, "tolerated": []}

            if row["gloss_type"] == "primary":
                generated_entries[entry_id]["primary"] = row["gloss"]
            else:
                generated_entries[entry_id]["tolerated"].append(row["gloss"])

    return generated_entries


def score_entry(key_entry: dict, generated_entry: dict | None) -> dict:
    entry_result = {
        "word": key_entry["word"],
        "entry_number": key_entry["entry_number"],
        "pos": key_entry["pos"],
        "explanation": key_entry["explanation"],
        "matched_entry_number": None,
        "primary": None,
        "tolerated": [],
        "primary_correct": False,
        "missing_tolerated": key_entry["must_tolerate"],
        "must_not_hits": [],
        "unjudged": [],
        "score": 0.0,
    }

    if generated_entry is None or generated_entry["primary"] is None:      # Word failed, was invalid, or the model dropped the entry
        return entry_result

    primary = generated_entry["primary"]
    tolerated = generated_entry["tolerated"]

    acceptable_primaries = {normalise_gloss(gloss) for gloss in key_entry["acceptable_primaries"]}
    primary_correct = normalise_gloss(primary) in acceptable_primaries      # Exact, so "eat" fails for "to eat": the form is part of the prompt's spec

    generated_glosses = {normalise_tolerant(gloss) for gloss in [primary] + tolerated}

    missing_tolerated = []
    for gloss in key_entry["must_tolerate"]:
        if normalise_tolerant(gloss) not in generated_glosses:
            missing_tolerated.append(gloss)

    must_not_hits = []
    for gloss in key_entry["must_not_include"]:
        if normalise_tolerant(gloss) in generated_glosses:
            must_not_hits.append(gloss)

    judged_glosses = set()
    for gloss in key_entry["acceptable_primaries"] + key_entry["must_tolerate"] + key_entry["must_not_include"]:
        judged_glosses.add(normalise_tolerant(gloss))

    unjudged = []
    for gloss in tolerated:
        if normalise_tolerant(gloss) not in judged_glosses:
            unjudged.append(gloss)

    primary_score = 1.0 if primary_correct else 0.0
    if key_entry["must_tolerate"] == []:
        base_score = primary_score      # Nothing to recall, so the primary carries the whole entry
    else:
        tolerated_recall = 1 - len(missing_tolerated) / len(key_entry["must_tolerate"])
        base_score = PRIMARY_WEIGHT * primary_score + TOLERATED_WEIGHT * tolerated_recall

    score = max(0.0, base_score - MUST_NOT_PENALTY * len(must_not_hits))

    entry_result["matched_entry_number"] = generated_entry["entry_number"]
    entry_result["primary"] = primary
    entry_result["tolerated"] = tolerated
    entry_result["primary_correct"] = primary_correct
    entry_result["missing_tolerated"] = missing_tolerated
    entry_result["must_not_hits"] = must_not_hits
    entry_result["unjudged"] = unjudged
    entry_result["score"] = round(score, 4)

    return entry_result


def score_word(key_entries: list[dict], generated_entries: dict[tuple[str, int], dict]) -> list[dict]:
    """
    Scores each key entry against the generated entry with the same number.
    Entries the model cannot tell apart (same part of speech and explanation, e.g. 인사 人事 twice)
    are matched in whichever order scores best, since the order it returns them in is arbitrary.
    """
    entry_groups = {}
    for key_entry in key_entries:
        group_id = (key_entry["pos"], key_entry["explanation"])
        if group_id not in entry_groups:
            entry_groups[group_id] = []
        entry_groups[group_id].append(key_entry)

    entry_results = []
    for group_entries in entry_groups.values():
        group_generated = [generated_entries.get((key_entry["word"], key_entry["entry_number"])) for key_entry in group_entries]

        best_results = None
        best_total = -1.0
        for ordering in itertools.permutations(group_generated):       # The first ordering is the unchanged one, and ties keep it
            ordering_results = [score_entry(key_entry, generated_entry) for key_entry, generated_entry in zip(group_entries, ordering)]
            ordering_total = sum(entry_result["score"] for entry_result in ordering_results)
            if ordering_total > best_total:
                best_results = ordering_results
                best_total = ordering_total

        entry_results.extend(best_results)

    entry_results.sort(key=lambda entry_result: entry_result["entry_number"])
    return entry_results


def find_duplicate_primaries(entry_results: list[dict]) -> list[dict]:
    """Entries of one word sharing a primary within the same part of speech. Reported, not scored."""
    entry_numbers_by_primary = {}
    for entry_result in entry_results:
        if entry_result["primary"] is None:
            continue

        primary_id = (entry_result["word"], entry_result["pos"], normalise_gloss(entry_result["primary"]))
        if primary_id not in entry_numbers_by_primary:
            entry_numbers_by_primary[primary_id] = []
        entry_numbers_by_primary[primary_id].append(entry_result["entry_number"])

    duplicate_primaries = []
    for (word, pos, primary), entry_numbers in entry_numbers_by_primary.items():
        if len(entry_numbers) > 1:
            duplicate_primaries.append({"word": word, "pos": pos, "primary": primary, "entry_numbers": entry_numbers})

    return duplicate_primaries


def summarise_metrics(entry_results: list[dict], key_entries_by_word: dict[str, list[dict]]) -> dict:
    entry_count = len(entry_results)
    must_tolerate_count = 0
    for key_entries in key_entries_by_word.values():
        for key_entry in key_entries:
            must_tolerate_count += len(key_entry["must_tolerate"])

    correct_primary_count = 0
    missing_tolerated_count = 0
    must_not_hit_count = 0
    unjudged_count = 0
    perfect_entry_count = 0
    missing_entry_count = 0
    imperfect_words = set()
    for entry_result in entry_results:
        if entry_result["primary_correct"]:
            correct_primary_count += 1
        if entry_result["primary"] is None:
            missing_entry_count += 1
        if entry_result["score"] == 1.0:
            perfect_entry_count += 1
        else:
            imperfect_words.add(entry_result["word"])

        missing_tolerated_count += len(entry_result["missing_tolerated"])
        must_not_hit_count += len(entry_result["must_not_hits"])
        unjudged_count += len(entry_result["unjudged"])

    total_score = sum(entry_result["score"] for entry_result in entry_results)
    metrics = {
        "score": round(100 * total_score / entry_count, 1),
        "primary_accuracy": round(100 * correct_primary_count / entry_count, 1),
        "tolerate_recall": round(100 * (1 - missing_tolerated_count / must_tolerate_count), 1),
        "must_not_hits": must_not_hit_count,
        "unjudged": unjudged_count,
        "perfect_entries": perfect_entry_count,
        "entries": entry_count,
        "perfect_words": len(key_entries_by_word) - len(imperfect_words),
        "words": len(key_entries_by_word),
        "missing_entries": missing_entry_count,
    }

    return metrics


def compare_with_previous_round(entry_results: list[dict], round_number: int) -> tuple[list[str], list[str]] | None:
    previous_results_path = f"{ROUNDS_DIRECTORY}/round_{round_number - 1:02d}_results.json"
    if os.path.exists(previous_results_path) is False:
        return None

    with open(previous_results_path, "r", encoding="utf-8") as previous_results_file:
        previous_results = json.load(previous_results_file)

    previous_scores = {}
    for entry_result in previous_results["entries"]:
        previous_scores[(entry_result["word"], entry_result["entry_number"])] = entry_result["score"]

    fixed = []
    regressed = []
    for entry_result in entry_results:
        entry_id = (entry_result["word"], entry_result["entry_number"])
        if entry_id not in previous_scores:     # Entry added to the key since the previous round
            continue

        entry_label = f"{entry_result['word']}#{entry_result['entry_number']}"
        if previous_scores[entry_id] < 1.0 and entry_result["score"] == 1.0:
            fixed.append(entry_label)
        if previous_scores[entry_id] == 1.0 and entry_result["score"] < 1.0:
            regressed.append(entry_label)

    return fixed, regressed


def print_report(results: dict) -> None:
    metrics = results["metrics"]
    print(f"Score: {metrics['score']} / 100")
    print(f"Primary accuracy: {metrics['primary_accuracy']}%")
    print(f"Tolerate recall: {metrics['tolerate_recall']}%")
    print(f"Must-not hits: {metrics['must_not_hits']}")
    print(f"Unjudged extras: {metrics['unjudged']}")
    print(f"Perfect entries: {metrics['perfect_entries']} / {metrics['entries']}")
    print(f"Perfect words: {metrics['perfect_words']} / {metrics['words']}")
    print(f"Missing entries: {metrics['missing_entries']}")

    print("\nFailures:")
    for entry_result in results["entries"]:
        if entry_result["score"] == 1.0:
            continue

        entry_label = f"{entry_result['word']}#{entry_result['entry_number']}"
        print(f"  {entry_label} ({entry_result['pos']}, '{entry_result['explanation']}') score {entry_result['score']}")
        if entry_result["primary"] is None:
            print("    no generated entry")
            continue
        if entry_result["primary_correct"] is False:
            print(f"    wrong primary: {entry_result['primary']}")
        if entry_result["missing_tolerated"]:
            print(f"    missing tolerated: {entry_result['missing_tolerated']}")
        if entry_result["must_not_hits"]:
            print(f"    must-not hits: {entry_result['must_not_hits']}")

    print("\nUnjudged extras (not scored, candidates for the key):")
    for entry_result in results["entries"]:
        if entry_result["unjudged"]:
            print(f"  {entry_result['word']}#{entry_result['entry_number']} ({entry_result['primary']}): {entry_result['unjudged']}")

    print("\nDuplicate primaries (not scored):")
    for duplicate in results["duplicate_primaries"]:
        print(f"  {duplicate['word']} {duplicate['pos']} '{duplicate['primary']}': entries {duplicate['entry_numbers']}")

    if results["fixed"] is None:
        print("\nNo previous round to compare against")
    else:
        print(f"\nFixed since previous round: {results['fixed']}")
        print(f"Regressed since previous round: {results['regressed']}")


def score_word_glosses(generated_csv_path: str, round_number: int | None) -> dict:
    key_entries_by_word = load_answer_key()
    validate_answer_key(key_entries_by_word)
    generated_entries = load_generated_glosses(generated_csv_path)

    entry_results = []
    for key_entries in key_entries_by_word.values():
        word_results = score_word(key_entries, generated_entries)
        entry_results.extend(word_results)

    results = {
        "round": round_number,
        "generated_csv": generated_csv_path,
        "metrics": summarise_metrics(entry_results, key_entries_by_word),
        "fixed": None,
        "regressed": None,
        "duplicate_primaries": find_duplicate_primaries(entry_results),
        "entries": entry_results,
    }

    if round_number is not None:
        comparison = compare_with_previous_round(entry_results, round_number)
        if comparison is not None:
            results["fixed"], results["regressed"] = comparison

        os.makedirs(ROUNDS_DIRECTORY, exist_ok=True)
        results_path = f"{ROUNDS_DIRECTORY}/round_{round_number:02d}_results.json"
        with open(results_path, "w", encoding="utf-8") as results_file:
            json.dump(results, results_file, ensure_ascii=False, indent=2)       # Hangul is not ascii

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score a generated word glosses CSV against the answer key")
    parser.add_argument("generated_csv_path")
    parser.add_argument("--round", type=int, dest="round_number", help="Saves the results as this round and compares with the previous one")
    arguments = parser.parse_args()

    results = score_word_glosses(arguments.generated_csv_path, arguments.round_number)
    print_report(results)
    if arguments.round_number is not None:
        print(f"\nSaved to {ROUNDS_DIRECTORY}/round_{arguments.round_number:02d}_results.json")
