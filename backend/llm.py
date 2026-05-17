import anthropic
from pydantic import BaseModel

client = anthropic.Anthropic()

def generate_sentences(sentence_words: list[str]) -> str:
    vocab_string = ", ".join(sentence_words)

    class SentencesPair(BaseModel):
        target: str
        source: str

    class SentencesPackage(BaseModel):
        sentences: list[SentencesPair]
    
    prompt = f"""
    Generate 3 coherent Korean sentences using primarily these vocabulary words: {vocab_string}.
    Particles, basic conjugations, and connectors are allowed as needed for grammar. 
    The sentences should sound natural and grammatically correct. 
    Intended for users learning Korean and seeing their learnt vocabulary in context.

    For each sentence:
        - target: Korean sentence.
        - source: English translation. 
    """

    response = client.messages.parse(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        output_format=SentencesPackage,
    )

    print(response) # Testing

    sentences = response.parsed_output.sentences

    return sentences
