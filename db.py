import sqlite3

conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

# کاربران
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

# محصولات
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT,
    name TEXT,
    description TEXT,
    manufacture_date TEXT,
    expire_date TEXT,
    quantity REAL,
    price_entry REAL,
    price_exit REAL,
    created_by INTEGER
)
""")

# تراکنش‌ها
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

# آیتم‌های تراکنش
cursor.execute("""
CREATE TABLE IF NOT EXISTS transaction_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER,
    name TEXT,
    seller_price REAL,
    buyer_price REAL
)
""")

# لاگ‌ها
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    details TEXT,
    date TEXT
)
""")

conn.commit()
