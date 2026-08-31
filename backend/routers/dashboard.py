from fastapi import APIRouter, Depends
from sqlalchemy import text, Connection
from typing import Annotated

from backend.auth.access_token import decode_access_token
from backend.db.connection import get_read_connection

router = APIRouter()


def get_word_table_data(conn: Connection, user_id: int) -> list[dict]:
    query = conn.execute(text("""
        SELECT
            w.id,
            w.target,
            UPPER(LEFT(w.source, 1)) || LOWER(SUBSTRING(w.source FROM 2)) AS source,
            COUNT(vr.id) AS times_reviewed,
            AVG(vr.response_time_ms) / 1000.0 / LENGTH(w.target) as av_s_per_syllable,
            COUNT(*) FILTER (WHERE vr.status = 'correct_first_try')::numeric / NULLIF(COUNT(vr.id), 0) AS accuracy
        FROM words w
        JOIN user_words uw ON w.id = uw.word_id
        LEFT JOIN vocab_results vr ON w.id = vr.word_id
        WHERE uw.user_id = :user_id
        GROUP BY
            w.id,
            w.target,
            w.source;
        """), {"user_id": user_id})

    rows = query.fetchall()

    return [{
        "id": row.id,
        "target": row.target,
        "source": row.source,
        "times_reviewed": row.times_reviewed,
        "av_s_per_syllable": float(row.av_s_per_syllable) if row.av_s_per_syllable is not None else None,
        "accuracy": float(row.accuracy) if row.accuracy is not None else None,
    } for row in rows]


def get_sentences_table_data(conn: Connection, user_id: int) -> list[dict]:
    query = conn.execute(text("""
        SELECT s.id, s.target, s.source
        FROM sentences s
        JOIN sentence_results sr ON s.id = sr.sentence_id
        WHERE sr.user_id = :user_id
        """), {"user_id": user_id})

    rows = query.fetchall()

    return [{"id": row.id, "target": row.target, "source": row.source} for row in rows]


def get_hero_metrics(conn: Connection, user_id: int) -> dict:
    query = conn.execute(text("""
        WITH total_reviewed AS (
            SELECT 1 FROM vocab_results WHERE user_id = :user_id AND status NOT IN ('skipped', 'cheated')    -- A skipped or cheated word isn't a review the user earned
        )
        SELECT
            (SELECT COUNT(*) FROM user_words WHERE user_id = :user_id) AS total_words,
            (SELECT COUNT(*) FROM total_reviewed) + (
                SELECT COUNT(*)
                FROM sentence_results sr
                JOIN sentence_words sw ON sr.sentence_id = sw.sentence_id
                WHERE sr.user_id = :user_id
                AND sr.status NOT IN ('skipped', 'cheated')     -- Words from a skipped or cheated sentence aren't reviews the user earned either
            ) AS total_reviewed
        """), {"user_id": user_id})

    row = query.fetchone()

    return {"total_words": row.total_words, "words_reviewed": row.total_reviewed}


def get_cumulative_word_chart_data(conn: Connection, user_id: int) -> list[dict]:
    query = conn.execute(text("""
        WITH date_series AS (
            SELECT (
                date_trunc('day', generate_series (
                    NOW() - INTERVAL '29 days',
                    NOW(),
                    '1 day'::interval
                ))
            ) AS series_date
        ),
        day_counts AS (
            SELECT
                COUNT(*) AS cum_words,
                date_trunc('day', added_at) AS date_added
            FROM user_words
            WHERE user_id = :user_id
            GROUP BY date_trunc('day', added_at)
        )
        SELECT
            series_date,
            SUM(COALESCE(cum_words, 0)) OVER (ORDER BY series_date) AS words_added
        FROM date_series
        LEFT JOIN day_counts
        ON date_series.series_date = day_counts.date_added
        ORDER BY series_date
    """), {"user_id": user_id})

    rows = query.fetchall()

    return [{"series_date": row.series_date, "cum_words": int(row.words_added)} for row in rows]


@router.get("/dashboard/words")
def get_dashboard_words(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)]) -> dict:
    words_table_data = get_word_table_data(conn, user_id)

    return {"words": words_table_data}


@router.get("/dashboard/hero-metrics")
def get_dashboard_hero_metrics(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)]) -> dict:
    hero_metrics = get_hero_metrics(conn, user_id)

    return {"metrics": hero_metrics}


@router.get("/dashboard/word-chart-data")
def get_word_chart_data(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)]) -> dict:
    cumulative_words = get_cumulative_word_chart_data(conn, user_id)

    return {"cumulative_words": cumulative_words}


@router.get("/dashboard/sentences")
def get_dashboard_sentences(conn: Annotated[Connection, Depends(get_read_connection)], user_id: Annotated[int, Depends(decode_access_token)]) -> dict:
    sentences_table_data = get_sentences_table_data(conn, user_id)

    return {"sentences": sentences_table_data}
