import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

DB_PATH = os.getenv("IME_DB_PATH", "interview_memory.db")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn, conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                source_type TEXT NOT NULL,
                source_path TEXT,
                transcript_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcript_id INTEGER NOT NULL,
                summary TEXT NOT NULL,
                strengths TEXT,
                weaknesses TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (transcript_id) REFERENCES transcripts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcript_id INTEGER,
                question_text TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT NOT NULL,
                difficulty TEXT DEFAULT 'medium',
                created_at TEXT NOT NULL,
                FOREIGN KEY (transcript_id) REFERENCES transcripts(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def insert_transcript(title: str | None, source_type: str, source_path: str | None, transcript_text: str) -> int:
    with closing(get_conn()) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO transcripts (title, source_type, source_path, transcript_text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, source_type, source_path, transcript_text, utc_now()),
        )
        return int(cursor.lastrowid)


def list_transcripts() -> list[dict]:
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT id, title, source_type, source_path, transcript_text, created_at
            FROM transcripts
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_transcript(transcript_id: int) -> dict | None:
    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT id, title, source_type, source_path, transcript_text, created_at
            FROM transcripts
            WHERE id = ?
            """,
            (transcript_id,),
        ).fetchone()
    return dict(row) if row else None


def insert_feedback(transcript_id: int, summary: str, strengths: list[str], weaknesses: list[str]) -> int:
    with closing(get_conn()) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO feedback (transcript_id, summary, strengths, weaknesses, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (transcript_id, summary, json.dumps(strengths), json.dumps(weaknesses), utc_now()),
        )
        return int(cursor.lastrowid)


def add_question(
    question_text: str,
    category: str,
    tags: list[str],
    difficulty: str = "medium",
    transcript_id: int | None = None,
) -> int:
    with closing(get_conn()) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO questions (transcript_id, question_text, category, tags, difficulty, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (transcript_id, question_text, category, json.dumps(tags), difficulty, utc_now()),
        )
        return int(cursor.lastrowid)


def list_questions(category: str | None = None) -> list[dict]:
    query = """
        SELECT id, transcript_id, question_text, category, tags, difficulty, created_at
        FROM questions
    """
    params: tuple = ()
    if category:
        query += " WHERE category = ?"
        params = (category,)
    query += " ORDER BY created_at DESC"

    with closing(get_conn()) as conn:
        rows = conn.execute(query, params).fetchall()

    result = []
    for row in rows:
        item = dict(row)
        item["tags"] = json.loads(item["tags"])
        result.append(item)
    return result


def random_quiz_questions(limit: int = 5) -> list[dict]:
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT id, question_text, category, tags, difficulty
            FROM questions
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    quiz = []
    for row in rows:
        item = dict(row)
        item["tags"] = json.loads(item["tags"])
        quiz.append(item)
    return quiz


def save_quiz_attempt(total_questions: int, correct_answers: int) -> int:
    with closing(get_conn()) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO quiz_attempts (total_questions, correct_answers, created_at)
            VALUES (?, ?, ?)
            """,
            (total_questions, correct_answers, utc_now()),
        )
        return int(cursor.lastrowid)


def analytics_snapshot() -> dict:
    with closing(get_conn()) as conn:
        attempts = conn.execute(
            """
            SELECT total_questions, correct_answers, created_at
            FROM quiz_attempts
            ORDER BY created_at DESC
            """
        ).fetchall()

        category_counts = conn.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM questions
            GROUP BY category
            ORDER BY count DESC
            """
        ).fetchall()

        weak = conn.execute(
            """
            SELECT q.category, COUNT(*) AS misses
            FROM questions q
            LEFT JOIN feedback f ON f.transcript_id = q.transcript_id
            GROUP BY q.category
            ORDER BY misses DESC
            """
        ).fetchall()

    attempts_list = [dict(row) for row in attempts]
    avg_score = 0.0
    if attempts_list:
        avg_score = sum(
            (a["correct_answers"] / a["total_questions"]) * 100 if a["total_questions"] else 0
            for a in attempts_list
        ) / len(attempts_list)

    return {
        "attempt_count": len(attempts_list),
        "average_score": round(avg_score, 2),
        "recent_attempts": attempts_list[:10],
        "question_categories": [dict(row) for row in category_counts],
        "weak_categories": [dict(row) for row in weak[:5]],
    }
