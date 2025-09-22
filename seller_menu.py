from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from auth import sessions
from db import cursor
from logs import add_log
from buyer_menu import buyer_menu


def check_login(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()


async def seller_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = check_login(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ لطفاً ابتدا وارد شوید با /start")
        return

    user_id, role = user
    if role != "seller":
        await update.message.reply_text("⛔ این بخش فقط برای فروشندگان است.")
        return

    add_log(user_id, "menu_open", "seller_menu")

    keyboard = [
        [InlineKeyboardButton("➕ افزودن محصول", callback_data="seller_add_product")],
        [InlineKeyboardButton("📋 محصولات من", callback_data="seller_my_products")],
        [InlineKeyboardButton("🛍 منوی خریدار", callback_data="buyer_menu")],
    ]

    await update.message.reply_text(
        "📦 منوی فروشنده:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


# --- گرفتن هندلرها ---
def get_seller_handlers():
    return [
        CommandHandler("seller_menu", seller_menu),
        # اینجا بعداً CallbackQueryHandlerها برای افزودن/ویرایش محصول اضافه میشه
    ]
