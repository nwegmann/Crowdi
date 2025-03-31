import sqlite3
import os

# Initialize SQLite DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "crowdi.db")

def get_path():
    return DB_PATH

def get_questions(user_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        if user_id:
            c.execute("""
                SELECT q.id, q.text, q.type,
                EXISTS (
                    SELECT 1 FROM responses r
                    WHERE r.question_id = q.id AND r.user_id = ?
                ) AS has_responded
                FROM questions q
                ORDER BY q.id DESC
            """, (user_id,))
        else:
            c.execute("""
                SELECT id, text, type, 0 AS has_responded
                FROM questions
                ORDER BY id DESC
            """)
        questions = c.fetchall()

        questions_with_options = []
        for q in questions:
            q_id, text, q_type, has_responded = q
            opts = []
            if q_type == "multiple":
                c.execute("SELECT id, option_text FROM options WHERE question_id = ?", (q_id,))
                opts = c.fetchall()
            questions_with_options.append((q_id, text, q_type, has_responded, opts))
            
    return questions_with_options

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Create questions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                type TEXT NOT NULL
            )
        ''')
        # Create responses table
        c.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                response TEXT NOT NULL,
                FOREIGN KEY(question_id) REFERENCES questions(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                FOREIGN KEY(question_id) REFERENCES questions(id)
            )
        ''')
        conn.commit()

def add_response(question_id: int, response: str):
    conn = sqlite3.connect(get_path())
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            response TEXT
        )
    """)
    c.execute("INSERT INTO responses (question_id, response) VALUES (?, ?)", (question_id, response))
    conn.commit()
    conn.close()