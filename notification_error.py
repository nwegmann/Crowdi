import sqlite3
from app.db import DB_PATH

with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE messages ADD COLUMN seen INTEGER DEFAULT 0;")
        print("✅ 'seen' column added to messages.")
    except sqlite3.OperationalError as e:
        print("⚠️ Could not add column (maybe it already exists?):", e)
