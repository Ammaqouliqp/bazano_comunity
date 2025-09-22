# buyer.py
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

async def buyer_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_tg(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ لطفاً ابتدا وارد شوید (/start)")
        return
    kb = [
        [InlineKeyboardButton("🛒 خریدهای من", callback_data="buyer:my_purchases")],
        [InlineKeyboardButton("📝 درخواست/نظر", callback_data="buyer:request")],
        [InlineKeyboardButton("📩 پشتیبانی", callback_data="buyer:support")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main:menu")],
    ]
    await update.message.reply_text("🛍 منوی خریدار:", reply_markup=InlineKeyboardMarkup(kb))
    add_log(user[0], "OPEN_MENU", "buyer_menu")

async def buyer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user = get_user_by_tg(q.from_user.id)
    if data == "buyer:my_purchases":
        cursor.execute("SELECT id, seller, date, sector FROM transactions WHERE buyer=?", (user[0],))
        rows = cursor.fetchall()
        if not rows:
            await q.message.reply_text("📭 شما هیچ خریدی انجام نداده‌اید.")
            return
        text = "🛒 خریدهای شما:\n\n"
        for r in rows:
            text += f"#{r[0]} | فروشنده: {r[1]} | تاریخ: {r[2]} | صنف: {r[3]}\n"
        await q.message.reply_text(text)
    elif data == "buyer:request":
        # will be handled by requests conv
        await q.message.reply_text("برای ثبت درخواست از دکمه استفاده کنید.")
    elif data == "buyer:support":
        await q.message.reply_text("📩 پیام شما به پشتیبانی ثبت خواهد شد.")
    add_log(user[0] if user else None, "BUYER_ACTION", data)

def get_buyer_handlers():
    return [
        CommandHandler("buyer", buyer_menu_cmd),
        CallbackQueryHandler(buyer_callback, pattern="^buyer:")
    ]
