from db import cursor, conn
from utils import now

def add_log(user_id, action, details=""):
    cursor.execute(
        "INSERT INTO logs (user_id, action, details, date) VALUES (?, ?, ?, ?)",
        (user_id, action, details, now())
    )
    conn.commit()

def get_logs(limit=50):
    cursor.execute("SELECT user_id, action, details, date FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    return cursor.fetchall()

def get_errors(limit=20):
    cursor.execute("SELECT user_id, action, details, date FROM logs WHERE action='ERROR' ORDER BY id DESC LIMIT ?", (limit,))
    return cursor.fetchall()
