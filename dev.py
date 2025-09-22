# dev.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from config import DEV_ID
from logs import read_logs, add_log

async def dev_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != DEV_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    kb = [
        [InlineKeyboardButton("📜 لاگ‌ها", callback_data="dev:logs")],
        [InlineKeyboardButton("♻️ reload (dev)", callback_data="dev:reload")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main:menu")],
    ]
    await update.message.reply_text("👨‍💻 منوی توسعه‌دهنده:", reply_markup=InlineKeyboardMarkup(kb))

async def dev_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid != DEV_ID:
        await q.message.reply_text("⛔ دسترسی ندارید.")
        return
    if q.data == "dev:logs":
        rows = read_logs(100)
        text = "📜 Dev Logs:\n\n" + "\n".join([f"#{r[0]}|u{r[1]} {r[2]} {r[3]} {r[4]}" for r in rows[:50]])
        await q.message.reply_text(text)
    elif q.data == "dev:reload":
        await q.message.reply_text("♻️ Reload requested (no-op here).")
        add_log(uid, "DEV_RELOAD", "requested")

def get_dev_handlers():
    return [
        CommandHandler("dev", dev_menu_cmd),
        CallbackQueryHandler(dev_callback, pattern="^dev:")
    ]
