# admin.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from auth import sessions
from db import cursor
from logs import add_log

def get_user_by_tg(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def admin_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_tg(update.effective_user.id)
    if not user or user[3] != "admin":
        await update.message.reply_text("⛔ شما ادمین نیستید.")
        return
    kb = [
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin:users")],
        [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:products")],
        [InlineKeyboardButton("📜 لاگ‌ها", callback_data="admin:logs")],
        [InlineKeyboardButton("🛍 منوی خریدار", callback_data="buyer:menu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main:menu")],
    ]
    await update.message.reply_text("⚙️ منوی ادمین:", reply_markup=InlineKeyboardMarkup(kb))
    add_log(user[0], "OPEN_MENU", "admin_menu")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = get_user_by_tg(q.from_user.id)
    if q.data == "admin:logs":
        from logs import read_logs
        rows = read_logs(50)
        if not rows:
            await q.message.reply_text("📭 لاگی وجود ندارد.")
            return
        text = "📜 لاگ‌ها:\n\n"
        for r in rows:
            text += f"#{r[0]} | user {r[1]} | {r[2]} | {r[3]} | {r[4]}\n\n"
        await q.message.reply_text(text)
    add_log(user[0] if user else None, "ADMIN_ACTION", q.data)

def get_admin_handlers():
    return [
        CommandHandler("admin", admin_menu_cmd),
        CallbackQueryHandler(admin_callback, pattern="^admin:")
    ]
