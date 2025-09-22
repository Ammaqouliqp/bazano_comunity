from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db import cursor
from logs import log_event
from auth import sessions

# -----------------------
# چک نقش
def check_role(tg_id, required_role):
    phone = sessions.get(tg_id)
    if not phone:
        return None, "⚠️ اول باید لاگین کنید (/start)"
    cursor.execute("SELECT id, role FROM users WHERE phonenumber=?", (phone,))
    user = cursor.fetchone()
    if not user:
        return None, "⚠️ کاربر یافت نشد."
    if user[1] != required_role:
        return None, "⛔ شما دسترسی لازم را ندارید."
    return user, None

# -----------------------
# منوی ادمین
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_role(update.effective_user.id, "admin")
    if err:
        await update.message.reply_text(err)
        return

    log_event(user[0], "menu_open", "admin_menu")

    await update.message.reply_text(
        "⚙️ منوی ادمین:\n\n"
        "۱️⃣ /view_transactions – مشاهده تراکنش‌ها\n"
        "۲️⃣ /add_transaction – اضافه کردن تراکنش\n"
        "۳️⃣ /feedbacks – مشاهده انتقادات و پیشنهادات"
    )

# -----------------------
# مشاهده تراکنش‌ها
async def view_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_role(update.effective_user.id, "admin")
    if err:
        await update.message.reply_text(err)
        return

    cursor.execute("SELECT id, buyer, seller, date FROM transactions LIMIT 10")
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("📭 هیچ تراکنشی ثبت نشده است.")
        return

    text = "📊 آخرین تراکنش‌ها:\n\n"
    for row in rows:
        text += f"شماره: {row[0]} | خریدار: {row[1]} | فروشنده: {row[2]} | تاریخ: {row[3]}\n"
    await update.message.reply_text(text)

# -----------------------
# اضافه کردن تراکنش (نسخه ساده - بعداً کامل می‌کنیم)
async def add_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_role(update.effective_user.id, "admin")
    if err:
        await update.message.reply_text(err)
        return

    await update.message.reply_text("➕ اضافه کردن تراکنش به زودی اینجا پیاده میشه.")

# -----------------------
# مشاهده انتقادات و پیشنهادات
async def feedbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_role(update.effective_user.id, "admin")
    if err:
        await update.message.reply_text(err)
        return

    cursor.execute("SELECT id, user_id, message, date FROM feedbacks ORDER BY date DESC LIMIT 10")
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("📭 هیچ نظری ثبت نشده است.")
        return

    text = "📬 آخرین نظرات:\n\n"
    for row in rows:
        text += f"شماره: {row[0]} | کاربر: {row[1]} | متن: {row[2]} | تاریخ: {row[3]}\n"
    await update.message.reply_text(text)

# -----------------------
# گرفتن هندلرها
def get_admin_handlers():
    return [
        CommandHandler("admin_menu", admin_menu),
        CommandHandler("view_transactions", view_transactions),
        CommandHandler("add_transaction", add_transaction),
        CommandHandler("feedbacks", feedbacks),
    ]
