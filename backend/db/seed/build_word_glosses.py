import csv
import json
import time
import anthropic
from anthropic import transform_schema
from anthropic.types.messages.batch_create_params import Request
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from backend.db.seed.build_words import NIKL_ENTRIES_PATH, group_and_filter_words_list

load_dotenv()

GENERATION_MODEL = "claude-haiku-5-5"
WORDS_FILE_PATH = "backend/db/seed/data/pilot_words.txt"      # None generates every word, otherwise a file with one word per line (pilot, or resending failures)

RAW_GLOSSES_PATH = f"backend/db/seed/data/word_glosses_raw_{GENERATION_MODEL}.jsonl"
FAILURES_PATH = "backend/db/seed/data/word_gloss_failures.txt"
WORD_GLOSSES_PATH = "backend/db/seed/data/word_glosses.csv"

EFFORT = "medium"
MAX_TOKENS = 16000           # Thinking counts towards this, and only generated tokens are billed
POLL_INTERVAL_SECONDS = 60

NIKL_POS_LABELS = {
    "명": "noun", "동": "verb", "형": "adjective", "부": "adverb",
    "관": "determiner", "대": "pronoun", "수": "numeral", "감": "interjection",
}

SYSTEM_PROMPT = """
 <instructions>
You will receive one Korean word and its entries, each with an entry number, part of speech, and any explanation. For every entry, give one primary gloss and any tolerated glosses, returned under the same entry number.
Use each entry's part of speech and explanation to identify which meaning it refers to. If an entry covers several related senses, gloss the one a learner is most likely to be taught.
An explanation may be hanja, a short Korean description, a collocation where ~ stands for the word, or empty. When it's empty, use the part of speech and the most common meaning.
For the primary gloss, choose the most common, natural English word or short phrase for that meaning. Match its form to the part of speech: verbs as "to" plus the verb (먹다 → "to eat"), adjectives as the bare adjective (크다 → "big"), and nouns without an article (학교 → "school"). Write primary glosses in American English, since most Korean loanwords come from it (아파트 → "apartment").
When a word has more than one entry, give each entry a primary gloss that distinguishes its meaning from the others. The exception is entries with the same meaning in different parts of speech, such as a pronoun and a determiner that both mean "this": these can share a primary gloss.
For tolerated glosses, include only other words a learner might type that mean exactly the same as the primary gloss, in that sense and part of speech. Leave out broader, narrower or merely related words, and don't repeat the primary gloss.
</instructions>

 <context>
The learner is an English speaker learning Korean. The app shows the learner a Korean word, and the learner types its meaning in English.
A Korean word has one or more entries: separate dictionary entries for the same spelling, each distinguished by its part of speech and, where present, an explanation. Each entry gets one primary gloss and zero or more tolerated glosses.
The primary gloss is the answer displayed as that entry's meaning. Tolerated glosses have exactly the same meaning as the primary gloss, and are also accepted as correct answers.
The app shows only the spelling, not which entry is meant, so the learner's answer is correct if it matches any of the word's glosses. A loose tolerated gloss on one entry therefore lets a wrong answer pass for the whole word, so tolerated glosses must be true equivalents. An empty list is better than a near miss.
Each entry's glosses are stored against its part of speech and reviewed entry by entry, so they must be accurate for that entry specifically.
</context>

<example>
<input>
{"word": "차", "entries": [
  {"entry_number": 1, "part_of_speech": "noun", "explanation": "車"},
  {"entry_number": 2, "part_of_speech": "noun", "explanation": "差"},
  {"entry_number": 3, "part_of_speech": "noun", "explanation": "茶"}
]}
</input>
<output>
{"entries": [
  {"entry_number": 1, "primary_gloss": "car", "tolerated_glosses": ["automobile"]},
  {"entry_number": 2, "primary_gloss": "difference", "tolerated_glosses": []},
  {"entry_number": 3, "primary_gloss": "tea", "tolerated_glosses": []}
]}
</output>
"vehicle" is not tolerated for entry 1 because it is broader than "car".
</example>
 """

client = anthropic.Anthropic()


class GlossEntry(BaseModel):
    entry_number: int
    primary_gloss: str
    tolerated_glosses: list[str]


class WordGlosses(BaseModel):
    entries: list[GlossEntry]


OUTPUT_SCHEMA = transform_schema(WordGlosses)   # As I am using pydantic models, but the API uses the raw json format


def load_nikl_entries() -> dict[str, list[dict[str, str]]]:
    with open(NIKL_ENTRIES_PATH, 'r', newline="", encoding="utf-8") as nikl_entries:
        nikl_rows = list(csv.DictReader(nikl_entries))

    nikl_entries_by_word, rejections = group_and_filter_words_list(nikl_rows)

    return nikl_entries_by_word


def format_word_prompt(word: str, entries: list[dict[str, str]]) -> str:
    prompt_entries = []
    for entry_number, entry in enumerate(entries, start=1):     # Position in the word's entries, rederived the same way to match results back assuming source csv unchanged
        prompt_entry = {
            "entry_number": entry_number,
            "part_of_speech": NIKL_POS_LABELS[entry["pos"]],
            "explanation": entry["explanation"],
        }
        prompt_entries.append(prompt_entry)

    prompt_data = {"word": word, "entries": prompt_entries}
    prompt = json.dumps(prompt_data, ensure_ascii=False)        # Hangul is not ascii, it will not render if True

    return prompt


def select_words(nikl_entries_by_word: dict[str, list[dict[str, str]]]) -> list[str]:
    if WORDS_FILE_PATH is None:
        words = list(nikl_entries_by_word)
    else:
        with open(WORDS_FILE_PATH, 'r', encoding="utf-8") as words_file:
            listed_words = words_file.read().split()     # No NIKL word contains a space, and this skips blank lines

        words = []
        for word in listed_words:
            if word not in nikl_entries_by_word:
                print(f"Skipping {word}: not in the NIKL entries")
                continue

            words.append(word)

    return words


def build_batch_requests(nikl_entries_by_word: dict[str, list[dict[str, str]]]) -> list[Request]:
    words = select_words(nikl_entries_by_word)

    batch_requests = []
    for word in words:
        entries = nikl_entries_by_word[word]

        request: Request = Request(
            custom_id=word.encode().hex(),
            params=MessageCreateParamsNonStreaming(
                model=GENERATION_MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": format_word_prompt(word, entries)
                    }
                ],
                output_config={
                    "effort": EFFORT,
                    "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}
                },
            ),
        )

        batch_requests.append(request)    

    return batch_requests


def submit_gloss_batch(batch_requests: list[Request]) -> str:
    # Batch API call, print its id 
    ...


def poll_for_batch(batch_id: str) -> None:
    # Until processing_status is "ended": print progress, sleep POLL_INTERVAL_SECONDS
    ...


def collect_gloss_batch(batch_id: str) -> None:
    # Save raw jsonl
    # Write failed words to FAILURES_PATH, print counts and token totals 
    ...


def build_word_glosses_csv(word_groups: dict[str, list[dict[str, str]]]) -> None:
    # Read RAW_GLOSSES_PATH, last line per word wins (resends replace earlier results)
    # Write WORD_GLOSSES_PATH, print rows written and the missing count
    ...


def build_word_glosses() -> None:
    nikl_entries_by_word = load_nikl_entries()
    batch_requests = build_batch_requests(nikl_entries_by_word)     # Uses hex for custom ID
    batch_id = submit_gloss_batch(batch_requests)
    poll_for_batch(batch_id)
    collect_gloss_batch(batch_id)
    build_word_glosses_csv(nikl_entries_by_word)


if __name__ == "__main__":
    build_word_glosses()
