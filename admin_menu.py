from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin_products")],
        [InlineKeyboardButton("🛒 منوی خریدار", callback_data="go_buyer")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    if update.message:
        await update.message.reply_text("🛡 منوی ادمین:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text("🛡 منوی ادمین:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "admin_users":
        await q.edit_message_text("👥 بخش مدیریت کاربران...")
    elif q.data == "admin_products":
        await q.edit_message_text("📦 بخش مدیریت محصولات...")
    elif q.data == "go_buyer":
        from buyer import buyer_menu
        await buyer_menu(update, context)
    elif q.data == "back_main":
        await q.edit_message_text("🔙 برگشتی به منوی اصلی...")

def get_admin_handlers():
    return [
        CommandHandler("admin", admin_menu),
        CallbackQueryHandler(admin_callback, pattern="^admin_"),
        CallbackQueryHandler(admin_callback, pattern="^go_buyer$"),
        CallbackQueryHandler(admin_callback, pattern="^back_main$"),
    ]
