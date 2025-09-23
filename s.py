import sqlite3

conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

cursor.execute("UPDATE users SET phonenumber = +989354211055 WHERE id = 2")

conn.commit()
conn.close()

print("Role for user id=3 updated  admin✅")
