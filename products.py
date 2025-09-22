# products.py
from db import cursor, conn
from logs import add_log
from utils import now

# -------------------------
# افزودن محصول
def add_product(user_id, role, brand, name, description, m_date, e_date, qty, price_entry, price_exit=None):
    # seller نمی‌تونه price_exit بده
    if role == "seller":
        price_exit = None

    cursor.execute("""
    INSERT INTO products 
    (brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (brand, name, description, m_date, e_date, qty, price_entry, price_exit, user_id))
    conn.commit()
    add_log(user_id, "ADD_PRODUCT", f"{name}")
    return True

# -------------------------
# گرفتن لیست محصولات
def get_products(role):
    if role in ("admin", "manager"):
        cursor.execute("SELECT id, brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit FROM products")
    else:  # buyer, seller
        cursor.execute("SELECT id, brand, name, description, manufacture_date, expire_date, quantity, price_entry FROM products")
    return cursor.fetchall()

# -------------------------
# ویرایش محصول
def edit_product(user_id, role, product_id, **kwargs):
    # فقط مقادیر داده‌شده آپدیت می‌شن
    fields, values = [], []
    for key, val in kwargs.items():
        if role == "seller" and key == "price_exit":
            continue  # seller حق ویرایش price_exit نداره
        fields.append(f"{key}=?")
        values.append(val)

    if not fields:
        return False

    values.append(product_id)
    sql = f"UPDATE products SET {', '.join(fields)} WHERE id=?"
    cursor.execute(sql, values)
    conn.commit()
    add_log(user_id, "EDIT_PRODUCT", f"id={product_id}")
    return True

# -------------------------
# حذف محصول
def delete_product(user_id, product_id):
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    add_log(user_id, "DELETE_PRODUCT", f"id={product_id}")
    return True
