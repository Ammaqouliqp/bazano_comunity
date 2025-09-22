from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

async def manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="manager_products")],
        [InlineKeyboardButton("📊 گزارش‌ها", callback_data="manager_reports")],
        [InlineKeyboardButton("🛒 منوی خریدار", callback_data="go_buyer")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    if update.message:
        await update.message.reply_text("📋 منوی مدیر:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text("📋 منوی مدیر:", reply_markup=InlineKeyboardMarkup(keyboard))

async def manager_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "manager_products":
        await q.edit_message_text("⚙ بخش مدیریت محصولات...")
    elif q.data == "manager_reports":
        await q.edit_message_text("📊 گزارش‌ها...")
    elif q.data == "go_buyer":
        from buyer import buyer_menu
        await buyer_menu(update, context)
    elif q.data == "back_main":
        await q.edit_message_text("🔙 برگشتی به منوی اصلی...")

def get_manager_handlers():
    return [
        CommandHandler("manager", manager_menu),
        CallbackQueryHandler(manager_callback, pattern="^manager_"),
        CallbackQueryHandler(manager_callback, pattern="^go_buyer$"),
        CallbackQueryHandler(manager_callback, pattern="^back_main$"),
    ]
