# dev_menu.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from config import DEV_ID
from logs import get_logs, get_errors
import importlib
import sys

async def dev_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != DEV_ID:
        await update.message.reply_text("⛔ شما توسعه‌دهنده نیستید.")
        return
    kb = [
        [InlineKeyboardButton("📜 آخرین لاگ‌ها", callback_data="dev:logs")],
        [InlineKeyboardButton("⚠️ خطاها", callback_data="dev:errors")],
        [InlineKeyboardButton("♻️ ری‌لود ماژول‌ها", callback_data="dev:reload")],
        [InlineKeyboardButton("🔙 بستن", callback_data="dev:close")]
    ]
    await update.message.reply_text("👨‍💻 منوی توسعه‌دهنده:", reply_markup=InlineKeyboardMarkup(kb))

async def dev_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    uid = cq.from_user.id
    if uid != DEV_ID:
        await cq.message.reply_text("⛔ دسترسی ندارید.")
        return
    if cq.data == "dev:logs":
        rows = get_logs(50)
        if not rows:
            await cq.message.reply_text("📭 لاگی وجود ندارد.")
            return
        text = "📜 لاگ‌ها:\n\n" + "\n\n".join([f"#{r[0]} | user {r[1]} | {r[2]} | {r[3]} | {r[4]}" for r in rows])
        await cq.message.reply_text(text)
    elif cq.data == "dev:errors":
        rows = get_errors(50)
        if not rows:
            await cq.message.reply_text("📭 خطایی ثبت نشده.")
            return
        text = "⚠️ خطاها:\n\n" + "\n\n".join([f"#{r[0]} | user {r[1]} | {r[2]} | {r[3]} | {r[4]}" for r in rows])
        await cq.message.reply_text(text)
    elif cq.data == "dev:reload":
        # simple reload of main modules: attempt importlib.reload for key modules
        mods = ["auth","products","buyer","seller","admin_menu","manager_menu","dev_menu"]
        reloaded = []
        for m in mods:
            if m in sys.modules:
                importlib.reload(sys.modules[m])
                reloaded.append(m)
        await cq.message.reply_text("♻️ ماژول‌ها ری‌لود شدند: " + ", ".join(reloaded))
    elif cq.data == "dev:close":
        try:
            await cq.message.delete()
        except:
            pass

def get_dev_handlers():
    return [
        CommandHandler("dev", dev_menu),
        CallbackQueryHandler(dev_callback, pattern="^dev:")
    ]
