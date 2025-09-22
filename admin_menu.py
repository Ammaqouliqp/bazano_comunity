# admin_menu.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from auth import sessions
from db import cursor
from logs import add_log

def get_user(tg_id):
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
    user = get_user(update.effective_user.id)
    if not user or user[3] != "admin":
        await target.reply_text("⛔ شما دسترسی ادمین ندارید.")
        return
    kb = [
        [InlineKeyboardButton("📋 مشاهده تراکنش‌ها", callback_data="admin:view_tx")],
        [InlineKeyboardButton("➕ اضافه کردن تراکنش", callback_data="admin:add_tx")],
        [InlineKeyboardButton("📩 پشتیبانی", callback_data="admin:view_support")],
        [InlineKeyboardButton("🗂 پیشنهادات", callback_data="admin:view_suggestions")],
        [InlineKeyboardButton("🔙 بستن", callback_data="admin:close")]
    ]
    await target.reply_text("⚙️ منوی ادمین:", reply_markup=InlineKeyboardMarkup(kb))

async def view_support_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    cursor.execute("SELECT id, user_id, message, date FROM support ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    if not rows:
        await cq.message.reply_text("📭 پیامی نیست.")
        return
    text = "📩 پیام‌های پشتیبانی:\n\n"
    for r in rows:
        text += f"#{r[0]} | user_id={r[1]} | {r[2]} | {r[3]}\n"
    await cq.message.reply_text(text)

async def view_suggestions_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    cursor.execute("SELECT id, user_id, message, date FROM suggestions ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    if not rows:
        await cq.message.reply_text("📭 نظری ثبت نشده.")
        return
    text = "💡 پیشنهادات/انتقادات:\n\n"
    for r in rows:
        text += f"#{r[0]} | user_id={r[1]} | {r[2]} | {r[3]}\n"
    await cq.message.reply_text(text)

async def admin_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except:
            pass

def get_admin_handlers():
    return [
        CommandHandler("admin_menu", admin_menu),
        CallbackQueryHandler(admin_menu, pattern="^admin_menu$"),
        CallbackQueryHandler(view_support_cb, pattern="^admin:view_support$"),
        CallbackQueryHandler(view_suggestions_cb, pattern="^admin:view_suggestions$"),
        CallbackQueryHandler(admin_close, pattern="^admin:close$"),
    ]
