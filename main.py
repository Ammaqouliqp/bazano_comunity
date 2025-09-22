import sqlite3
import hashlib
import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# ---------- CONFIG ----------
TOKEN = "8251595621:AAFlLuEXqt6v0w6pJUgF_pdGd9IXKufPtiw"
REGISTER_CODE = "Havayekhoobarodarim"

# ---------- DATABASE ----------
conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

# users: role default = 'member'
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT,
    lastname TEXT,
    phonenumber TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'member'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    subject TEXT,
    message TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_code TEXT,
    buyer_id INTEGER,
    seller_id INTEGER,
    partners TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category TEXT,
    products TEXT,
    buyer_score INTEGER,
    buyer_feedback TEXT,
    FOREIGN KEY(buyer_id) REFERENCES users(id),
    FOREIGN KEY(seller_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    message TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    details TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

conn.commit()

# ---------- STATES ----------
ASK_CODE, ASK_PHONE, ASK_LOGIN_PASS, ASK_FIRSTNAME, ASK_LASTNAME, ASK_REGISTER_PASS = range(6)
SETROLE_PHONE, SETROLE_CHOOSE_ROLE = 100, 101

# ---------- IN-MEMORY SESSIONS ----------
# maps telegram_user_id -> phone
sessions = {}

# ---------- HELPERS ----------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_phone(phone: str):
    cursor.execute("SELECT id, firstname, lastname, phonenumber, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()  # (id, firstname, lastname, phonenumber, role) or None

def get_user_with_password(phone: str):
    cursor.execute("SELECT id, password, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()  # (id, password, firstname, lastname, role) or None

def get_user_id_by_phone(phone: str):
    row = get_user_by_phone(phone)
    return row[0] if row else None

def log_event(user_id, action, details=""):
    try:
        cursor.execute("INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)", (user_id, action, details))
        conn.commit()
    except Exception as e:
        # logging failure should not crash the bot
        print("Log error:", e)

def get_role_by_telegram_id(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    row = get_user_by_phone(phone)
    return row[4] if row else None

def is_manager(tg_id):
    role = get_role_by_telegram_id(tg_id)
    return role == "manager"

def is_admin(tg_id):
    role = get_role_by_telegram_id(tg_id)
    return role == "admin" or role == "manager"

# ---------- REGISTRATION / LOGIN / LOGOUT HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔑 لطفاً کد ثبت‌نام را وارد کنید:")
    return ASK_CODE

async def ask_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == REGISTER_CODE:
        await update.message.reply_text("📱 لطفاً شماره تلفن خود را با +98 وارد کنید (مثال: 989123456789+):")
        return ASK_PHONE
    else:
        await update.message.reply_text("❌ کد معتبر نیست. با /start دوباره تلاش کنید.")
        return ConversationHandler.END

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["phone"] = phone

    user = get_user_with_password(phone)
    if user:
        # user exists -> login
        await update.message.reply_text("🔒 شماره یافت شد. لطفاً رمز عبور را وارد کنید:")
        return ASK_LOGIN_PASS
    else:
        # register
        await update.message.reply_text("🆕 به بازانو خوش آمدید. لطفاً نام خود را وارد کنید:")
        return ASK_FIRSTNAME

async def ask_login_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data["phone"]
    user = get_user_with_password(phone)
    if user and user[1] == hash_password(update.message.text.strip()):
        # successful login
        sessions[update.effective_user.id] = phone
        user_id = user[0]
        log_event(user_id, 'login', f'telegram_id={update.effective_user.id}')
        await update.message.reply_text(f"✅ ورود موفق\n👤 خوش آمدید، {user[2]} {user[3]}")
    else:
        await update.message.reply_text("❌ رمز اشتباه است. با /start دوباره تلاش کنید.")
    return ConversationHandler.END

async def ask_firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["firstname"] = update.message.text.strip()
    await update.message.reply_text("✍️ لطفاً نام خانوادگی خود را وارد کنید:")
    return ASK_LASTNAME

async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lastname"] = update.message.text.strip()
    await update.message.reply_text("🔒 لطفاً یک رمز عبور برای حساب خود انتخاب کنید:")
    return ASK_REGISTER_PASS

async def ask_register_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data["phone"]
    firstname = context.user_data["firstname"]
    lastname = context.user_data["lastname"]
    password = hash_password(update.message.text.strip())

    # Insert with explicit role = 'member' (default new users are members)
    cursor.execute(
        "INSERT INTO users (firstname, lastname, phonenumber, password, role) VALUES (?, ?, ?, ?, ?)",
        (firstname, lastname, phone, password, 'member')
    )
    conn.commit()
    new_user_id = cursor.lastrowid

    sessions[update.effective_user.id] = phone
    log_event(new_user_id, 'signup', f'telegram_id={update.effective_user.id}')

    await update.message.reply_text(f"✅ ثبت‌نام موفق!\n👤 خوش آمدی {firstname} {lastname}\nنقش شما: عضو (member)")
    return ConversationHandler.END

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    if tg_id in sessions:
        phone = sessions.pop(tg_id)
        user_id = get_user_id_by_phone(phone)
        if user_id:
            log_event(user_id, 'logout', f'telegram_id={tg_id}')
        await update.message.reply_text("🚪 شما با موفقیت خارج شدید.")
    else:
        await update.message.reply_text("⚠️ شما وارد نشده‌اید.")

# ---------- PROFILE ----------
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    phone = sessions.get(tg_id)
    if not phone:
        await update.message.reply_text("⚠️ شما وارد نشده‌اید. برای ورود /start را بزنید.")
        return

    row = get_user_by_phone(phone)
    if not row:
        await update.message.reply_text("⚠️ کاربر در دیتابیس یافت نشد.")
        return

    user_id, firstname, lastname, ph, role = row
    await update.message.reply_text(
        f"👤 اطلاعات شما:\n\nنام: {firstname}\nنام خانوادگی: {lastname}\nشماره: {ph}\nنقش: {role}"
    )

# ---------- HELP ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 راهنمای دستورات (فارسی):\n\n"
        "/start – شروع فرایند ورود یا ثبت‌نام\n"
        "/logout – خروج از حساب\n"
        "/profile – نمایش اطلاعات کاربری\n"
        "/help – نمایش این راهنما\n\n"
        "دستورات مدیریتی (فقط برای manager):\n"
        "/list_users – مشاهدهٔ فهرست کاربران\n"
        "/setrole – تغییر نقش یک کاربر (تعاملی)\n\n"
        "توضیح: برای ثبت‌نام با /start شروع کنید، کد را وارد کنید، شماره، نام و پس از آن رمز انتخاب کنید."
    )

# ---------- MANAGER: list_users ----------
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_manager(update.effective_user.id):
        await update.message.reply_text("❌ دسترسی ندارید. این دستور فقط برای مدیر (manager) است.")
        return

    cursor.execute("SELECT id, firstname, lastname, phonenumber, role FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("هیچ کاربری یافت نشد.")
        return

    text_lines = ["📋 فهرست کاربران:"]
    for r in rows:
        uid, fn, ln, ph, role = r
        text_lines.append(f"• id={uid} | {fn} {ln} | {ph} | role={role}")
    await update.message.reply_text("\n".join(text_lines))

# ---------- MANAGER: setrole (conversation) ----------
async def setrole_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_manager(update.effective_user.id):
        await update.message.reply_text("❌ دسترسی ندارید. این دستور فقط برای مدیر (manager) است.")
        return ConversationHandler.END

    await update.message.reply_text("📱 لطفاً شماره تلفن کاربر مورد نظر را وارد کنید (مثال: +994501234567):")
    return SETROLE_PHONE

async def setrole_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["setrole_target_phone"] = phone

    row = get_user_by_phone(phone)
    if not row:
        await update.message.reply_text("⚠️ کاربری با این شماره یافت نشد. عملیات لغو شد.")
        return ConversationHandler.END

    target_id, fn, ln, ph, old_role = row
    # options keyboard (roles)
    roles = ["member", "buyer", "seller", "admin", "manager"]
    reply_kb = ReplyKeyboardMarkup([[r] for r in roles], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        f"👤 یافت شد: {fn} {ln} | شماره: {ph} | نقش فعلی: {old_role}\n\n"
        "لطفاً نقش جدید را از لیست انتخاب کنید:",
        reply_markup=reply_kb
    )
    context.user_data["setrole_target_id"] = target_id
    context.user_data["setrole_old_role"] = old_role
    return SETROLE_CHOOSE_ROLE

async def setrole_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_role = update.message.text.strip().lower()
    allowed = ["member", "buyer", "seller", "admin", "manager"]
    if new_role not in allowed:
        await update.message.reply_text("نقش نامعتبر است. عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    phone = context.user_data.get("setrole_target_phone")
    target_id = context.user_data.get("setrole_target_id")
    old_role = context.user_data.get("setrole_old_role")
    manager_tg = update.effective_user.id

    cursor.execute("UPDATE users SET role=? WHERE phonenumber=?", (new_role, phone))
    conn.commit()

    # log both for target user and for manager (optional)
    log_event(target_id, 'role_changed', f'from {old_role} to {new_role} by manager_tg={manager_tg}')
    manager_user_id = get_user_id_by_phone(sessions.get(manager_tg)) if sessions.get(manager_tg) else None
    if manager_user_id:
        log_event(manager_user_id, 'changed_role', f'changed user_id={target_id} to {new_role}')

    await update.message.reply_text(
        f"✅ نقش کاربر با شماره {phone} از {old_role} به {new_role} تغییر کرد.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ---------- FALLBACK / CANCEL ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ---------- MAIN ----------
def main():
    app = Application.builder().token(TOKEN).build()

    # Conversation handler for registration/login
    conv_handler = ConversationHandler(
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
    )

    # Conversation handler for setrole
    setrole_conv = ConversationHandler(
        entry_points=[CommandHandler("setrole", setrole_start)],
        states={
            SETROLE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setrole_phone)],
            SETROLE_CHOOSE_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setrole_choose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(setrole_conv)
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list_users", list_users))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
