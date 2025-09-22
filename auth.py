from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import cursor, conn
from utils import hash_password
from logs import add_log

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ثبت‌نام", callback_data="register")],
        [InlineKeyboardButton("ورود", callback_data="login")]
    ]
    await update.message.reply_text("به ربات فروشگاه خوش آمدید 🙌", reply_markup=InlineKeyboardMarkup(keyboard))

async def register_user(user_id, firstname, lastname, phone, password):
    cursor.execute(
        "INSERT INTO users (firstname, lastname, phonenumber, password) VALUES (?, ?, ?, ?)",
        (firstname, lastname, phone, hash_password(password))
    )
    conn.commit()
    add_log(user_id, "REGISTER", f"{firstname} {lastname}")
