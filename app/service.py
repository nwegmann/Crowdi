import sqlite3
from .db import DB_PATH

def fetch_questions():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, text, type FROM questions ORDER BY id DESC")
        return c.fetchall()

def fetch_options(question_id, conn):
    c = conn.cursor()
    c.execute("SELECT id, option_text FROM options WHERE question_id = ?", (question_id,))
    return c.fetchall()

def fetch_responses(question_id, conn):
    c = conn.cursor()
    c.execute("SELECT response FROM responses WHERE question_id = ?", (question_id,))
    return [row[0] for row in c.fetchall()]

def check_user_has_responded(question_id, user_id, conn):
    c = conn.cursor()
    c.execute(
        "SELECT 1 FROM responses WHERE question_id = ? AND user_id = ? LIMIT 1",
        (question_id, user_id)
    )
    return c.fetchone() is not None

def get_questions_with_data(user_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        result = []
        for q_id, text, q_type in fetch_questions():
            opts = fetch_options(q_id, conn) if q_type == "multiple" else []
            responses = fetch_responses(q_id, conn)
            has_responded = check_user_has_responded(q_id, user_id, conn) if user_id else False
            result.append((q_id, text, q_type, has_responded, opts, responses))
        return result