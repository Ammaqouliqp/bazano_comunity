# products.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, ContextTypes, filters
)
from db import cursor, conn
from logs import add_log
from auth import sessions

# states
(ADD_BRAND, ADD_NAME, ADD_DESC, ADD_MDATE, ADD_EDATE, ADD_QTY, ADD_PRICE_ENTRY, ADD_PRICE_EXIT) = range(8)
(EDIT_SELECT, EDIT_VALUE) = range(100, 102)
PAGE_SIZE = 8

def get_user(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

# products menu
async def products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # support command or callback
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.message

    user = get_user(update.effective_user.id)
    if not user:
        await target.reply_text("⚠️ لطفاً ابتدا /start کنید و وارد شوید.")
        return

    kb = [
        [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
        [InlineKeyboardButton("📋 لیست محصولات", callback_data="products:list:0")],
        [InlineKeyboardButton("❌ بستن", callback_data="products:close")]
    ]
    await target.reply_text("📦 منوی محصولات:", reply_markup=InlineKeyboardMarkup(kb))

# add product conv
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("➕ شروع افزودن محصول (برای لغو /cancel):")
    else:
        await update.message.reply_text("➕ شروع افزودن محصول (برای لغو /cancel):")
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ ابتدا وارد شوید.")
        return ConversationHandler.END
    context.user_data['actor'] = user
    await update.effective_chat.send_message("🏷 برند را وارد کنید:")
    return ADD_BRAND

async def add_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['brand'] = update.message.text.strip()
    await update.message.reply_text("📛 نام محصول را وارد کنید:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("📝 توضیحات را وارد کنید یا 'no':")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data['description'] = None if txt.lower() in ("no", "-", "") else txt
    await update.message.reply_text("🏭 تاریخ تولید (YYYY-MM-DD) یا 'no':")
    return ADD_MDATE

async def add_mdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data['manufacture_date'] = None if txt.lower() in ("no", "-", "") else txt
    await update.message.reply_text("⌛ تاریخ انقضا (YYYY-MM-DD) یا 'no':")
    return ADD_EDATE

async def add_edate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data['expire_date'] = None if txt.lower() in ("no", "-", "") else txt
    await update.message.reply_text("⚖️ مقدار + واحد (مثال: 5 kg):")
    return ADD_QTY

async def add_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['quantity'] = update.message.text.strip()
    role = context.user_data['actor'][3]  # role
    if role == "seller":
        await update.message.reply_text("💵 قیمت ورود (این قیمت ورود کالای شما به بازانو است). لطفاً عدد وارد کنید:")
    else:
        await update.message.reply_text("💵 قیمت ورود (این قیمت، قیمت ورود به بازانو است). لطفاً قیمت واحد را وارد کنید:")
    return ADD_PRICE_ENTRY

async def add_price_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.strip())
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر، عدد وارد کنید:")
        return ADD_PRICE_ENTRY
    context.user_data['price_entry'] = val
    role = context.user_data['actor'][3]
    if role in ("admin", "manager"):
        await update.message.reply_text("💰 (اختیاری) قیمت خروج را وارد کنید یا 'no':")
        return ADD_PRICE_EXIT
    # seller path
    context.user_data['price_exit'] = None
    # save
    return await add_save(update, context)

async def add_price_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    if txt in ("no", "-", ""):
        context.user_data['price_exit'] = None
    else:
        try:
            context.user_data['price_exit'] = float(txt)
        except:
            await update.message.reply_text("⚠️ مقدار نامعتبر، عدد یا 'no' وارد کنید:")
            return ADD_PRICE_EXIT
    return await add_save(update, context)

async def add_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    actor = context.user_data['actor']
    user_id = actor[0]
    cursor.execute("""
        INSERT INTO products (brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        context.user_data.get('brand'),
        context.user_data.get('name'),
        context.user_data.get('description'),
        context.user_data.get('manufacture_date'),
        context.user_data.get('expire_date'),
        context.user_data.get('quantity'),
        context.user_data.get('price_entry'),
        context.user_data.get('price_exit'),
        user_id
    ))
    conn.commit()
    pid = cursor.lastrowid
    add_log(user_id, "ADD_PRODUCT", f"product_id={pid} name={context.user_data.get('name')}")
    await update.message.reply_text(f"✅ محصول ثبت شد (ID={pid}).", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# list products (paginated)
async def list_products_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    parts = cq.data.split(":")
    page = int(parts[2])
    await send_products_list(cq.message, cq.from_user.id, page)

async def send_products_list(message, tg_id, page=0):
    user = get_user(tg_id)
    if not user:
        await message.reply_text("⚠️ ابتدا وارد شوید.")
        return
    role = user[3]
    offset = page * PAGE_SIZE
    cursor.execute("SELECT id, brand, name, quantity, price_entry, price_exit, created_by FROM products ORDER BY id DESC LIMIT ? OFFSET ?", (PAGE_SIZE, offset))
    rows = cursor.fetchall()
    if not rows:
        await message.reply_text("📭 هیچ محصولی برای نمایش وجود ندارد.")
        return
    lines = []
    kb = []
    for r in rows:
        lines.append(f"#{r[0]} — {r[1]} | {r[2]} ({r[3]})")
        kb.append([InlineKeyboardButton(f"نمایش #{r[0]}", callback_data=f"products:view:{r[0]}")])
    # pagination nav
    cursor.execute("SELECT COUNT(*) FROM products")
    total = cursor.fetchone()[0]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"products:list:{page-1}"))
    if (page+1)*PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"products:list:{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton("🔙 بستن", callback_data="products:close")])
    await message.reply_text("📋 لیست محصولات:\n\n" + "\n".join(lines), reply_markup=InlineKeyboardMarkup(kb))

# view product
async def view_product_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    parts = cq.data.split(":")
    pid = int(parts[2])
    cursor.execute("SELECT id, brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit, created_by FROM products WHERE id=?", (pid,))
    r = cursor.fetchone()
    if not r:
        await cq.message.reply_text("⚠️ محصول یافت نشد.")
        return
    user = get_user(cq.from_user.id)
    role = user[3] if user else None
    text = f"📦 #{r[0]} — {r[1]} | {r[2]}\n\n📝 {r[3] or '-'}\n🏭 تولید: {r[4] or '-'}\n⌛ انقضا: {r[5] or '-'}\n⚖️ مقدار: {r[6]}\n💵 قیمت ورود: {r[7]}\n"
    if role in ("admin","manager"):
        text += f"💰 قیمت خروج: {r[8] or '-'}\n"
    else:
        text += "🔔 قیمت خروج فقط برای مدیر/ادمین قابل مشاهده است.\n"
    kb = [
        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"products:edit:{pid}"),
         InlineKeyboardButton("🗑 حذف", callback_data=f"products:del:{pid}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="products:list:0")]
    ]
    await cq.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    add_log(user[0] if user else None, "VIEW_PRODUCT", f"product_id={pid}")

# delete product confirm
async def del_product_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    pid = int(cq.data.split(":")[2])
    kb = [
        [InlineKeyboardButton("✅ تایید حذف", callback_data=f"products:del_confirm:{pid}")],
        [InlineKeyboardButton("❌ انصراف", callback_data=f"products:view:{pid}")]
    ]
    await cq.message.reply_text(f"⚠️ آیا از حذف محصول #{pid} اطمینان دارید؟", reply_markup=InlineKeyboardMarkup(kb))

async def del_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    pid = int(cq.data.split(":")[2])
    user = get_user(cq.from_user.id)
    uid = user[0] if user else None
    cursor.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    add_log(uid, "DELETE_PRODUCT", f"product_id={pid}")
    await cq.message.reply_text(f"🗑 محصول #{pid} حذف شد.")

# edit product: entry -> show fields -> accept new value
async def edit_entry_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    pid = int(cq.data.split(":")[2])
    context.user_data['edit_pid'] = pid
    user = get_user(cq.from_user.id)
    role = user[3] if user else None
    kb = [
        [InlineKeyboardButton("برند", callback_data=f"products:edit_field:brand:{pid}"),
         InlineKeyboardButton("نام", callback_data=f"products:edit_field:name:{pid}")],
        [InlineKeyboardButton("توضیحات", callback_data=f"products:edit_field:description:{pid}"),
         InlineKeyboardButton("تاریخ تولید", callback_data=f"products:edit_field:manufacture_date:{pid}")],
        [InlineKeyboardButton("تاریخ انقضا", callback_data=f"products:edit_field:expire_date:{pid}"),
         InlineKeyboardButton("مقدار", callback_data=f"products:edit_field:quantity:{pid}")],
        [InlineKeyboardButton("قیمت ورود", callback_data=f"products:edit_field:price_entry:{pid}")]
    ]
    if role in ("admin","manager"):
        kb[-1].append(InlineKeyboardButton("قیمت خروج", callback_data=f"products:edit_field:price_exit:{pid}"))
    kb.append([InlineKeyboardButton("✅ اتمام / بازگشت", callback_data=f"products:view:{pid}")])
    await cq.message.reply_text("🔧 فیلد مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
    return EDIT_SELECT

async def edit_field_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    parts = cq.data.split(":")
    field = parts[3]
    pid = int(parts[4])
    context.user_data['edit_field'] = field
    await cq.message.reply_text(f"✍️ مقدار جدید برای `{field}` را ارسال کنید:", parse_mode="Markdown")
    return EDIT_VALUE

async def edit_value_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data.get('edit_field')
    pid = context.user_data.get('edit_pid')
    user = get_user(update.effective_user.id)
    uid = user[0] if user else None
    if not field or not pid:
        await update.message.reply_text("⚠️ خطا در اطلاعات ویرایش.")
        return ConversationHandler.END
    new = update.message.text.strip()
    if field in ("price_entry", "price_exit"):
        try:
            newd = float(new)
        except:
            await update.message.reply_text("⚠️ مقدار نامعتبر. از عدد استفاده کنید.")
            return EDIT_VALUE
    else:
        newd = new
    cursor.execute(f"UPDATE products SET {field}=? WHERE id=?", (newd, pid))
    conn.commit()
    add_log(uid, "EDIT_PRODUCT", f"product_id={pid} field={field}")
    await update.message.reply_text("✅ مقدار ذخیره شد.")
    return ConversationHandler.END

# close products
async def products_close_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except:
            pass

def get_product_handlers():
    handlers = []
    handlers.append(CommandHandler("products_menu", products_menu))
    handlers.append(CallbackQueryHandler(products_menu, pattern="^products_menu$"))
    # add conversation
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add_product", add_start), CallbackQueryHandler(add_start, pattern="^products:add$")],
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
    # list
    handlers.append(CallbackQueryHandler(list_products_cb, pattern="^products:list:\d+$"))
    handlers.append(CallbackQueryHandler(view_product_cb, pattern="^products:view:\d+$"))
    handlers.append(CallbackQueryHandler(del_product_cb, pattern="^products:del:\d+$"))
    handlers.append(CallbackQueryHandler(del_confirm_cb, pattern="^products:del_confirm:\d+$"))
    # edit conversation
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_entry_cb, pattern="^products:edit:\d+$")],
        states={
            EDIT_SELECT: [CallbackQueryHandler(edit_field_cb, pattern="^products:edit_field:")],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_received)]
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: (c.user_data.clear(), ReplyKeyboardRemove()))],
        allow_reentry=True
    )
    handlers.append(edit_conv)
    handlers.append(CallbackQueryHandler(products_close_cb, pattern="^products:close$"))
    return handlers
