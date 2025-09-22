# main.py
from telegram.ext import Application
from config import TOKEN
from db import init_db

# import get handlers from modules
from auth import get_auth_handlers
from products import get_product_handlers
from menus.buyer_menu import get_buyer_handlers
from menus.seller_menu import get_seller_handlers
from menus.admin_menu import get_admin_handlers
from menus.manager_menu import get_manager_handlers
from menus.dev_menu import get_dev_handlers
from transactions import get_transaction_handlers

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # register handlers (each module returns list of handlers)
    for h in get_auth_handlers():
        app.add_handler(h)

    for h in get_product_handlers():
        app.add_handler(h)

    for h in get_buyer_handlers():
        app.add_handler(h)

    for h in get_seller_handlers():
        app.add_handler(h)

    for h in get_admin_handlers():
        app.add_handler(h)

    for h in get_manager_handlers():
        app.add_handler(h)

    for h in get_dev_handlers():
        app.add_handler(h)

    for h in get_transaction_handlers():
        app.add_handler(h)

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
