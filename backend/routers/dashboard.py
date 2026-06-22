from fastapi import APIRouter
from sqlalchemy import text

from backend.db.connection import engine

router = APIRouter()


@router.get("/dashboard/words")
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


@router.get("/dashboard/hero-metrics")
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


@router.get("/dashboard/word-chart-data")
def get_word_chart_data(user_id: int):
    with engine.begin() as conn:
        query = conn.execute(text("""
            WITH date_series AS (
                SELECT (
                    date_trunc('day', generate_series (
                        NOW() - INTERVAL '30 days',
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

    cumulative_words = [{"series_date": row.series_date, "cum_words": row.words_added} for row in rows]

    return {"cumulative_words": cumulative_words}