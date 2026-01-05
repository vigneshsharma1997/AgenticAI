# core/db/init_db.py
import sqlite3

DB_PATH = "/Users/vigneshsharma/Desktop/Langgraph/pod_containers/storage_db.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sf_sessions (
        session_id TEXT PRIMARY KEY,
        account TEXT NOT NULL,
        host TEXT NOT NULL,
        token TEXT NOT NULL,
        token_issued_at REAL NOT NULL,
        expires_at REAL NOT NULL
    )
    """
)

conn.commit()
conn.close()

