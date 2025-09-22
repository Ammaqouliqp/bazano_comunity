from telegram.ext import CommandHandler

async def my_transactions(update, context):
    await update.message.reply_text("📦 لیست تراکنش‌های شما (در حال توسعه).")

def get_transaction_handlers():
    return [
        CommandHandler("my_transactions", my_transactions),
    ]
