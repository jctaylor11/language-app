from fastapi import APIRouter
from sqlalchemy import text, insert
from pydantic import BaseModel

from backend.db.connection import engine
from backend.llm import generate_sentences
from backend.lemmatiser import extract_lemmas
from backend.db.models import Sentence
from backend.enums import SentenceResultStatus


router = APIRouter()

class SentenceResult(BaseModel):
    sentence_id: int
    #TODO: session_id: int - add when session is wired to sentences too, NULL until then
    status: SentenceResultStatus


@router.get("/sentences")
def get_sentence_batch(user_id: int, num_words: int):
    # TODO: Extract this (along with others) to a get_eligible_sentences function that returns the rows. The rows are procesed to applicable shape
    # Will get many more sentences (limit 50) than LLM because querying DB is free, compared to querying LLM
    with engine.begin() as conn: 
        eligible_sentences = conn.execute(text("""
        SELECT s.id, s.target, s.source
        FROM sentences s
        WHERE NOT EXISTS (
            SELECT 1
            FROM sentence_results sr
            WHERE sr.sentence_id = s.id
            AND sr.user_id = :user_id
        )
        LIMIT 50    -- Fetch many eligible in one batch for the session since free from database (rather than LLM)
        """), {"user_id": user_id}).fetchall()

    if len(eligible_sentences) > 3:
        return {"sentences": [{"id": row.id, "target": row.target, "source": row.source} for row in eligible_sentences]}

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT target
            FROM words
            JOIN user_words ON user_words.word_id = words.id
            WHERE user_id = :user_id
            ORDER BY RANDOM()
            LIMIT :num_words
        """), {"user_id": user_id, "num_words": num_words})
    
        rows = result.fetchall()

    sentence_words = [row.target for row in rows]

    # API request
    sentences = generate_sentences(sentence_words)

    # Lemmas are needed as a standard form to reference vocab table (citation form)
    for sentence in sentences:
        sentence.lemmas = extract_lemmas(sentence.target)

    # Collate all lemmas for single database query to get word IDs
    all_lemmas_in_sentence = set()
    for sentence in sentences:
        for lemma in sentence.lemmas:
            all_lemmas_in_sentence.add(lemma)
    all_lemmas_in_sentence = list(all_lemmas_in_sentence)

    with engine.begin() as conn:
        result = conn.execute(insert(Sentence).returning(Sentence.id, Sentence.target, Sentence.source),    # Core with expression language used to handle multi-rows
            [{"target": sentence.target, "source": sentence.source, "lemma_count": len(sentence.lemmas)} for sentence in sentences])

        rows = result.fetchall()

        # Word IDs are queried so the the words corresponding to each sentence can be inserted into sentence_words table
        result = conn.execute(text("""
            SELECT id, target FROM words
            WHERE target = ANY(:lemmas)
            """), {"lemmas": all_lemmas_in_sentence})

        # Mapping lemmas to the word ID so we can map which words are in each sentence, reference in citation form
        lemma_to_word_id = {row.target: row.id for row in result}

        # Assembling list of row objects to insert in sentence_words table
        sentence_word_mappings = []
        for row, sentence in zip(rows, sentences):  # Zipped to give access to both sentence IDs (in row) and sentence lemmas (in sentence) in each iteration
            for lemma in sentence.lemmas:           
                if lemma in lemma_to_word_id:       # Sentence lemmas may not all be in vocab table (hence will have no ID)
                    sentence_word_mappings.append({"sentence_id": row.id, "word_id": lemma_to_word_id[lemma]})

        # Record which word IDs are in each sentence to track which words have been reviewed by the user when they review each sentence
        conn.execute(text("""
            INSERT INTO sentence_words (sentence_id, word_id)
            VALUES (:sentence_id, :word_id)
            ON CONFLICT DO NOTHING
        """), sentence_word_mappings)

    return {"sentences": [{"id": row.id, "target": row.target, "source": row.source} for row in rows]}

@router.post("/sentence-results")
def create_sentence_result(user_id: int, payload: SentenceResult):      # TODO: batch these and send via beacon on page close
    params = {"user_id": user_id, **payload.model_dump(mode="json")}

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sentence_results (user_id, sentence_id, status)
            VALUES (:user_id, :sentence_id, :status)
        """), params)

    return {"saved_sentence_id": payload.sentence_id}