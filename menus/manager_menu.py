from telegram.ext import CommandHandler

async def manager_menu(update, context):
    await update.message.reply_text("📋 منوی مدیر (در حال توسعه).")

def get_manager_handlers():
    return [
        CommandHandler("manager_menu", manager_menu),
    ]
