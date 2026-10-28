import csv
import json
import time
import anthropic
from anthropic import transform_schema
from anthropic.types.messages.batch_create_params import Request
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from backend.db.seed.build_words import NIKL_ENTRIES_PATH, group_and_filter_words_list

load_dotenv()   # The Anthropic client reads ANTHROPIC_API_KEY from the root .env

GENERATION_MODEL = "claude-haiku-5-5"
WORDS_FILE_PATH = None      # None generates every word, otherwise a file with one word per line (pilot, or resending failures)

RAW_GLOSSES_PATH = f"backend/db/seed/data/word_glosses_raw_{GENERATION_MODEL}.jsonl"
FAILURES_PATH = "backend/db/seed/data/word_gloss_failures.txt"
WORD_GLOSSES_PATH = "backend/db/seed/data/word_glosses.csv"

EFFORT = "medium"
MAX_TOKENS = 16000      # Thinking counts towards this, and only generated tokens are billed
POLL_INTERVAL_SECONDS = 60

NIKL_POS_LABELS = {
    "명": "noun", "동": "verb", "형": "adjective", "부": "adverb",
    "관": "determiner", "대": "pronoun", "수": "numeral", "감": "interjection",
}

# TODO: learner context, primary = meaning matching POS + explanation, tolerated = exact equivalents only,
SYSTEM_PROMPT = """"""

client = anthropic.Anthropic()


class GlossEntry(BaseModel):
    entry_number: int
    primary_gloss: str
    tolerated_glosses: list[str]


class WordGlosses(BaseModel):
    entries: list[GlossEntry]


OUTPUT_SCHEMA = transform_schema(WordGlosses)   # I am using pydantic models, but the API uses the raw json format


def load_nikl_entries() -> dict[str, list[dict[str, str]]]:
    # Read nikl_entries.csv
    # Filter and group using shared function from build_words.py (filter_words_list)
    # return homograph details grouped by word key
    ...

def build_batch_requests(nikl_entries_by_word: dict[str, list[dict[str, str]]]) -> list[Request]: 
    # If WORDS_FILE_PATH is set, keep only those words and print any not in word_groups
    # Each custom ID is hex
    ...


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
