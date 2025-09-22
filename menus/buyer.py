from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from db import cursor, conn
from logs import log_event
from auth import sessions
import datetime

# -----------------------
# چک ورود کاربر
def check_login(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None, "⚠️ اول باید لاگین کنید (/start)"
    cursor.execute("SELECT id, firstname, lastname FROM users WHERE phonenumber=?", (phone,))
    user = cursor.fetchone()
    if not user:
        return None, "⚠️ کاربر یافت نشد."
    return user, None

# -----------------------
# منوی خریدار
async def buyer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return

    log_event(user[0], "menu_open", "buyer_menu")

    await update.message.reply_text(
        "🛍 منوی خریدار:\n\n"
        "۱️⃣ /my_purchases – مشاهده خریدهای من\n"
        "۲️⃣ /feedback – ثبت نظر برای خرید\n"
        "۳️⃣ /support – ارسال پیام پشتیبانی\n"
        "۴️⃣ /suggestions – ارسال انتقاد یا پیشنهاد"
    )

# -----------------------
# مشاهده خریدهای خریدار
async def my_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return

    buyer_id = user[0]
    cursor.execute("SELECT id, seller, date, sector FROM transactions WHERE buyer=?", (buyer_id,))
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("📭 شما هیچ خریدی انجام نداده‌اید.")
        return

    text = "🛒 خریدهای شما:\n\n"
    for row in rows:
        text += f"شماره: {row[0]} | فروشنده: {row[1]} | تاریخ: {row[2]} | صنف: {row[3]}\n"
    await update.message.reply_text(text)

# -----------------------
# ثبت نظر برای خرید
ASK_TRANSACTION_ID, ASK_FEEDBACK_TEXT = range(2)

async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return ConversationHandler.END

    await update.message.reply_text("📝 لطفاً شماره تراکنش را وارد کنید:")
    return ASK_TRANSACTION_ID

async def feedback_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["transaction_id"] = update.message.text.strip()
    await update.message.reply_text("✍️ نظر خود را وارد کنید:")
    return ASK_FEEDBACK_TEXT

async def feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return ConversationHandler.END

    transaction_id = context.user_data["transaction_id"]
    feedback_text = update.message.text.strip()
    buyer_id = user[0]

    cursor.execute("INSERT INTO feedbacks (user_id, transaction_id, message, date) VALUES (?, ?, ?, ?)",
                   (buyer_id, transaction_id, feedback_text, datetime.datetime.now()))
    conn.commit()

    log_event(buyer_id, "feedback", f"transaction={transaction_id}")
    await update.message.reply_text("✅ نظر شما ثبت شد. متشکریم 🙏")
    return ConversationHandler.END

# -----------------------
# ارسال پیام پشتیبانی
ASK_SUPPORT_TEXT = range(1)

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return ConversationHandler.END

    await update.message.reply_text("📩 لطفاً پیام خود برای پشتیبانی را بنویسید:")
    return ASK_SUPPORT_TEXT

async def support_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        return ConversationHandler.END

    buyer_id = user[0]
    msg = update.message.text.strip()

    cursor.execute("INSERT INTO support (user_id, message, date) VALUES (?, ?, ?)",
                   (buyer_id, msg, datetime.datetime.now()))
    conn.commit()

    log_event(buyer_id, "support", "message_sent")
    await update.message.reply_text("✅ پیام شما به پشتیبانی ارسال شد.")
    return ConversationHandler.END

# -----------------------
# انتقادات و پیشنهادات
ASK_SUGGESTION_TEXT = range(1)

async def suggestions_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return ConversationHandler.END

    await update.message.reply_text("💡 لطفاً نظر، انتقاد یا پیشنهاد خود را وارد کنید:")
    return ASK_SUGGESTION_TEXT

async def suggestions_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login(update.effective_user.id)
    if err:
        return ConversationHandler.END

    buyer_id = user[0]
    msg = update.message.text.strip()

    cursor.execute("INSERT INTO suggestions (user_id, message, date) VALUES (?, ?, ?)",
                   (buyer_id, msg, datetime.datetime.now()))
    conn.commit()

    log_event(buyer_id, "suggestion", "message_sent")
    await update.message.reply_text("✅ نظر شما ثبت شد. متشکریم 🙏")
    return ConversationHandler.END

# -----------------------
# گرفتن هندلرها
def get_buyer_handlers():
    return [
        CommandHandler("buyer_menu", buyer_menu),
        CommandHandler("my_purchases", my_purchases),
        ConversationHandler(
            entry_points=[CommandHandler("feedback", feedback_start)],
            states={
                ASK_TRANSACTION_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_transaction)],
                ASK_FEEDBACK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_text)],
            },
            fallbacks=[],
        ),
        ConversationHandler(
            entry_points=[CommandHandler("support", support_start)],
            states={
                ASK_SUPPORT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_text)],
            },
            fallbacks=[],
        ),
        ConversationHandler(
            entry_points=[CommandHandler("suggestions", suggestions_start)],
            states={
                ASK_SUGGESTION_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, suggestions_text)],
            },
            fallbacks=[],
        ),
    ]
