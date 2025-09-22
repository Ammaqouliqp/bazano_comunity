# menus/admin_menu.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from auth import sessions
from db import cursor
from logs import add_log

def get_user_by_tg(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.message
    user = get_user_by_tg(update.effective_user.id)
    if not user or user[3] != "admin":
        await target.reply_text("⛔ شما ادمین نیستید.")
        return
    kb = [
        [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:manage_products")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin:users")],
        [InlineKeyboardButton("📜 لاگ‌ها", callback_data="admin:logs")],
        [InlineKeyboardButton("📥 درخواست محصول (مشترک)", callback_data="common:request")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="common:back")],
    ]
    await target.reply_text("⚙️ منوی ادمین:", reply_markup=InlineKeyboardMarkup(kb))

async def admin_view_support_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    cursor.execute("SELECT id, user_id, message, date FROM support ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    if not rows:
        await cq.message.reply_text("📭 پیامی وجود ندارد.")
        return
    text = "📩 پیام‌های پشتیبانی:\n\n"
    for r in rows:
        text += f"#{r[0]} | user {r[1]} | {r[2]} | {r[3]}\n"
    await cq.message.reply_text(text)
