from sqlalchemy import text, insert
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from backend.db.connection import get_engine
from backend.db.models import Sentence
from backend.llm import generate_sentences
from backend.enums import VocabResultStatus, SentenceResultStatus
from backend.lemmatiser import extract_lemmas

app = FastAPI()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

engine = get_engine()


class WordResult(BaseModel):
    word_id: int
    response_time_ms: int | None = None
    answered_at: datetime | None = None
    raw_keystrokes: str | None = None
    status: VocabResultStatus
    session_position: int


class VocabResults(BaseModel):
    session_id: int
    word_results: list[WordResult]


class SentenceResult(BaseModel):
    sentence_id: int
    #TODO: session_id: int - add when session is wired to sentences too, NULL until then
    status: SentenceResultStatus


@app.post("/sessions")
async def create_session(user_id: int):
    """Create new session and return session ID to client"""
    # Create new entry in sessions
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO sessions (user_id, started_at)
            VALUES (:user_id, CURRENT_TIMESTAMP)
            RETURNING id             
        """), {"user_id": user_id})

        session_id = result.scalar()

    return {"session_id": session_id}


@app.get("/words")
async def get_word_batch(user_id: int):
    """Fetch batch of words to show to user"""
    # Fetch a batch of 5 words from database
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT id, target, source
            FROM words
            JOIN user_words ON user_words.word_id = words.id
            WHERE user_id = :user_id
            ORDER BY RANDOM()
            LIMIT 5
        """), {"user_id": user_id})

        rows = result.fetchall()    
        word_batch = [row._asdict() for row in rows]

    return {"word_batch": word_batch}


@app.post("/vocab-results")
async def create_vocab_results(user_id: int, vocab_results: VocabResults):
    """Save user's response data for each word in the session batch"""

    params = [{"user_id": user_id, "session_id": vocab_results.session_id, **word_result.model_dump(mode="json")} for word_result in vocab_results.word_results]

    with engine.begin() as conn:
        # All response data for each word in the session batch saved
        conn.execute(text("""
            INSERT INTO vocab_results (user_id, session_id, word_id, response_time_ms, answered_at, raw_keystrokes, status, session_position)
            VALUES (:user_id, :session_id, :word_id, :response_time_ms, :answered_at, :raw_keystrokes, :status, :session_position)
        """), params)

        # Session's completed_at value is updated each flush - final update accurate logs completion
        conn.execute(text("""
            UPDATE sessions
            SET completed_at = NOW()
            WHERE id = :session_id
        """), {"session_id": vocab_results.session_id})
    
    return {"results_saved": len(vocab_results.word_results)} 


@app.get("/sentences")
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


@app.post("/sentence-results")
def create_sentence_result(user_id: int, payload: SentenceResult):      # TODO: batch these and send via beacon on page close
    params = {"user_id": user_id, **payload.model_dump(mode="json")}

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sentence_results (user_id, sentence_id, status)
            VALUES (:user_id, :sentence_id, :status)
        """), params)

    return {"saved_sentence_id": payload.sentence_id}


@app.get("/dashboard/words")
def get_dashboard_words(user_id: int):
    with engine.begin() as conn:
        query = conn.execute(text("""
            SELECT 
                w.id,
                w.target, 
                UPPER(LEFT(w.source, 1)) || LOWER(SUBSTRING(w.source FROM 2)) AS source, 
                COUNT(vr.id) AS times_reviewed,
                AVG(vr.response_time_ms) / 1000.0 / LENGTH(w.target) as av_s_per_syllable,
                COUNT(*) FILTER (WHERE vr.status = 'correct_first_try')::numeric / COUNT(*) AS accuracy
            FROM words w
            JOIN user_words uw ON w.id = uw.word_id
            JOIN vocab_results vr ON w.id = vr.word_id
            WHERE uw.user_id = :user_id
            GROUP BY 
                w.id, 
                w.target, 
                w.source;
            """), {"user_id": user_id})
        
        rows = query.fetchall()
        
        word_table = [{"id": row.id, "target": row.target, "source": row.source, "times_reviewed": row.times_reviewed, "av_s_per_syllable": row.av_s_per_syllable, "accuracy": row.accuracy} for row in rows]

    return {"words": word_table}


@app.get("/dashboard/hero-metrics")
def get_dashboard_hero_metrics(user_id: int):
    with engine.begin() as conn:
        query = conn.execute(text("""
            WITH total_reviewed AS (
                SELECT 1 FROM vocab_results WHERE user_id = :user_id
            )
            SELECT 
                (SELECT COUNT(*) FROM user_words WHERE user_id = :user_id) AS total_words,
                (SELECT COUNT(*) FROM total_reviewed) + (
                    SELECT COUNT(*)
                    FROM sentence_results sr
                    JOIN sentence_words sw ON sr.sentence_id = sw.sentence_id
                    WHERE sr.user_id = :user_id
                ) AS total_reviewed
            """), {"user_id": user_id})
    
        row = query.fetchone()

        hero_metrics = {"total_words": row.total_words, "words_reviewed": row.total_reviewed} 

    return {"metrics": hero_metrics}
