# menus/main_menu.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import cursor

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("❌ شما هنوز ثبت‌نام نکرده‌اید.")
        return

    role = row[0]

    # هدایت بر اساس نقش
    if role == "seller":
        from seller import seller_menu
        await seller_menu(update, context)
    elif role == "buyer":
        from buyer import buyer_menu
        await buyer_menu(update, context)
    elif role == "manager":
        from manager import manager_menu
        await manager_menu(update, context)
    elif role == "admin":
        from admin import admin_menu
        await admin_menu(update, context)
    elif role == "dev":
        from dev import dev_menu
        await dev_menu(update, context)
    else:
        await update.message.reply_text("⚠️ نقش شما تعریف نشده.")
