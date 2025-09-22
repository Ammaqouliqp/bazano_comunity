# buyer.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, ContextTypes, filters
from db import cursor, conn
from auth import sessions
from logs import add_log
from utils import now

(REQ_SUBJECT, REQ_TEXT) = range(2)

def get_user(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def buyer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.message
    user = get_user(update.effective_user.id)
    if not user:
        await target.reply_text("⚠️ ابتدا وارد شوید.")
        return
    kb = [
        [InlineKeyboardButton("🛍 خریدهای من", callback_data="buyer:my_purchases")],
        [InlineKeyboardButton("📝 ثبت درخواست خرید", callback_data="buyer:request")],
        [InlineKeyboardButton("📩 پشتیبانی", callback_data="buyer:support")],
        [InlineKeyboardButton("💡 انتقاد/پیشنهاد", callback_data="buyer:suggest")],
        [InlineKeyboardButton("🔙 بستن", callback_data="buyer:close")]
    ]
    await target.reply_text("🛒 منوی خریدار:", reply_markup=InlineKeyboardMarkup(kb))

async def my_purchases_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    user = get_user(cq.from_user.id)
    if not user:
        await cq.message.reply_text("⚠️ ابتدا وارد شوید.")
        return
    uid = user[0]
    cursor.execute("SELECT id, seller, date, sector FROM transactions WHERE buyer=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        await cq.message.reply_text("📭 شما خریدی ندارید.")
        return
    text = "🛒 خریدهای شما:\n\n"
    for r in rows:
        text += f"#{r[0]} | فروشنده: {r[1]} | تاریخ: {r[2]} | صنف: {r[3]}\n"
    await cq.message.reply_text(text)

# request flow
async def request_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    await cq.message.reply_text("📝 لطفاً موضوع درخواست را وارد کنید:")
    return REQ_SUBJECT

async def req_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['req_subject'] = update.message.text.strip()
    await update.message.reply_text("✍️ متن درخواست را وارد کنید:")
    return REQ_TEXT

async def req_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ ابتدا وارد شوید.")
        return ConversationHandler.END
    cursor.execute("INSERT INTO requests (user_id, subject, message, date) VALUES (?, ?, ?, ?)",
                   (user[0], context.user_data.get('req_subject'), update.message.text.strip(), now()))
    conn.commit()
    add_log(user[0], "REQUEST", context.user_data.get('req_subject'))
    await update.message.reply_text("✅ درخواست ثبت شد. بعد از بررسی با شما تماس می‌گیریم.")
    return ConversationHandler.END

async def support_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    await cq.message.reply_text("📩 لطفاً پیام پشتیبانی را تایپ کنید (ارسال کنید):")
    return REQ_TEXT  # reuse

# suggestions
async def suggest_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    await cq.message.reply_text("💡 لطفاً انتقاد یا پیشنهاد خود را ارسال کنید:")
    return REQ_TEXT

async def suggest_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ ابتدا وارد شوید.")
        return ConversationHandler.END
    cursor.execute("INSERT INTO suggestions (user_id, message, date) VALUES (?, ?, ?)", (user[0], update.message.text.strip(), now()))
    conn.commit()
    add_log(user[0], "SUGGESTION", update.message.text.strip())
    await update.message.reply_text("✅ پیام شما ثبت شد.")
    return ConversationHandler.END

async def buyer_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except:
            pass

def get_buyer_handlers():
    handlers = []
    handlers.append(CommandHandler("buyer_menu", buyer_menu))
    handlers.append(CallbackQueryHandler(buyer_menu, pattern="^buyer_menu$"))
    handlers.append(CallbackQueryHandler(my_purchases_cb, pattern="^buyer:my_purchases$"))
    # request conv
    request_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_start_cb, pattern="^buyer:request$")],
        states={
            REQ_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_subject)],
            REQ_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_text)]
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: c.user_data.clear())],
        allow_reentry=True
    )
    handlers.append(request_conv)
    # support conv (simple)
    support_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(support_cb, pattern="^buyer:support$")],
        states={
            REQ_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: (support_save(u,c) if False else None))]
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: c.user_data.clear())],
        allow_reentry=True
    )
    # we will not use support_conv here; direct text handlers used in products/buyer flows
    handlers.append(CallbackQueryHandler(suggest_cb, pattern="^buyer:suggest$"))
    handlers.append(CallbackQueryHandler(buyer_close, pattern="^buyer:close$"))
    return handlers
