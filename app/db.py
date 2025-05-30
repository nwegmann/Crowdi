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
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                trust_score FLOAT DEFAULT 5.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Items available for lending
        c.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                image_path TEXT,
                hashtags TEXT,
                status TEXT DEFAULT 'available',
                city TEXT,
                latitude REAL,
                longitude REAL,
                condition_score FLOAT DEFAULT 5.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )
        ''')
        # Lending records
        c.execute('''
            CREATE TABLE IF NOT EXISTS lendings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                lender_id INTEGER NOT NULL,
                borrower_id INTEGER NOT NULL,
                lend_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                return_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY(item_id) REFERENCES items(id),
                FOREIGN KEY(lender_id) REFERENCES users(id),
                FOREIGN KEY(borrower_id) REFERENCES users(id)
            )
        ''')
        # Conversations
        c.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                item_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(id),
                FOREIGN KEY (user2_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        ''')
        # Messages
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER,
                content TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seen INTEGER DEFAULT 0,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id)
            )
        ''')
        # Requested items
        c.execute('''
            CREATE TABLE IF NOT EXISTS requested_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                image_path TEXT,
                hashtags TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # User ratings
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rater_id INTEGER,
                rated_id INTEGER,
                rating FLOAT NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rater_id) REFERENCES users(id),
                FOREIGN KEY (rated_id) REFERENCES users(id),
                UNIQUE(rater_id, rated_id)
            )
        ''')
        # Borrow requests
        c.execute('''
            CREATE TABLE IF NOT EXISTS borrow_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(item_id) REFERENCES items(id),
                FOREIGN KEY(requester_id) REFERENCES users(id)
            )
        ''')
        # Notifications
        c.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seen INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()