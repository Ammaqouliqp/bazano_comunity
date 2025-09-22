# manager_menu.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from auth import sessions
from logs import get_logs
from db import cursor

def get_user(tg_id):
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
    user = get_user(update.effective_user.id)
    if not user or user[3] != "manager":
        await target.reply_text("⛔ شما مدیر نیستید.")
        return
    kb = [
        [InlineKeyboardButton("📜 تاریخچه فعالیت‌ها", callback_data="manager:logs")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="manager:users")],
        [InlineKeyboardButton("🔙 بستن", callback_data="manager:close")]
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
        # r: (id, user_id, action, details, date)
        text += f"👤 کاربر {r[1]} | عملیات: {r[2]} | {r[3]} | {r[4]}\n\n"
    await cq.message.reply_text(text)

def get_manager_handlers():
    return [
        CommandHandler("manager_menu", manager_menu),
        CallbackQueryHandler(manager_menu, pattern="^manager_menu$"),
        CallbackQueryHandler(manager_logs_cb, pattern="^manager:logs$"),
    ]
