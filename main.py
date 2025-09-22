from telegram.ext import Application
from auth import get_auth_handlers
from menus.admin_menu import get_admin_handlers
from menus.seller_menu import get_seller_handlers
from menus.buyer import get_buyer_handlers
from products import get_product_handlers
TOKEN = "8251595621:AAFlLuEXqt6v0w6pJUgF_pdGd9IXKufPtiw"

def main():
    app = Application.builder().token(TOKEN).build()

    # auth
    for handler in get_auth_handlers():
        app.add_handler(handler)

    # admin
    for handler in get_admin_handlers():
        app.add_handler(handler)

    # seller
    for handler in get_seller_handlers():
        app.add_handler(handler)

    # buyer
    for handler in get_buyer_handlers():
        app.add_handler(handler)

    for handler in get_product_handlers():
        app.add_handler(handler)
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
