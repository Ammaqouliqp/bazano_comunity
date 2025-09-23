# main.py
from telegram.ext import Application
from config import TOKEN
from db import init_db

# import handlers
from auth import get_auth_handlers, start
from products import get_product_handlers
from requests import get_request_handlers
from buyer import get_buyer_handlers
from seller import get_seller_handlers
from manager import get_manager_handlers
from admin import get_admin_handlers
from dev import get_dev_handlers
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # auth (start and conv)
    for h in get_auth_handlers():
        app.add_handler(h)

    # product handlers
    for h in get_product_handlers():
        app.add_handler(h)

    # requests
    for h in get_request_handlers():
        app.add_handler(h)

    # role menus & callbacksz
    for h in get_buyer_handlers():
        app.add_handler(h)
    for h in get_seller_handlers():
        app.add_handler(h)
    for h in get_manager_handlers():
        app.add_handler(h)
    for h in get_admin_handlers():
        app.add_handler(h)
    for h in get_dev_handlers():
        app.add_handler(h)

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
