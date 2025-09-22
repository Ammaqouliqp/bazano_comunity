import sqlite3
from pathlib import Path

DB_PATH = Path("shop.db")
conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
cursor = conn.cursor()

def add_log(user_id, action, details):
    cursor.execute("""
        INSERT INTO logs (user_id, action, details)
        VALUES (?, ?, ?)
    """, (user_id, action, details ))
    conn.commit()

def read_logs(limit: int = 20):
    cursor.execute("""
        SELECT id, user_id, action, details
        FROM logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    return cursor.fetchall()
