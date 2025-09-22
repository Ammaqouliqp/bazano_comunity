from telegram import Update, InputFile
from telegram.ext import CommandHandler, ContextTypes
from db import cursor, conn
from logs import log_event
from auth import sessions
import csv
import os
import datetime

# -----------------------
# چک ورود کاربر
def check_login(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None, "⚠️ اول باید لاگین کنید (/start)"
    cursor.execute("SELECT id, firstname, lastname FROM users WHERE phonenumber=?", (phone,))
    user = cursor.fetchone()
    if not user:
        return None, "⚠️ کاربر یافت نشد."
    return user, None

# -----------------------
# منوی فروشنده
async def seller_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return

    log_event(user[0], "menu_open", "seller_menu")

    await update.message.reply_text(
        "📦 منوی فروشنده:\n\n"
        "۱️⃣ /my_sales – مشاهده فروش‌های من\n"
        "۲️⃣ /export_sales – دریافت فایل خروجی فروش‌ها"
    )

# -----------------------
# نمایش فروش‌های من
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return

    seller_id = user[0]
    cursor.execute("SELECT id, buyer, date, sector FROM transactions WHERE seller=?", (seller_id,))
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("📭 هیچ فروشی برای شما ثبت نشده است.")
        return

    text = "📋 فروش‌های شما:\n\n"
    for row in rows:
        text += f"شماره: {row[0]} | خریدار: {row[1]} | تاریخ: {row[2]} | صنف: {row[3]}\n"
    await update.message.reply_text(text)

# -----------------------
# خروجی CSV از فروش‌ها
async def export_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return

    seller_id = user[0]
    cursor.execute("SELECT id, buyer, date, sector FROM transactions WHERE seller=?", (seller_id,))
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("📭 هیچ فروشی برای شما ثبت نشده است.")
        return

    # ایجاد فایل CSV
    filename = f"sales_{seller_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["TransactionID", "BuyerID", "Date", "Sector"])
        writer.writerows(rows)

    # ارسال فایل به کاربر
    with open(filename, "rb") as f:
        await update.message.reply_document(InputFile(f, filename=filename))

    # حذف فایل موقت
    os.remove(filename)

    log_event(seller_id, "export_sales", f"rows={len(rows)}")

# -----------------------
# گرفتن هندلرها
def get_seller_handlers():
    return [
        CommandHandler("seller_menu", seller_menu),
        CommandHandler("my_sales", my_sales),
        CommandHandler("export_sales", export_sales),
    ]
