from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import cursor, conn
from utils import hash_password
from logs import add_log

ASK_FIRSTNAME, ASK_LASTNAME, ASK_PHONE, ASK_PASS = range(4)
ASK_LOGIN_PHONE, ASK_LOGIN_PASS = range(4, 6)


# ----- شروع -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ثبت‌نام", callback_data="register")],
        [InlineKeyboardButton("ورود", callback_data="login")]
    ]
    await update.message.reply_text(
        "به ربات فروشگاه خوش آمدید 🙌\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ----- انتخاب ثبت‌نام -----
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✍️ لطفاً نام خود را وارد کنید:")
    return ASK_FIRSTNAME


async def ask_firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["firstname"] = update.message.text.strip()
    await update.message.reply_text("✍️ حالا نام خانوادگی خود را وارد کنید:")
    return ASK_LASTNAME


async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lastname"] = update.message.text.strip()
    await update.message.reply_text("📱 شماره موبایل خود را وارد کنید:")
    return ASK_PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("🔒 یک رمز عبور انتخاب کنید:")
    return ASK_PASS


async def ask_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    firstname = context.user_data["firstname"]
    lastname = context.user_data["lastname"]
    phone = context.user_data["phone"]
    password = hash_password(update.message.text.strip())

    cursor.execute(
        "INSERT INTO users (firstname, lastname, phonenumber, password) VALUES (?, ?, ?, ?)",
        (firstname, lastname, phone, password)
    )
    conn.commit()
    user_id = cursor.lastrowid
    add_log(user_id, "REGISTER", f"{firstname} {lastname}")

    await update.message.reply_text(f"✅ ثبت‌نام موفق!\n👤 {firstname} {lastname}")
    return ConversationHandler.END


# ----- انتخاب ورود -----
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📱 لطفاً شماره موبایل خود را وارد کنید:")
    return ASK_LOGIN_PHONE


async def ask_login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("🔒 لطفاً رمز عبور خود را وارد کنید:")
    return ASK_LOGIN_PASS


async def ask_login_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data["phone"]
    password = hash_password(update.message.text.strip())

    cursor.execute("SELECT id, firstname, lastname FROM users WHERE phonenumber=? AND password=?", (phone, password))
    user = cursor.fetchone()

    if user:
        await update.message.reply_text(f"✅ ورود موفق!\n👤 خوش آمدید {user[1]} {user[2]}")
        add_log(user[0], "LOGIN", phone)
    else:
        await update.message.reply_text("❌ شماره یا رمز اشتباه است.")
    return ConversationHandler.END
