import sqlite3

conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

# جدول کاربران
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT,
    lastname TEXT,
    phonenumber TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'buyer'
)
""")
# جدول تراکنش‌ها
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer INTEGER,
    seller INTEGER,
    date TEXT,
    sector TEXT,
    buyer_rating INTEGER,
    buyer_feedback TEXT
)
""")

# جدول محصولات تراکنش
cursor.execute("""
CREATE TABLE IF NOT EXISTS transaction_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER,
    name TEXT,
    seller_price REAL,
    buyer_price REAL
)
""")

# جدول نظرات
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    transaction_id INTEGER,
    message TEXT,
    date TEXT
)
""")

# جدول پشتیبانی
cursor.execute("""
CREATE TABLE IF NOT EXISTS support (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    date TEXT
)
""")

# جدول انتقادات و پیشنهادات
cursor.execute("""
CREATE TABLE IF NOT EXISTS suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    date TEXT
)
""")

conn.commit()
def get_db():
    return conn, cursor