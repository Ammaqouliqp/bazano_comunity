# products.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, ContextTypes, filters
)
from db import cursor, conn
from logs import add_log
from auth import sessions

# states for add product
(ADD_BRAND, ADD_NAME, ADD_DESC, ADD_MDATE, ADD_EDATE, ADD_QTY, ADD_PRICE_ENTRY, ADD_PRICE_EXIT) = range(8)
# states for edit
(EDIT_WAIT_VALUE,) = range(100, 101)
PAGE_SIZE = 8

def get_user_by_tg(tg_id):
    phone = sessions.get(tg_id)
    if not phone:
        return None
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    return cursor.fetchone()

# menu
async def products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # support both command and callback
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.message

    user = get_user_by_tg(update.effective_user.id)
    if not user:
        await target.reply_text("⚠️ لطفاً ابتدا /start کنید و وارد شوید.")
        return

    kb = [
        [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
        [InlineKeyboardButton("📋 لیست محصولات", callback_data="products:list:0")],
        [InlineKeyboardButton("📥 درخواست محصول (مشترک)", callback_data="common:request")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="common:back")],
    ]
    await target.reply_text("📦 منوی محصولات:", reply_markup=InlineKeyboardMarkup(kb))

# add product flow
async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("➕ شروع افزودن محصول (برای لغو /cancel):")
    else:
        await update.message.reply_text("➕ شروع افزودن محصول (برای لغو /cancel):")

    user = get_user_by_tg(update.effective_user.id)
    if not user:
        await update.message.reply_text("⚠️ ابتدا وارد شوید.")
        return ConversationHandler.END
    context.user_data['actor'] = user
    await update.effective_chat.send_message("🏷 لطفاً برند محصول را وارد کنید:")
    return ADD_BRAND

async def add_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['brand'] = update.message.text.strip()
    await update.message.reply_text("📦 نام محصول را وارد کنید:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("📝 توضیحات (یا 'no'):")
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
    await update.message.reply_text("⚖️ مقدار + واحد (مثال: 5 kg یا 10 بسته):")
    return ADD_QTY

async def add_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['quantity'] = update.message.text.strip()
    role = context.user_data['actor'][3]
    if role == "seller":
        await update.message.reply_text("💵 قیمت ورود (این قیمت وارد شدن کالای شما به بازانو است). لطفاً عدد وارد کنید:")
    else:
        await update.message.reply_text("💵 قیمت ورود (این قیمت، قیمت ورود به بازانو است). لطفاً قیمت واحد را وارد کنید:")
    return ADD_PRICE_ENTRY

async def add_price_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        context.user_data['price_entry'] = float(txt)
    except:
        await update.message.reply_text("⚠️ مقدار نامعتبر. لطفاً عدد وارد کنید:")
        return ADD_PRICE_ENTRY

    role = context.user_data['actor'][3]
    if role in ("admin", "manager"):
        await update.message.reply_text("💰 (اختیاری) قیمت خروج را وارد کنید یا 'no':")
        return ADD_PRICE_EXIT
    # seller path -> price_exit set None
    context.user_data['price_exit'] = None
    return await add_save(update, context)

async def add_price_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    if txt in ("no", "-", ""):
        context.user_data['price_exit'] = None
    else:
        try:
            context.user_data['price_exit'] = float(txt)
        except:
            await update.message.reply_text("⚠️ مقدار نامعتبر. عدد یا 'no' وارد کنید:")
            return ADD_PRICE_EXIT
    return await add_save(update, context)

async def add_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brand = context.user_data.get('brand')
    name = context.user_data.get('name')
    description = context.user_data.get('description')
    mdate = context.user_data.get('manufacture_date')
    edate = context.user_data.get('expire_date')
    qty = context.user_data.get('quantity')
    pentry = context.user_data.get('price_entry')
    pexit = context.user_data.get('price_exit')

    cursor.execute("""
        INSERT INTO products (brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (brand, name, description, mdate, edate, qty, pentry, pexit))
    conn.commit()
    pid = cursor.lastrowid
    actor = context.user_data.get('actor')
    uid = actor[0] if actor else None
    add_log(uid, "ADD_PRODUCT", f"product_id={pid} name={name}")
    await update.message.reply_text(f"✅ محصول ثبت شد (ID={pid}).", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# list (paginated)
async def list_products_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    parts = cq.data.split(":")
    page = int(parts[2])
    await send_products_list(cq.message, cq.from_user.id, page)

async def send_products_list(message, tg_id, page=0):
    user = get_user_by_tg(tg_id)
    if not user:
        await message.reply_text("⚠️ ابتدا وارد شوید.")
        return
    role = user[3]
    offset = page * PAGE_SIZE
    cursor.execute("SELECT id, brand, name, quantity, price_entry, price_exit FROM products ORDER BY id DESC LIMIT ? OFFSET ?", (PAGE_SIZE, offset))
    rows = cursor.fetchall()
    if not rows:
        await message.reply_text("📭 هیچ محصولی ثبت نشده است.")
        return
    lines = []
    kb = []
    for r in rows:
        lines.append(f"#{r[0]} — {r[1]} | {r[2]} ({r[3]})")
        kb.append([InlineKeyboardButton(f"نمایش #{r[0]}", callback_data=f"products:view:{r[0]}")])
    # pagination
    cursor.execute("SELECT COUNT(*) FROM products")
    total = cursor.fetchone()[0]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"products:list:{page-1}"))
    if (page+1)*PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"products:list:{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="products:menu")])
    await message.reply_text("📋 لیست محصولات:\n\n" + "\n".join(lines), reply_markup=InlineKeyboardMarkup(kb))

# view
async def view_product_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    pid = int(cq.data.split(":")[2])
    cursor.execute("SELECT id, brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit FROM products WHERE id=?", (pid,))
    r = cursor.fetchone()
    if not r:
        await cq.message.reply_text("⚠️ محصول یافت نشد.")
        return
    user = get_user_by_tg(cq.from_user.id)
    role = user[3] if user else None
    text = f"📦 #{r[0]} — {r[1]} | {r[2]}\n\n📝 {r[3] or '-'}\n🏭 تولید: {r[4] or '-'}\n⌛ انقضا: {r[5] or '-'}\n⚖️ مقدار: {r[6]}\n💵 قیمت ورود: {r[7]}\n"
    if role in ("admin", "manager"):
        text += f"💰 قیمت خروج: {r[8] if r[8] is not None else '-'}\n"
    else:
        text += "🔔 قیمت خروج فقط برای مدیر/ادمین نمایش داده می‌شود.\n"
    kb = [
        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"products:edit:{pid}"), InlineKeyboardButton("🗑 حذف", callback_data=f"products:del:{pid}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="products:list:0")],
    ]
    await cq.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    add_log(user[0] if user else None, "VIEW_PRODUCT", f"product_id={pid}")

# delete
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
    user = get_user_by_tg(cq.from_user.id)
    uid = user[0] if user else None
    cursor.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    add_log(uid, "DELETE_PRODUCT", f"product_id={pid}")
    await cq.message.reply_text(f"🗑 محصول #{pid} حذف شد.")

# edit flow
async def edit_entry_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    pid = int(cq.data.split(":")[2])
    context.user_data['edit_pid'] = pid
    user = get_user_by_tg(cq.from_user.id)
    role = user[3] if user else None
    kb = [
        [InlineKeyboardButton("برند", callback_data=f"products:edit_field:brand:{pid}"), InlineKeyboardButton("نام", callback_data=f"products:edit_field:name:{pid}")],
        [InlineKeyboardButton("توضیحات", callback_data=f"products:edit_field:description:{pid}"), InlineKeyboardButton("تاریخ تولید", callback_data=f"products:edit_field:manufacture_date:{pid}")],
        [InlineKeyboardButton("تاریخ انقضا", callback_data=f"products:edit_field:expire_date:{pid}"), InlineKeyboardButton("مقدار", callback_data=f"products:edit_field:quantity:{pid}")],
        [InlineKeyboardButton("قیمت ورود", callback_data=f"products:edit_field:price_entry:{pid}")]
    ]
    if role in ("admin", "manager"):
        kb[-1].append(InlineKeyboardButton("قیمت خروج", callback_data=f"products:edit_field:price_exit:{pid}"))
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"products:view:{pid}")])
    await cq.message.reply_text("🔧 فیلد مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
    return EDIT_WAIT_VALUE

async def edit_field_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    parts = cq.data.split(":")
    field = parts[3]
    pid = int(parts[4])
    context.user_data['edit_field'] = field
    context.user_data['edit_pid'] = pid
    await cq.message.reply_text(f"✍️ مقدار جدید برای `{field}` را ارسال کنید:", parse_mode="Markdown")
    return EDIT_WAIT_VALUE

async def edit_value_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data.get('edit_field')
    pid = context.user_data.get('edit_pid')
    user = get_user_by_tg(update.effective_user.id)
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
            return EDIT_WAIT_VALUE
    else:
        newd = new
    cursor.execute(f"UPDATE products SET {field}=? WHERE id=?", (newd, pid))
    conn.commit()
    add_log(uid, "EDIT_PRODUCT", f"product_id={pid} field={field} new={newd}")
    await update.message.reply_text("✅ مقدار ذخیره شد.")
    return ConversationHandler.END

# menu navigation callbacks
async def products_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    await products_menu(update, context)

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
    handlers.append(CallbackQueryHandler(products_menu_cb, pattern="^products:menu$|^products_menu$"))
    # add product conv
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add_product", add_product), CallbackQueryHandler(add_product, pattern="^products:add$")],
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
    handlers.append(CallbackQueryHandler(del_product_cb, pattern="^products:del:\d+$"))
    handlers.append(CallbackQueryHandler(del_confirm_cb, pattern="^products:del_confirm:\d+$"))
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_entry_cb, pattern="^products:edit:\d+$")],
        states={
            EDIT_WAIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_received)]
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: (c.user_data.clear(), ReplyKeyboardRemove()))],
        allow_reentry=True
    )
    handlers.append(edit_conv)
    handlers.append(CallbackQueryHandler(products_close_cb, pattern="^products:close$"))
    handlers.append(CallbackQueryHandler(products_close_cb, pattern="^products:menu$"))
    return handlers
