from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

async def seller_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ افزودن محصول", callback_data="seller_add")],
        [InlineKeyboardButton("📦 محصولات من", callback_data="seller_list")],
        [InlineKeyboardButton("🛒 منوی خریدار", callback_data="go_buyer")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    if update.message:
        await update.message.reply_text("🏪 منوی فروشنده:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text("🏪 منوی فروشنده:", reply_markup=InlineKeyboardMarkup(keyboard))

async def seller_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "seller_add":
        await q.edit_message_text("✍ افزودن محصول جدید...")
    elif q.data == "seller_list":
        await q.edit_message_text("📦 لیست محصولات شما...")
    elif q.data == "go_buyer":
        from buyer import buyer_menu
        await buyer_menu(update, context)
    elif q.data == "back_main":
        await q.edit_message_text("🔙 برگشتی به منوی اصلی...")

def get_seller_handlers():
    return [
        CommandHandler("seller", seller_menu),
        CallbackQueryHandler(seller_callback, pattern="^seller_"),
        CallbackQueryHandler(seller_callback, pattern="^go_buyer$"),
        CallbackQueryHandler(seller_callback, pattern="^back_main$"),
    ]
