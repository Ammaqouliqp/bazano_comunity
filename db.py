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
    role TEXT DEFAULT 'buyer'
)
""")

# products (exactly 8 fields as requested)
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
    price_exit REAL
)
""")

# purchase requests (available to everyone)
cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    subject TEXT,
    message TEXT,
    date TEXT
)
""")

# transactions (skeleton)
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_code TEXT,
    buyer INTEGER,
    seller INTEGER,
    date TEXT,
    sector TEXT,
    products TEXT
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
    # placeholder in case we want to call explicitly
    pass
