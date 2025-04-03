import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "crowdi.db")

def get_path():
    return DB_PATH

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Questions
        c.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                type TEXT NOT NULL
            )
        ''')
        # Responses
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
        # Users
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        ''')
        # Options (for multiple choice)
        c.execute('''
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                FOREIGN KEY(question_id) REFERENCES questions(id)
            )
        ''')
        conn.commit()