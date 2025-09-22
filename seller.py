# seller.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from db import cursor
from auth import sessions
from logs import add_log

def get_user_by_tg(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def seller_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_tg(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ لطفاً ابتدا وارد شوید (/start)")
        return
    kb = [
        [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
        [InlineKeyboardButton("📦 محصولات من", callback_data="seller:my_products")],
        [InlineKeyboardButton("🛍 منوی خریدار", callback_data="buyer:menu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main:menu")],
    ]
    await update.message.reply_text("🏪 منوی فروشنده:", reply_markup=InlineKeyboardMarkup(kb))
    add_log(user[0], "OPEN_MENU", "seller_menu")

async def seller_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user = get_user_by_tg(q.from_user.id)
    if data == "seller:my_products":
        cursor.execute("SELECT id, brand, name, quantity, price_entry FROM products")
        rows = cursor.fetchall()
        if not rows:
            await q.message.reply_text("📭 محصولی ثبت نشده.")
            return
        text = "📦 محصولات:\n"
        for r in rows:
            text += f"#{r[0]} — {r[1]} | {r[2]} | {r[3]} | ورود: {r[4]}\n"
        await q.message.reply_text(text)
    add_log(user[0] if user else None, "SELLER_ACTION", data)

def get_seller_handlers():
    return [
        CommandHandler("seller", seller_menu_cmd),
        CallbackQueryHandler(seller_callback, pattern="^seller:")
    ]
