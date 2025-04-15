import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "crowdi.db")

def get_path():
    return DB_PATH

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Users
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        ''')
        # Items available for lending
        c.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                hashtags TEXT,
                status TEXT DEFAULT 'available',
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )
        ''')
        # Lending records
        c.execute('''
            CREATE TABLE IF NOT EXISTS lendings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                borrower_id INTEGER NOT NULL,
                lend_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                return_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY(item_id) REFERENCES items(id),
                FOREIGN KEY(borrower_id) REFERENCES users(id)
            )
        ''')
        conn.commit()