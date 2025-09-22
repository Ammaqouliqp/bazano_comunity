from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TOKEN
from auth import start
from menus.dev_menu import dev_menu, dev_callback
from menus.manager_menu import manager_menu, manager_callback

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dev", dev_menu))
    app.add_handler(CommandHandler("manager", manager_menu))

    app.add_handler(CallbackQueryHandler(dev_callback, pattern="^dev_"))
    app.add_handler(CallbackQueryHandler(manager_callback, pattern="^manager_"))

    app.run_polling()

if __name__ == "__main__":
    main()
