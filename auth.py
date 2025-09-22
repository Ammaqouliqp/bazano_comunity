from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db import cursor
from logs import log_event

sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 خوش آمدید! از /help برای راهنما استفاده کنید.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 راهنما:\n\n"
        "/start – شروع\n"
        "/profile – اطلاعات کاربری\n"
        "/logout – خروج\n"
        "/help – راهنما"
    )

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    if tg_id in sessions:
        sessions.pop(tg_id)
        await update.message.reply_text("🚪 خروج موفق.")
    else:
        await update.message.reply_text("⚠️ شما وارد نشده‌اید.")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 پروفایل شما (به زودی تکمیل می‌شود).")

def get_auth_handlers():
    return [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("logout", logout),
        CommandHandler("profile", profile),
    ]
