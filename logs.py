from db import cursor, conn

def log_event(user_id, action, details=""):
    cursor.execute("INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)", (user_id, action, details))
    conn.commit()
