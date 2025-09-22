import sqlite3

conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

cursor.execute("UPDATE users SET role = 'manager' WHERE id = 1")

conn.commit()
conn.close()

print("Role for user id=1 updated to manager ✅")
