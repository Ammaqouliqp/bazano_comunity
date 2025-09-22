# requests.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ConversationHandler, MessageHandler, filters,
    CallbackQueryHandler, CommandHandler, ContextTypes
)
from db import cursor, conn
from utils import now
from logs import add_log
from auth import sessions

(REQ_SUBJECT, REQ_TEXT) = range(2)

def get_user_by_tg(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def request_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        "📝 لطفاً موضوع درخواست را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="cancel")]])
    )
    return REQ_SUBJECT

async def request_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['req_subject'] = update.message.text.strip()
    await update.message.reply_text("✍️ حالا متن درخواست را وارد کنید:")
    return REQ_TEXT

async def request_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_tg(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ ابتدا وارد شوید.")
        return ConversationHandler.END

    cursor.execute(
        "INSERT INTO requests (user_id, subject, message, date) VALUES (?, ?, ?, ?)",
        (user[0], context.user_data.get('req_subject'), update.message.text.strip(), now())
    )
    conn.commit()
    add_log(user[0], "REQUEST", context.user_data.get('req_subject'))

    await update.message.reply_text(
        "✅ درخواست شما با موفقیت ثبت شد.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="buyer:menu")]])
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

def get_request_handlers():
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_start_cb, pattern="^buyer:request$|^common:request$")],
        states={
            REQ_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_subject)],
            REQ_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_text)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern="^cancel$")
        ],
        allow_reentry=True
    )
    return [conv]
