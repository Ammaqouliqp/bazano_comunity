from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from logs import get_logs, get_errors
from config import DEV_ID

async def dev_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DEV_ID:
        return

    keyboard = [
        [InlineKeyboardButton("📜 لاگ‌ها", callback_data="dev_logs")],
        [InlineKeyboardButton("⚠️ خطاها", callback_data="dev_errors")],
        [InlineKeyboardButton("♻️ ری‌لود", callback_data="dev_reload")]
    ]
    await update.message.reply_text("منوی توسعه‌دهنده 👨‍💻", reply_markup=InlineKeyboardMarkup(keyboard))

async def dev_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "dev_logs":
        logs = get_logs()
        text = "\n".join([f"👤 {u} | {a} | {d} | {t}" for u, a, d, t in logs])
        await query.edit_message_text(f"📜 آخرین لاگ‌ها:\n{text}")
    elif query.data == "dev_errors":
        errs = get_errors()
        text = "\n".join([f"❌ {d} | {t}" for u, a, d, t in errs])
        await query.edit_message_text(f"⚠️ خطاها:\n{text}")
    elif query.data == "dev_reload":
        await query.edit_message_text("♻️ ماژول‌ها ری‌لود شدند (نمونه).")
