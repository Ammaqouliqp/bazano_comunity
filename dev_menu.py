from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import DEV_ID
from logs import read_logs

async def dev_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DEV_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    keyboard = [
        [InlineKeyboardButton("📜 لاگ‌ها", callback_data="dev_logs")],
        [InlineKeyboardButton("🛒 منوی خریدار", callback_data="go_buyer")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    if update.message:
        await update.message.reply_text("👨‍💻 منوی توسعه‌دهنده:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text("👨‍💻 منوی توسعه‌دهنده:", reply_markup=InlineKeyboardMarkup(keyboard))

async def dev_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "dev_logs":
        logs = read_logs()
        await q.edit_message_text("📜 لاگ‌ها:\n\n" + "\n".join(logs[-10:]))
    elif q.data == "go_buyer":
        from buyer import buyer_menu
        await buyer_menu(update, context)
    elif q.data == "back_main":
        await q.edit_message_text("🔙 برگشتی به منوی اصلی...")

def get_dev_handlers():
    return [
        CommandHandler("dev", dev_menu),
        CallbackQueryHandler(dev_callback, pattern="^dev_"),
        CallbackQueryHandler(dev_callback, pattern="^go_buyer$"),
        CallbackQueryHandler(dev_callback, pattern="^back_main$"),
    ]
