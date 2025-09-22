# reports.py
from db import cursor
import csv
from logs import add_log

def export_products_csv(user_id, filename="products_export.csv"):
    cursor.execute("SELECT id, brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit FROM products")
    rows = cursor.fetchall()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","brand","name","description","manufacture_date","expire_date","quantity","price_entry","price_exit"])
        w.writerows(rows)
    add_log(user_id, "EXPORT_PRODUCTS", f"rows={len(rows)}")
    return filename
