# transactions.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from db import cursor, conn
from logs import add_log
from auth import sessions
import json

def get_user(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def view_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ ابتدا وارد شوید.")
        return
    cursor.execute("SELECT id, transaction_code, buyer, seller, date FROM transactions ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("📭 تراکنشی موجود نیست.")
        return
    text = "📊 تراکنش‌ها:\n\n"
    for r in rows:
        text += f"#{r[0]} | code:{r[1]} | buyer:{r[2]} | seller:{r[3]} | {r[4]}\n"
    await update.message.reply_text(text)

def get_transaction_handlers():
    return [
        CommandHandler("view_transactions", view_transactions),
    ]
