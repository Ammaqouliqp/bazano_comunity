import sqlite3

conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

cursor.execute("UPDATE users SET role = 'admin' WHERE id = 5")

conn.commit()
conn.close()

print("Role for user id=1 updated to manager ✅")
