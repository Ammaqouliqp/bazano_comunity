from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db import cursor
from logs import log_event
from auth import sessions

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
# منوی مدیر
async def manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_role(update.effective_user.id, "manager")
    if err:
        await update.message.reply_text(err)
        return

    log_event(user[0], "menu_open", "manager_menu")

    await update.message.reply_text(
        "📂 منوی مدیریت:\n\n"
        "۱️⃣ /manage_transactions – مدیریت تراکنش‌ها\n"
        "۲️⃣ /manage_users – مدیریت کاربران\n"
    )

# -----------------------
# مدیریت تراکنش‌ها
async def manage_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_role(update.effective_user.id, "manager")
    if err:
        await update.message.reply_text(err)
        return

    await update.message.reply_text("📊 اینجا می‌تونید تراکنش‌ها رو ببینید و مدیریت کنید (به زودی).")

# -----------------------
# مدیریت کاربران
async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_role(update.effective_user.id, "manager")
    if err:
        await update.message.reply_text(err)
        return

    await update.message.reply_text("👥 اینجا می‌تونید کاربران رو مدیریت کنید (به زودی).")

# -----------------------
# گرفتن هندلرها
def get_manager_handlers():
    return [
        CommandHandler("manager_menu", manager_menu),
        CommandHandler("manage_transactions", manage_transactions),
        CommandHandler("manage_users", manage_users),
    ]
