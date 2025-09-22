# utils.py
import hashlib
from datetime import datetime

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
