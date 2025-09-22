# products.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
from db import cursor, conn
from logs import add_log
from auth import sessions

(ADD_BRAND, ADD_NAME, ADD_DESC, ADD_MDATE, ADD_EDATE, ADD_QTY, ADD_PRICE_ENTRY, ADD_PRICE_EXIT) = range(8)
PAGE_SIZE = 6

def get_user_by_tg(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

async def products_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
        [InlineKeyboardButton("📋 لیست محصولات", callback_data="products:list:0")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main:back")],
    ]
    await update.message.reply_text("📦 منوی محصولات:", reply_markup=InlineKeyboardMarkup(kb))

# add flow
async def add_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
        await q.message.reply_text("➕ شروع افزودن محصول — برند را وارد کنید:")
    else:
        await update.message.reply_text("➕ شروع افزودن محصول — برند را وارد کنید:")
    user = get_user_by_tg(update.effective_user.id)
    if not user:
        await (q.message if q else update.message).reply_text("⚠️ ابتدا لاگین کنید (/start).")
        return ConversationHandler.END
    context.user_data["actor"] = user
    return ADD_BRAND

async def add_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["brand"] = update.message.text.strip()
    await update.message.reply_text("نام محصول را وارد کنید:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("توضیحات (یا 'no'):")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data["description"] = None if txt.lower() in ("no","-","") else txt
    await update.message.reply_text("تاریخ تولید (YYYY-MM-DD) یا 'no':")
    return ADD_MDATE

async def add_mdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data["manufacture_date"] = None if txt.lower() in ("no","-","") else txt
    await update.message.reply_text("تاریخ انقضا (YYYY-MM-DD) یا 'no':")
    return ADD_EDATE

async def add_edate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data["expire_date"] = None if txt.lower() in ("no","-","") else txt
    await update.message.reply_text("مقدار + واحد (مثال: 5 kg یا 10 pack):")
    return ADD_QTY

async def add_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quantity"] = update.message.text.strip()
    await update.message.reply_text("قیمت ورود (قیمت ورود به بازانو) را وارد کنید (عدد):")
    return ADD_PRICE_ENTRY

async def add_price_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        p = float(update.message.text.strip())
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر، لطفا عدد وارد کنید:")
        return ADD_PRICE_ENTRY
    context.user_data["price_entry"] = p
    # only admin/manager can set price_exit now; sellers cannot
    actor = context.user_data.get("actor")
    role = actor[3] if actor else None
    if role in ("admin","manager"):
        await update.message.reply_text("قیمت خروج (اختیاری) یا 'no':")
        return ADD_PRICE_EXIT
    else:
        context.user_data["price_exit"] = None
        return await add_save(update, context)

async def add_price_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    if txt in ("no","-",""):
        context.user_data["price_exit"] = None
    else:
        try:
            context.user_data["price_exit"] = float(txt)
        except:
            await update.message.reply_text("⚠️ مقدار نامعتبر. عدد یا 'no' وارد کنید:")
            return ADD_PRICE_EXIT
    return await add_save(update, context)

async def add_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brand = context.user_data.get("brand")
    name = context.user_data.get("name")
    description = context.user_data.get("description")
    mdate = context.user_data.get("manufacture_date")
    edate = context.user_data.get("expire_date")
    qty = context.user_data.get("quantity")
    pentry = context.user_data.get("price_entry")
    pexit = context.user_data.get("price_exit")
    cursor.execute("""INSERT INTO products (brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (brand, name, description, mdate, edate, qty, pentry, pexit))
    conn.commit()
    pid = cursor.lastrowid
    actor = context.user_data.get("actor")
    uid = actor[0] if actor else None
    add_log(uid, "ADD_PRODUCT", f"id={pid}, name={name}")
    await update.message.reply_text(f"✅ محصول ثبت شد (ID={pid}).", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# list & view
async def list_products_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split(":")
    page = int(parts[2])
    offset = page * PAGE_SIZE
    cursor.execute("SELECT id, brand, name, quantity, price_entry, price_exit FROM products ORDER BY id DESC LIMIT ? OFFSET ?", (PAGE_SIZE, offset))
    rows = cursor.fetchall()
    if not rows:
        await q.message.reply_text("📭 هیچ محصولی ثبت نشده است.")
        return
    text = "📋 لیست محصولات:\n\n"
    kb = []
    for r in rows:
        text += f"#{r[0]} — {r[1]} | {r[2]} | {r[3]} | ورود: {r[4]}\n"
        kb.append([InlineKeyboardButton(f"نمایش #{r[0]}", callback_data=f"products:view:{r[0]}")])
    cursor.execute("SELECT COUNT(*) FROM products")
    total = cursor.fetchone()[0]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"products:list:{page-1}"))
    if (page+1)*PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"products:list:{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main:menu")])
    await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def view_product_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pid = int(q.data.split(":")[2])
    cursor.execute("SELECT id, brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit FROM products WHERE id=?", (pid,))
    r = cursor.fetchone()
    if not r:
        await q.message.reply_text("⚠️ محصول یافت نشد.")
        return
    user = get_user_by_tg(q.from_user.id)
    role = user[3] if user else None
    text = f"📦 #{r[0]} — {r[1]} | {r[2]}\n\n📝 {r[3] or '-'}\n🏭 تولید: {r[4] or '-'}\n⌛ انقضا: {r[5] or '-'}\n⚖️ مقدار: {r[6]}\n💵 قیمت ورود: {r[7]}\n"
    if role in ("admin","manager"):
        text += f"💰 قیمت خروج: {r[8] if r[8] is not None else '-'}\n"
    else:
        text += "🔔 قیمت خروج فقط برای مدیر/ادمین نمایش داده می‌شود.\n"
    kb = [
        [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="products:list:0")],
    ]
    await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    add_log(user[0] if user else None, "VIEW_PRODUCT", f"product_id={pid}")

def get_product_handlers():
    handlers = []
    from telegram.ext import CallbackQueryHandler
    # product menu command
    handlers.append(CommandHandler("products", products_menu_cmd))
    # add conv
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_start_cb, pattern="^products:add$"), CommandHandler("add_product", products_menu_cmd)],
        states={
            ADD_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_brand)],
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_MDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_mdate)],
            ADD_EDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_edate)],
            ADD_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_qty)],
            ADD_PRICE_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price_entry)],
            ADD_PRICE_EXIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price_exit)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: (c.user_data.clear(), ReplyKeyboardRemove()))],
        allow_reentry=True
    )
    handlers.append(add_conv)
    handlers.append(CallbackQueryHandler(list_products_cb, pattern="^products:list:\d+$"))
    handlers.append(CallbackQueryHandler(view_product_cb, pattern="^products:view:\d+$"))
    return handlers
