import anthropic
import time
from pydantic import BaseModel

from backend.schemas import SentencePair

client = anthropic.Anthropic()

class SentencePackage(BaseModel):
    sentences: list[SentencePair]


def generate_sentences(sentence_words: list[str], num_sentences_generated: int) -> list[SentencePair]:

    vocab_string = ", ".join(sentence_words)

    prompt = f"""
    Generate {num_sentences_generated} coherent Korean sentences using primarily these vocabulary words: {vocab_string}.
    Particles, basic conjugations, and connectors are allowed as needed for grammar.
    The sentences should sound natural and grammatically correct. Do not start with a greeting.
    Intended for users learning Korean and seeing their learnt vocabulary in context.

    For each sentence:
        - target: Korean sentence.
        - source: English translation.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.messages.parse(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                output_format=SentencePackage,
            )

            sentences = response.parsed_output.sentences    # SentencePackage is just a wrapper to define shape of LLM output - unpackaged to give caller the data directly

            # For testing
            print(f"\nSentences generated using vocab:\n{vocab_string}\n")
            for sentence in sentences:
                print(f"Target: {sentence.target}\nSource: {sentence.source}\n")

            return sentences

        except (anthropic.APIConnectionError, anthropic.RateLimitError) as e:
            if attempt == max_retries - 1:
                print(f"All {max_retries} transient attempts failed: {e}")
                raise
            else:
                wait = 2 ** attempt     # Exponentially backing off
                print(f"Attempt {attempt} failed, retrying in {wait} seconds: {e}")
                time.sleep(wait)

        except anthropic.APIStatusError as e:
            print(f"Non-transient error: {e}")
            raise   # Raise immediately if error is not transient

