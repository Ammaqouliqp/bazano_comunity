from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

async def buyer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 مشاهده محصولات", callback_data="buyer_view")],
        [InlineKeyboardButton("➕ درخواست خرید", callback_data="buyer_request")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    if update.message:
        await update.message.reply_text("👤 منوی خریدار:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text("👤 منوی خریدار:", reply_markup=InlineKeyboardMarkup(keyboard))

async def buyer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "buyer_view":
        await q.edit_message_text("📦 لیست محصولات (نمایشی)...")
    elif q.data == "buyer_request":
        await q.edit_message_text("✍ درخواست خرید ثبت شد.")
    elif q.data == "back_main":
        await q.edit_message_text("🔙 برگشتی به منوی اصلی...")

def get_buyer_handlers():
    return [
        CommandHandler("buyer", buyer_menu),
        CallbackQueryHandler(buyer_callback, pattern="^buyer_"),
        CallbackQueryHandler(buyer_callback, pattern="^back_main$"),
    ]
