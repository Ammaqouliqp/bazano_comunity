# db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("shop.db")
conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
cursor = conn.cursor()

# users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT,
    lastname TEXT,
    phonenumber TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'member'
)
""")

# products
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT,
    name TEXT,
    description TEXT,
    manufacture_date TEXT,
    expire_date TEXT,
    quantity TEXT,
    price_entry REAL,
    price_exit REAL,
    created_by INTEGER,
    created_at TEXT
)
""")

# requests (purchase requests from buyers)
cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    subject TEXT,
    message TEXT,
    date TEXT
)
""")

# transactions
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_code TEXT,
    buyer INTEGER,
    seller INTEGER,
    date TEXT,
    sector TEXT,
    products TEXT,
    buyer_score INTEGER,
    buyer_feedback TEXT
)
""")

# transaction items
cursor.execute("""
CREATE TABLE IF NOT EXISTS transaction_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER,
    name TEXT,
    seller_price REAL,
    buyer_price REAL
)
""")

# feedbacks
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    transaction_id INTEGER,
    message TEXT,
    date TEXT
)
""")

# support
cursor.execute("""
CREATE TABLE IF NOT EXISTS support (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    date TEXT
)
""")

# suggestions
cursor.execute("""
CREATE TABLE IF NOT EXISTS suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    date TEXT
)
""")

# logs
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

def init_db():
    # kept for compatibility: calling this will ensure tables exist
    pass
