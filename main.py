from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TOKEN

from auth import get_auth_handlers
from buyer import get_buyer_handlers
from seller import get_seller_handlers
from admin_menu import get_admin_handlers
from manager_menu import get_manager_handlers
from dev_menu import get_dev_handlers

def main():
    app = Application.builder().token(TOKEN).build()

    # Auth
    for h in get_auth_handlers():
        app.add_handler(h)

    # Buyer (همه دارن)
    for h in get_buyer_handlers():
        app.add_handler(h)

    # Seller
    for h in get_seller_handlers():
        app.add_handler(h)

    # Manager
    for h in get_manager_handlers():
        app.add_handler(h)

    # Admin
    for h in get_admin_handlers():
        app.add_handler(h)

    # Dev
    for h in get_dev_handlers():
        app.add_handler(h)

    print("🤖 Bot running…")
    app.run_polling()

if __name__ == "__main__":
    main()
