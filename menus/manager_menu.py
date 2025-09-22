from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from logs import get_logs

async def manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📜 تاریخچه فعالیت‌ها", callback_data="manager_logs")]
    ]
    await update.message.reply_text("مدیریت 👨‍💼", reply_markup=InlineKeyboardMarkup(keyboard))

async def manager_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "manager_logs":
        logs = get_logs()
        text = "\n\n".join([f"👤 کاربر {u}\nعملیات: {a}\nجزئیات: {d}\n⏰ {t}" for u, a, d, t in logs])
        await query.edit_message_text(f"📜 تاریخچه:\n{text}")
