from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from config import TOKEN
from auth import get_auth_handlers
from buyer_menu import get_buyer_handlers
from seller_menu import get_seller_handlers
from manager_menu import get_manager_handlers
from admin_menu import get_admin_handlers
from dev_menu import get_dev_handlers


def main():
    app = Application.builder().token(TOKEN).build()

    # --- Auth Handlers ---
    for h in get_auth_handlers():
        app.add_handler(h)

    # --- Buyer Menu (همه می‌بینن) ---
    for h in get_buyer_handlers():
        app.add_handler(h)

    # --- Seller Menu ---
    for h in get_seller_handlers():
        app.add_handler(h)

    # --- Manager Menu ---
    for h in get_manager_handlers():
        app.add_handler(h)

    # --- Admin Menu ---
    for h in get_admin_handlers():
        app.add_handler(h)

    # --- Dev Menu ---
    for h in get_dev_handlers():
        app.add_handler(h)

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
