# menus/manager_menu.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from auth import sessions
from logs import get_logs
from db import cursor

def get_user_by_tg(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.message
    user = get_user_by_tg(update.effective_user.id)
    if not user or user[3] != "manager":
        await target.reply_text("⛔ شما مدیر نیستید.")
        return
    kb = [
        [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:manage_products")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="manager:users")],
        [InlineKeyboardButton("📜 تاریخچه فعالیت‌ها", callback_data="manager:logs")],
        [InlineKeyboardButton("📥 درخواست محصول (مشترک)", callback_data="common:request")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="common:back")],
    ]
    await target.reply_text("🧾 منوی مدیریت:", reply_markup=InlineKeyboardMarkup(kb))

async def manager_logs_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    rows = get_logs(50)
    if not rows:
        await cq.message.reply_text("📭 لاگی وجود ندارد.")
        return
    text = "📜 تاریخچه فعالیت‌ها:\n\n"
    for r in rows:
        text += f"👤 کاربر {r[1]} | عملیات: {r[2]} | جزئیات: {r[3]} | ⏰ {r[4]}\n\n"
    await cq.message.reply_text(text)
