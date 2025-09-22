# seller.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from auth import sessions
from db import cursor, conn
from logs import add_log
import csv, os

def get_user(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def seller_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.message
    user = get_user(update.effective_user.id)
    if not user:
        await target.reply_text("⚠️ ابتدا وارد شوید.")
        return
    kb = [
        [InlineKeyboardButton("📦 محصولات من", callback_data="seller:my_products")],
        [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
        [InlineKeyboardButton("🗂 فروش‌های من", callback_data="seller:my_sales")],
        [InlineKeyboardButton("⬇️ خروجی CSV", callback_data="seller:export")],
        [InlineKeyboardButton("🔙 بستن", callback_data="seller:close")]
    ]
    await target.reply_text("🏪 منوی فروشنده:", reply_markup=InlineKeyboardMarkup(kb))

async def my_products_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    user = get_user(cq.from_user.id)
    if not user:
        await cq.message.reply_text("⚠️ ابتدا وارد شوید.")
        return
    uid = user[0]
    cursor.execute("SELECT id, brand, name, quantity, price_entry FROM products WHERE created_by=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        await cq.message.reply_text("📭 هیچ محصولی ثبت نکرده‌اید.")
        return
    text = "📋 محصولات شما:\n\n"
    for r in rows:
        text += f"#{r[0]} | {r[1]} - {r[2]} | مقدار: {r[3]} | قیمت ورود: {r[4]}\n"
    await cq.message.reply_text(text)

async def my_sales_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    user = get_user(cq.from_user.id)
    if not user:
        await cq.message.reply_text("⚠️ ابتدا وارد شوید.")
        return
    uid = user[0]
    cursor.execute("SELECT id, buyer, date, sector FROM transactions WHERE seller=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        await cq.message.reply_text("📭 هیچ فروشی ثبت نشده است.")
        return
    text = "📦 فروش‌های شما:\n\n"
    for r in rows:
        text += f"#{r[0]} | خریدار: {r[1]} | تاریخ: {r[2]} | صنف: {r[3]}\n"
    await cq.message.reply_text(text)

async def export_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    user = get_user(cq.from_user.id)
    if not user:
        await cq.message.reply_text("⚠️ ابتدا وارد شوید.")
        return
    uid = user[0]
    cursor.execute("SELECT id, buyer, date, sector FROM transactions WHERE seller=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        await cq.message.reply_text("📭 هیچ فروشی برای خروجی وجود ندارد.")
        return
    filename = f"seller_{uid}_sales.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["TransactionID", "BuyerID", "Date", "Sector"])
        w.writerows(rows)
    await cq.message.reply_document(open(filename, "rb"))
    try:
        os.remove(filename)
    except:
        pass
    add_log(uid, "EXPORT_SALES", f"rows={len(rows)}")

async def seller_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except:
            pass

def get_seller_handlers():
    return [
        CommandHandler("seller_menu", seller_menu),
        CallbackQueryHandler(seller_menu, pattern="^seller_menu$"),
        CallbackQueryHandler(my_products_cb, pattern="^seller:my_products$"),
        CallbackQueryHandler(my_sales_cb, pattern="^seller:my_sales$"),
        CallbackQueryHandler(export_cb, pattern="^seller:export$"),
        CallbackQueryHandler(seller_close, pattern="^seller:close$"),
    ]
