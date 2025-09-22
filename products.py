from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from db import cursor, conn
from auth import sessions
from logs import log_event
import datetime

# STATES
ASK_SECTOR, ASK_BRAND, ASK_NAME, ASK_DESCRIPTION, ASK_AMOUNT, ASK_PRICE_ENTRY, ASK_PRICE_EXIT, ASK_SELLER_PHONE, ASK_PRODUCTION_DATE, ASK_EXPIRATION_DATE = range(10)

# ---------- helper ----------
def check_login_role(tg_id, allowed_roles=None):
    """
    returns (user_row, None) or (None, error_message)
    user_row = (id, firstname, lastname, phonenumber, role) if found
    """
    phone = sessions.get(tg_id)
    if not phone:
        return None, "⚠️ اول باید لاگین کنید (/start)"
    cursor.execute("SELECT id, firstname, lastname, phonenumber, role FROM users WHERE phonenumber=?", (phone,))
    user = cursor.fetchone()
    if not user:
        return None, "⚠️ کاربر در دیتابیس یافت نشد."
    if allowed_roles and user[4] not in allowed_roles:
        return None, "⛔ شما دسترسی لازم را ندارید."
    return user, None

# ---------- start ----------
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, err = check_login_role(update.effective_user.id, allowed_roles=["seller", "admin", "manager"])
    if err:
        await update.message.reply_text(err)
        return ConversationHandler.END

    await update.message.reply_text(
        "📦 ثبت محصول جدید — مرحله اول\n"
        "لطفاً *صنف* محصول را وارد کنید (مثلاً: موبایل، خوراکی، پوشاک).\n\n"
        "برای خروج از فرایند /cancel را بزنید.",
        parse_mode="Markdown"
    )
    return ASK_SECTOR

async def add_product_sector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sector"] = update.message.text.strip()
    await update.message.reply_text("🏷 لطفاً برند محصول را وارد کنید (یا اگر ندارد 'بدون برند' بنویسید):")
    return ASK_BRAND

async def add_product_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["brand"] = update.message.text.strip()
    await update.message.reply_text("📛 لطفاً نام محصول را وارد کنید:")
    return ASK_NAME

async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("📝 لطفاً توضیحات محصول را وارد کنید (مشخصات کوتاه، مدل، رنگ و ...):")
    return ASK_DESCRIPTION

async def add_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text.strip()
    await update.message.reply_text(
        "🔢 لطفاً مقدار (amount) را همراه واحد وارد کنید.\n"
        "مثال: `5 kg` یا `10 بسته` یا `1 عدد`.\n"
        "توجه: مقدار به صورت متن ذخیره می‌شود تا انعطاف داشته باشیم."
    )
    return ASK_AMOUNT

async def add_product_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text.strip()

    # role-specific instruction for price_entry
    user, _ = check_login_role(update.effective_user.id)
    role = user[4]

    if role == "seller":
        prompt = (
            "💵 لطفاً *قیمت ورود* را وارد کنید (قیمت وارد شدن کالای شما به بازانو).\n"
            "🔔 لطفاً قیمت واحد را وارد نمایید (قیمت ورودی بر اساس هر واحد/وزن باشد)."
        )
    else:  # admin / manager
        prompt = (
            "💵 لطفاً *قیمت ورود* را وارد کنید.\n"
            "توضیح: این قیمت، قیمت ورود به بازانو است و باید قیمت خروج در مراحل خرید ثبت شود.\n"
            "🔔 لطفاً قیمت واحد را وارد نمایید (قیمت بر اساس هر واحد/وزن باشد)."
        )

    await update.message.reply_text(prompt, parse_mode="Markdown")
    return ASK_PRICE_ENTRY

async def add_product_price_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        price_entry = float(txt)
    except:
        await update.message.reply_text("⚠️ مقدار قیمت نامعتبر است. لطفاً یک عدد (مثلاً 123.45) وارد کنید.")
        return ASK_PRICE_ENTRY

    context.user_data["price_entry"] = price_entry

    # decide next step based on role
    user, _ = check_login_role(update.effective_user.id)
    role = user[4]

    if role in ["admin", "manager"]:
        # ask for price_exit (admin/manager can view/set it)
        await update.message.reply_text(
            "💱 (فقط برای admin/manager) در صورت وجود، قیمت خروج را وارد کنید؛ در غیر این صورت 'no' یا '-' بنویسید."
        )
        return ASK_PRICE_EXIT
    else:
        # seller -> seller_id is the current user
        context.user_data["seller_id"] = user[0]
        await update.message.reply_text(
            "📅 لطفاً تاریخ تولید را وارد کنید (فرمت پیشنهادی YYYY-MM-DD) یا اگر موجود نیست 'no' وارد کنید:"
        )
        return ASK_PRODUCTION_DATE

async def add_product_price_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    if txt in ("no", "-", "none", ""):
        context.user_data["price_exit"] = None
    else:
        try:
            context.user_data["price_exit"] = float(txt)
        except:
            await update.message.reply_text("⚠️ مقدار قیمت خروج نامعتبر است. یک عدد وارد کنید یا 'no' بنویسید.")
            return ASK_PRICE_EXIT

    # ask for seller phone to associate product
    await update.message.reply_text("📱 لطفاً شماره تلفن فروشنده را وارد کنید (مثال: +994501234567):")
    return ASK_SELLER_PHONE

async def add_product_seller_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    cursor.execute("SELECT id, role FROM users WHERE phonenumber=?", (phone,))
    row = cursor.fetchone()
    if not row:
        await update.message.reply_text("⚠️ کاربری با این شماره یافت نشد. لطفاً شماره‌ صحیح وارد کنید یا /cancel برای لغو.")
        return ASK_SELLER_PHONE

    seller_id, seller_role = row
    # ensure the target is a seller (or allow admin/manager to set any user as seller?)
    if seller_role != "seller":
        await update.message.reply_text("⚠️ کاربر یافت شد اما نقش او seller نیست. لطفاً شمارهٔ یک فروشنده را وارد کنید.")
        return ASK_SELLER_PHONE

    context.user_data["seller_id"] = seller_id
    await update.message.reply_text("📅 لطفاً تاریخ تولید را وارد کنید (فرمت YYYY-MM-DD) یا اگر نیست 'no' وارد کنید:")
    return ASK_PRODUCTION_DATE

async def add_product_production_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt.lower() in ("no", "-", ""):
        context.user_data["production_date"] = None
    else:
        context.user_data["production_date"] = txt  # keep as text
    await update.message.reply_text("⏳ لطفاً تاریخ انقضا را وارد کنید (فرمت YYYY-MM-DD) یا 'no' اگر ندارد:")
    return ASK_EXPIRATION_DATE

async def add_product_expiration_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt.lower() in ("no", "-", ""):
        context.user_data["expiration_date"] = None
    else:
        context.user_data["expiration_date"] = txt

    # save product
    sector = context.user_data.get("sector")
    brand = context.user_data.get("brand")
    name = context.user_data.get("name")
    description = context.user_data.get("description")
    amount = context.user_data.get("amount")
    price_entry = context.user_data.get("price_entry")
    price_exit = context.user_data.get("price_exit", None)
    production_date = context.user_data.get("production_date")
    expiration_date = context.user_data.get("expiration_date")
    seller_id = context.user_data.get("seller_id")

    now = datetime.datetime.now().isoformat()
    cursor.execute(
        """INSERT INTO products (
            seller_id, sector, brand, name, description, amount,
            price_entry, price_exit, production_date, expiration_date, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (seller_id, sector, brand, name, description, amount, price_entry, price_exit, production_date, expiration_date, now)
    )
    conn.commit()
    product_id = cursor.lastrowid

    # actor (who ran /add_product)
    actor_user, _ = check_login_role(update.effective_user.id)
    actor_id = actor_user[0]

    log_event(actor_id, "add_product", f"product_id={product_id} seller={seller_id} name={name}")

    # reply summary (hide price_exit if creator was seller)
    if actor_user[4] == "seller":
        await update.message.reply_text(
            f"✅ محصول ثبت شد (id={product_id}):\n\n"
            f"📦 نام: {name}\n"
            f"🏷 برند: {brand}\n"
            f"صنف: {sector}\n"
            f"📦 مقدار: {amount}\n"
            f"💵 قیمت ورود (واحد): {price_entry}\n"
            f"📅 تولید: {production_date or '-'}\n"
            f"⏳ انقضا: {expiration_date or '-'}\n\n"
            "🔔 توجه: قیمت خروج فقط توسط admin/manager قابل مشاهده و ویرایش است."
        )
    else:
        await update.message.reply_text(
            f"✅ محصول ثبت شد (id={product_id}):\n\n"
            f"📦 نام: {name}\n"
            f"🏷 برند: {brand}\n"
            f"صنف: {sector}\n"
            f"📦 مقدار: {amount}\n"
            f"💵 قیمت ورود (واحد): {price_entry}\n"
            f"💰 قیمت خروج: {price_exit if price_exit is not None else '-'}\n"
            f"📅 تولید: {production_date or '-'}\n"
            f"⏳ انقضا: {expiration_date or '-'}"
        )

    return ConversationHandler.END

async def cancel_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات ثبت محصول لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ---------- handlers getter ----------
def get_product_handlers():
    conv = ConversationHandler(
        entry_points=[CommandHandler("add_product", add_product_start)],
        states={
            ASK_SECTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_sector)],
            ASK_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_brand)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_description)],
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_amount)],
            ASK_PRICE_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price_entry)],
            ASK_PRICE_EXIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price_exit)],
            ASK_SELLER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_seller_phone)],
            ASK_PRODUCTION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_production_date)],
            ASK_EXPIRATION_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_expiration_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_product)],
        allow_reentry=False,
    )
    return [conv]
