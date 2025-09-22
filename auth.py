# auth.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, ContextTypes, filters
)
from db import cursor, conn
from utils import hash_password, now
from logs import add_log
from config import REGISTER_CODE

# States
(
    REG_FIRST, REG_LAST, REG_PHONE, REG_PASS,
    LOGIN_PHONE, LOGIN_PASS
) = range(6)

# sessions: telegram_id -> phonenumber
sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("ثبت‌نام", callback_data="auth_register")],
        [InlineKeyboardButton("ورود", callback_data="auth_login")]
    ]
    await update.message.reply_text("🔸 به ربات BazaarNo خوش آمدید!\nلطفاً یک گزینه انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

# register flow
async def auth_register_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("✍️ ثبت‌نام — لطفاً نام خود را وارد کنید:")
    return REG_FIRST

async def reg_first(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["firstname"] = update.message.text.strip()
    await update.message.reply_text("✍️ نام خانوادگی را وارد کنید:")
    return REG_LAST

async def reg_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lastname"] = update.message.text.strip()
    await update.message.reply_text("📱 شماره تلفن (مثال: +994501234567) را وارد کنید:")
    return REG_PHONE

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["phone"] = phone
    await update.message.reply_text("🔒 یک رمز عبور انتخاب کنید:")
    return REG_PASS

async def reg_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    firstname = context.user_data.get("firstname")
    lastname = context.user_data.get("lastname")
    phone = context.user_data.get("phone")
    pwd = hash_password(update.message.text.strip())

    try:
        cursor.execute("INSERT INTO users (firstname, lastname, phonenumber, password, role) VALUES (?, ?, ?, ?, ?)",
                       (firstname, lastname, phone, pwd, "member"))
        conn.commit()
        user_id = cursor.lastrowid
        add_log(user_id, "REGISTER", f"{firstname} {lastname}")
        sessions[update.effective_user.id] = phone
        await update.message.reply_text("✅ ثبت‌نام با موفقیت انجام شد.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await update.message.reply_text("❌ خطا در ثبت‌نام — احتمالاً شماره تکراری است.")
        add_log(None, "ERROR", f"register_error: {e}")
    return ConversationHandler.END

# login flow
async def auth_login_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("📱 لطفاً شماره تلفن خود را وارد کنید:")
    return LOGIN_PHONE

async def login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("🔒 رمز عبور را وارد کنید:")
    return LOGIN_PASS

async def login_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data.get("phone")
    pwd = hash_password(update.message.text.strip())
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=? AND password=?", (phone, pwd))
    user = cursor.fetchone()
    if user:
        sessions[update.effective_user.id] = phone
        add_log(user[0], "LOGIN", f"telegram={update.effective_user.id}")
        await update.message.reply_text(f"✅ ورود موفق. خوش آمدید {user[1]} {user[2]}", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("❌ شماره یا رمز اشتباه است.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# profile / logout / help
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user.id
    phone = sessions.get(tg)
    if not phone:
        await update.message.reply_text("⚠️ شما وارد نشده‌اید. /start")
        return
    cursor.execute("SELECT firstname, lastname, phonenumber, role FROM users WHERE phonenumber=?", (phone,))
    u = cursor.fetchone()
    if not u:
        await update.message.reply_text("⚠️ کاربر یافت نشد.")
        return
    await update.message.reply_text(f"👤 {u[0]} {u[1]}\n📱 {u[2]}\n🔰 نقش: {u[3]}")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user.id
    if tg in sessions:
        phone = sessions.pop(tg)
        cursor.execute("SELECT id FROM users WHERE phonenumber=?", (phone,))
        u = cursor.fetchone()
        if u:
            add_log(u[0], "LOGOUT", f"telegram={tg}")
        await update.message.reply_text("🚪 شما خارج شدید.")
    else:
        await update.message.reply_text("⚠️ شما وارد نشده اید.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user.id
    phone = sessions.get(tg)
    role = None
    if phone:
        cursor.execute("SELECT role FROM users WHERE phonenumber=?", (phone,))
        r = cursor.fetchone()
        role = r[0] if r else None

    # simple static help for now; later will be dynamic per role
    base = "📖 راهنما:\n/start – منوی اصلی\n/profile – پروفایل\n/logout – خروج\n"
    if role == "admin":
        base += "/admin_menu – منوی ادمین\n"
    if role == "manager":
        base += "/manager_menu – منوی مدیریت\n"
    base += "/products_menu – منوی محصولات\n"
    await update.message.reply_text(base)

def get_auth_handlers():
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(auth_register_cb, pattern="^auth_register$"),
            CallbackQueryHandler(auth_login_cb, pattern="^auth_login$"),
        ],
        states={
            REG_FIRST: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_first)],
            REG_LAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_last)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_pass)],
            LOGIN_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_phone)],
            LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_pass)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: c.user_data.clear())],
        allow_reentry=True
    )

    handlers = [
        conv,
        CommandHandler("profile", profile),
        CommandHandler("logout", logout),
        CommandHandler("help", help_cmd),
    ]
    return handlers
