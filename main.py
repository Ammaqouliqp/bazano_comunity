from telegram.ext import Application
from auth import get_auth_handlers
from db import init_db
from logs import log_event
from transactions import get_transaction_handlers
from menus.manager_menu import get_manager_handlers
from menus.admin_menu import get_admin_handlers
from menus.seller_menu import get_seller_handlers
from menus.buyer_menu import get_buyer_handlers

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

def main():
    # init db
    init_db()

    # create bot
    app = Application.builder().token(TOKEN).build()

    # auth handlers
    for h in get_auth_handlers():
        app.add_handler(h)

    # transaction handlers
    for h in get_transaction_handlers():
        app.add_handler(h)

    # menus
    for h in get_manager_handlers():
        app.add_handler(h)

    for h in get_admin_handlers():
        app.add_handler(h)

    for h in get_seller_handlers():
        app.add_handler(h)

    for h in get_buyer_handlers():
        app.add_handler(h)

    print("🤖 Bot is running ...")
    app.run_polling()

if __name__ == "__main__":
    main()
