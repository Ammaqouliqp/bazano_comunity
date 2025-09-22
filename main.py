from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TOKEN
from auth import get_auth_handlers  
from menus.dev_menu import dev_menu, dev_callback
from menus.manager_menu import manager_menu, manager_callback
from telegram.ext import CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from auth import start, register_start, ask_firstname, ask_lastname, ask_phone, ask_pass, login_start, ask_login_phone, ask_login_pass


def main():
    app = Application.builder().token(TOKEN).build()

    # هندلرهای auth (ثبت‌نام/ورود/پروفایل/خروج/راهنما)
    app.add_handlers(get_auth_handlers())

    # منوها
    app.add_handler(CommandHandler("dev", dev_menu))
    app.add_handler(CommandHandler("manager", manager_menu))

    # کال‌بک‌ها
    app.add_handler(CallbackQueryHandler(dev_callback, pattern="^dev_"))
    app.add_handler(CallbackQueryHandler(manager_callback, pattern="^manager_"))

    # اجرا
    app.run_polling()


if __name__ == "__main__":
    main()
