import sqlite3
from app.db import DB_PATH

with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    c.execute("PRAGMA table_info(requested_items);")
    columns = [col[1] for col in c.fetchall()]
    if "hashtags" not in columns:
        print("Adding 'hashtags' column to requested_items...")
        c.execute("ALTER TABLE requested_items ADD COLUMN hashtags TEXT;")
        conn.commit()
        print("Column added.")
    else:
        print("Column 'hashtags' already exists.")
