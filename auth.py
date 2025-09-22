from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from db import cursor, conn
from utils import hash_password
from logs import log_event

# ----- ثبت‌نام -----
ASK_CODE, ASK_PHONE, ASK_LOGIN_PASS, ASK_FIRSTNAME, ASK_LASTNAME, ASK_REGISTER_PASS = range(6)
REGISTER_CODE = "Havayekhoobarodarim"

# جلسات فعال (telegram_id -> phone)
sessions = {}

# ------------------------
# شروع /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔑 لطفاً کد ثبت‌نام را وارد کنید:")
    return ASK_CODE

async def ask_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == REGISTER_CODE:
        await update.message.reply_text("📱 لطفاً شماره تلفن خود را وارد کنید (مثال: +994501234567):")
        return ASK_PHONE
    else:
        await update.message.reply_text("❌ کد معتبر نیست. با /start دوباره تلاش کنید.")
        return ConversationHandler.END

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["phone"] = phone

    cursor.execute("SELECT id, password, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    user = cursor.fetchone()

    if user:
        await update.message.reply_text("🔒 شماره یافت شد. لطفاً رمز عبور را وارد کنید:")
        return ASK_LOGIN_PASS
    else:
        await update.message.reply_text("🆕 شماره یافت نشد. لطفاً نام خود را وارد کنید:")
        return ASK_FIRSTNAME

async def ask_login_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data["phone"]
    cursor.execute("SELECT id, password, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    user = cursor.fetchone()

    if user and user[1] == hash_password(update.message.text.strip()):
        sessions[update.effective_user.id] = phone
        log_event(user[0], "login", f"telegram_id={update.effective_user.id}")
        await update.message.reply_text(f"✅ ورود موفق\n👤 خوش آمدید، {user[2]} {user[3]} | نقش: {user[4]}")
    else:
        await update.message.reply_text("❌ رمز اشتباه است. دوباره /start بزنید.")
    return ConversationHandler.END

async def ask_firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["firstname"] = update.message.text.strip()
    await update.message.reply_text("✍️ لطفاً نام خانوادگی خود را وارد کنید:")
    return ASK_LASTNAME

async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lastname"] = update.message.text.strip()
    await update.message.reply_text("🔒 لطفاً یک رمز عبور انتخاب کنید:")
    return ASK_REGISTER_PASS

async def ask_register_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data["phone"]
    firstname = context.user_data["firstname"]
    lastname = context.user_data["lastname"]
    password = hash_password(update.message.text.strip())

    cursor.execute(
        "INSERT INTO users (firstname, lastname, phonenumber, password, role) VALUES (?, ?, ?, ?, ?)",
        (firstname, lastname, phone, password, "member"),
    )
    conn.commit()
    user_id = cursor.lastrowid
    sessions[update.effective_user.id] = phone
    log_event(user_id, "signup", f"telegram_id={update.effective_user.id}")

    await update.message.reply_text(f"✅ ثبت‌نام موفق!\n👤 {firstname} {lastname}\n📱 {phone}\n🔑 نقش: member")
    return ConversationHandler.END

# ------------------------
# پروفایل
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    phone = sessions.get(tg_id)
    if not phone:
        await update.message.reply_text("⚠️ شما وارد نشده‌اید. اول /start بزنید.")
        return

    cursor.execute("SELECT firstname, lastname, phonenumber, role FROM users WHERE phonenumber=?", (phone,))
    user = cursor.fetchone()
    if not user:
        await update.message.reply_text("⚠️ کاربر در دیتابیس یافت نشد.")
        return

    await update.message.reply_text(
        f"👤 پروفایل:\n\n"
        f"نام: {user[0]}\n"
        f"نام خانوادگی: {user[1]}\n"
        f"شماره: {user[2]}\n"
        f"نقش: {user[3]}"
    )

# ------------------------
# خروج
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    if tg_id in sessions:
        phone = sessions.pop(tg_id)
        cursor.execute("SELECT id FROM users WHERE phonenumber=?", (phone,))
        user = cursor.fetchone()
        if user:
            log_event(user[0], "logout", f"telegram_id={tg_id}")
        await update.message.reply_text("🚪 خروج موفق.")
    else:
        await update.message.reply_text("⚠️ شما وارد نشده‌اید.")

# ------------------------
# راهنما
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 راهنمای دستورات:\n\n"
        "/start – ورود یا ثبت‌نام\n"
        "/profile – نمایش اطلاعات کاربری\n"
        "/logout – خروج از حساب\n"
        "/help – نمایش این راهنما"
    )

# ------------------------
# کنسل
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ------------------------
# برگرداندن هندلرها
def get_auth_handlers():
    return [
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                ASK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_code)],
                ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
                ASK_LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_login_pass)],
                ASK_FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_firstname)],
                ASK_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_lastname)],
                ASK_REGISTER_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_register_pass)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        ),
        CommandHandler("profile", profile),
        CommandHandler("logout", logout),
        CommandHandler("help", help_command),
    ]
