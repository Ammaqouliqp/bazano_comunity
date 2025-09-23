# auth.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, CommandHandler, ConversationHandler,
    MessageHandler, filters
)
from db import cursor, conn
from utils import hash_password
from logs import add_log
from config import REGISTER_CODE

# Conversation states
(REG_CODE, REG_PHONE, REG_FIRST, REG_LAST, REG_PASS, LOGIN_PHONE, LOGIN_PASS) = range(7)

# sessions: telegram_id -> phonenumber
sessions = {}

# ------------------- Helpers -------------------

def normalize_phone(phone: str) -> str | None:
    """Normalize Iranian phone numbers to +98 format."""
    phone = phone.strip()
    if phone.startswith("+98") and phone[3:].isdigit() and len(phone) == 13:
        return phone
    elif phone.startswith("0") and phone[1:].isdigit() and len(phone) == 11:
        return "+98" + phone[1:]
    else:
        return None

# ------------------- Start & Menu -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📥 ثبت‌نام", callback_data="auth_register")],
        [InlineKeyboardButton("🔐 ورود", callback_data="auth_login")],
        [InlineKeyboardButton("📖 راهنما", callback_data="auth_help")],
    ]
    await update.message.reply_text(
        "🔸 به بازانــو خوش آمدید!\nیک گزینه انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "auth_register":
        await q.message.reply_text("🔑 لطفاً کد ثبت‌نام را وارد کنید:")
        return REG_CODE
    if q.data == "auth_login":
        await q.message.reply_text("📱 لطفاً شماره تلفن خود را وارد کنید:")
        return LOGIN_PHONE
    if q.data == "auth_help":
        text = (
            "📱 راهنمای ورود و ثبت‌نام:\n\n"
            "— ورود —\n"
            "• شماره تلفن خود را وارد کنید (با 0 یا +98)\n"
            "• سپس رمز عبور خود را وارد نمایید\n\n"
            "— ثبت‌نام —\n"
            "• کد را از کانال بازانو دریافت کنید\n"
            "• شماره تلفن خود را وارد کنید (با 0 یا +98)\n"
            "• نام، نام خانوادگی و رمز عبور خود را وارد کنید\n"
        )
        await q.message.reply_text(text)
        return ConversationHandler.END
    return ConversationHandler.END

# ------------------- Register flow -------------------

async def reg_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if code != REGISTER_CODE:
        await update.message.reply_text("❌ کد اشتباه است. دوباره وارد کنید:")
        return REG_CODE
    await update.message.reply_text("📱 شماره تلفن خود را وارد کنید (مثال: 09121234567):")
    return REG_PHONE

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = normalize_phone(update.message.text.strip())
    if not phone:
        await update.message.reply_text("❌ شماره تلفن نامعتبر است. دوباره وارد کنید (مثال: 09121234567):")
        return REG_PHONE

    cursor.execute("SELECT id FROM users WHERE phonenumber=?", (phone,))
    existing = cursor.fetchone()
    if existing:
        kb = [
            [InlineKeyboardButton("🔁 ثبت شماره جدید", callback_data="auth_register")],
            [InlineKeyboardButton("🔐 ورود با همین شماره", callback_data="auth_login")],
        ]
        await update.message.reply_text(
            "⚠️ این شماره قبلاً ثبت شده است. یکی از گزینه‌ها را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return ConversationHandler.END

    context.user_data["phone"] = phone
    await update.message.reply_text("✍️ نام خود را وارد کنید:")
    return REG_FIRST

async def reg_first(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["firstname"] = update.message.text.strip()
    await update.message.reply_text("✍️ نام خانوادگی خود را وارد کنید:")
    return REG_LAST

async def reg_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lastname"] = update.message.text.strip()
    await update.message.reply_text("🔒 یک رمز عبور انتخاب کنید:")
    return REG_PASS

async def reg_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    phone = context.user_data["phone"]
    firstname = context.user_data["firstname"]
    lastname = context.user_data["lastname"]

    try:
        cursor.execute(
            "INSERT INTO users (firstname, lastname, phonenumber, password, role) VALUES (?, ?, ?, ?, ?)",
            (firstname, lastname, phone, hash_password(password), "buyer")
        )
        conn.commit()
        user_id = cursor.lastrowid
        sessions[update.effective_user.id] = phone
        add_log(user_id, "REGISTER", f"telegram={update.effective_user.id}")
        await update.message.reply_text(f"✅ ثبت‌نام موفق! خوش آمدید {firstname} {lastname}")
        await send_role_menu(update, context, phone)
    except Exception as e:
        await update.message.reply_text("❌ خطا در ثبت‌نام — احتمالاً شماره تکراری است.")
        add_log(None, "ERROR", f"register_error: {e}")
    return ConversationHandler.END

# ------------------- Login flow -------------------

async def login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = normalize_phone(update.message.text.strip())
    if not phone:
        await update.message.reply_text("❌ شماره تلفن نامعتبر است. دوباره وارد کنید (مثال: 09121234567):")
        return LOGIN_PHONE
    context.user_data["phone"] = phone
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
        await update.message.reply_text(f"✅ ورود موفق. به بازانـو خوش آمدید {user[1]} {user[2]}")
        await send_role_menu(update, context, phone)
    else:
        await update.message.reply_text("❌ شماره یا رمز اشتباه است.")
    return ConversationHandler.END

# ------------------- Role Menu -------------------

async def send_role_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str):
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    row = cursor.fetchone()
    if not row:
        await update.message.reply_text("⚠️ خطا در بارگذاری منو.")
        return
    uid, firstname, lastname, role = row

    role_labels = {
        "buyer": "کاربر معمولی 👤",
        "seller": "فروشنده 🏪",
        "admin": "ادمین 👮",
        "manager": "مدیریت 🧑‍💼",
        "dev": "توسعه‌دهنده 🧑‍💻",
    }
    role_text = role_labels.get(role, role)

    text = f"👋 سلام {firstname} {lastname}\nنقش شما: {role_text}\n\nلطفاً یک بخش را انتخاب کنید:"

    buyer_buttons = [
        [InlineKeyboardButton("🛍 خریدهای من", callback_data="buyer:my_purchases")],
        [InlineKeyboardButton("📝 ثبت درخواست/نظر", callback_data="buyer:request")],
        [InlineKeyboardButton("📩 پشتیبانی", callback_data="buyer:support")],
        [InlineKeyboardButton("💡 انتقاد/پیشنهاد", callback_data="buyer:suggest")],
    ]

    role_buttons = []
    if role == "seller":
        role_buttons = [
            [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
            [InlineKeyboardButton("📦 محصولات من", callback_data="seller:my_products")],
        ]
    elif role == "manager":
        role_buttons = [
            [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
            [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:manage_products")],
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="manager:users")],
        ]
    elif role == "admin":
        role_buttons = [
            [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:manage_products")],
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin:users")],
            [InlineKeyboardButton("📜 لاگ‌ها", callback_data="admin:logs")],
        ]
    elif role == "dev":
        role_buttons = [
            [InlineKeyboardButton("⚙️ Debug Tools", callback_data="dev:menu")],
            [InlineKeyboardButton("📜 لاگ‌ها (Dev)", callback_data="dev:logs")],
        ]

    kb = []
    kb.extend(buyer_buttons)
    if role_buttons:
        kb.append([InlineKeyboardButton("────────", callback_data="noop")])
        kb.extend(role_buttons)
    kb.append([InlineKeyboardButton("🔙 خروج", callback_data="common:logout")])

    await update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    add_log(uid, "OPEN_MENU", f"role={role}")

# ------------------- Handlers -------------------

def get_auth_handlers():
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(auth_callback, pattern="^auth_")],
        states={
            REG_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_code)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_FIRST: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_first)],
            REG_LAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_last)],
            REG_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_pass)],
            LOGIN_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_phone)],
            LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_pass)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: (c.user_data.clear(), ReplyKeyboardRemove()))],
        allow_reentry=True,
    )
    handlers = [
        CommandHandler("start", start),
        conv,
    ]
    return handlers
