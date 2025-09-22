# products.py
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from db import cursor, conn
from logs import add_log
from auth import sessions
from utils import now

# --- Conversation states ---
(
    ADD_BRAND, ADD_NAME, ADD_DESC, ADD_MDATE, ADD_EDATE, ADD_QTY, ADD_PRICE_ENTRY, ADD_PRICE_EXIT,
) = range(8)

(
    EDIT_SELECT_FIELD, EDIT_WAIT_VALUE,
) = range(100, 102)

# pagination page size
PAGE_SIZE = 10

# --- helpers ---
def get_user_role(tg_id):
    """
    returns (user_row, None) or (None, error_message)
    user_row = (id, firstname, lastname, phonenumber, role)
    """
    phone = sessions.get(tg_id)
    if not phone:
        return None, "⚠️ ابتدا وارد شوید (/start)."
    cursor.execute("SELECT id, firstname, lastname, phonenumber, role FROM users WHERE phonenumber=?", (phone,))
    user = cursor.fetchone()
    if not user:
        return None, "⚠️ کاربر در دیتابیس یافت نشد."
    return user, None

def format_product_row(row, role):
    """
    row: (id, brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit, created_by)
    role: string
    """
    pid, brand, name, desc, mdate, edate, qty, pentry, pexit, created_by = row
    lines = [
        f"📦 #{pid} — {brand} | {name}",
        f"📝 توضیحات: {desc or '-'}",
        f"🏭 تولید: {mdate or '-'}    ⏳ انقضا: {edate or '-'}",
        f"⚖️ مقدار: {qty or '-'}",
        f"💵 قیمت ورود (واحد): {pentry if pentry is not None else '-'}",
    ]
    if role in ("manager", "admin"):
        lines.append(f"💰 قیمت خروج: {pexit if pexit is not None else '-'}")
    else:
        # hint for seller
        lines.append("🔔 قیمت خروج فقط برای مدیر/ادمین قابل مشاهده است.")
    lines.append(f"🧾 ثبت‌شده توسط: user_id={created_by}")
    return "\n".join(lines)

# --- PRODUCTS MENU (inline) ---
async def products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # supports both message and callback
    if update.callback_query:
        cq = update.callback_query
        await cq.answer()
        chat = cq.message
        send = chat.reply_text
    else:
        send = update.message.reply_text

    user, err = get_user_role(update.effective_user.id)
    if err:
        await send(err)
        return

    kb = [
        [InlineKeyboardButton("➕ افزودن محصول", callback_data="add_product")],
        [InlineKeyboardButton("📋 لیست محصولات", callback_data="list_prod:0")],
        [InlineKeyboardButton("❌ بستن", callback_data="close_products")],
    ]
    await send("📦 منوی محصولات — یک گزینه انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

# --- ADD PRODUCT (Conversation) ---
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # entry point can be command or callback
    if update.callback_query:
        cq = update.callback_query
        await cq.answer()
        await cq.message.reply_text("📦 شروع افزودن محصول (لغو: /cancel)")
    else:
        await update.message.reply_text("📦 شروع افزودن محصول (لغو: /cancel)")

    user, err = get_user_role(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return ConversationHandler.END

    # keep actor info
    context.user_data["actor_id"] = user[0]
    context.user_data["actor_role"] = user[4]

    await update.effective_chat.send_message("🏷 لطفاً برند محصول را وارد کنید:")
    return ADD_BRAND

async def add_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["brand"] = update.message.text.strip()
    await update.message.reply_text("📦 نام محصول را وارد کنید:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("📝 توضیحات محصول را وارد کنید (یا 'no'):")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data["description"] = None if txt.lower() in ("no", "-", "") else txt
    await update.message.reply_text("🏭 تاریخ تولید (YYYY-MM-DD) یا 'no':")
    return ADD_MDATE

async def add_mdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data["manufacture_date"] = None if txt.lower() in ("no", "-", "") else txt
    await update.message.reply_text("⌛ تاریخ انقضا (YYYY-MM-DD) یا 'no':")
    return ADD_EDATE

async def add_edate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    context.user_data["expire_date"] = None if txt.lower() in ("no", "-", "") else txt
    await update.message.reply_text("⚖️ مقدار + واحد (مثال: 5 kg یا 10 بسته):")
    return ADD_QTY

async def add_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quantity"] = update.message.text.strip()
    role = context.user_data.get("actor_role")
    if role == "seller":
        prompt = "💵 قیمت ورود (قیمت وارد شدن کالای شما به بازانو؛ قیمت واحد را وارد نمایید):"
    else:
        prompt = ("💵 قیمت ورود (این قیمت، قیمت ورود به بازانو است و باید قیمت خروج در مراحل خرید ثبت شود).\n"
                  "🔔 لطفاً قیمت واحد را وارد نمایید:")
    await update.message.reply_text(prompt)
    return ADD_PRICE_ENTRY

async def add_price_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        context.user_data["price_entry"] = float(txt)
    except:
        await update.message.reply_text("⚠️ مقدار قیمت نامعتبر است. دوباره عدد وارد کنید:")
        return ADD_PRICE_ENTRY

    role = context.user_data.get("actor_role")
    if role in ("manager", "admin"):
        await update.message.reply_text("💰 (اختیاری) قیمت خروج را وارد کنید یا 'no':")
        return ADD_PRICE_EXIT
    else:
        context.user_data["price_exit"] = None
        # proceed to save
        return await add_product_save(update, context)

async def add_price_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    if txt in ("no", "-", ""):
        context.user_data["price_exit"] = None
    else:
        try:
            context.user_data["price_exit"] = float(txt)
        except:
            await update.message.reply_text("⚠️ مقدار قیمت خروج نامعتبر است، عدد یا 'no' وارد کنید:")
            return ADD_PRICE_EXIT

    return await add_product_save(update, context)

async def add_product_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    actor_id = context.user_data.get("actor_id")
    brand = context.user_data.get("brand")
    name = context.user_data.get("name")
    description = context.user_data.get("description")
    mdate = context.user_data.get("manufacture_date")
    edate = context.user_data.get("expire_date")
    qty = context.user_data.get("quantity")
    pentry = context.user_data.get("price_entry")
    pexit = context.user_data.get("price_exit")

    cursor.execute("""
        INSERT INTO products (brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (brand, name, description, mdate, edate, qty, pentry, pexit, actor_id))
    conn.commit()
    pid = cursor.lastrowid
    add_log(actor_id, "ADD_PRODUCT", f"product_id={pid} name={name}")

    await update.message.reply_text(f"✅ محصول ثبت شد (id={pid}).", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- LIST PRODUCTS (paginated) ---
async def list_products_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # callback pattern list_prod:{page}
    cq = update.callback_query
    await cq.answer()
    data = cq.data  # ex: list_prod:0
    try:
        _, page_s = data.split(":")
        page = int(page_s)
    except:
        page = 0
    await send_products_list(cq.message, update.effective_user.id, page)

async def send_products_list(message_or_obj, tg_id, page=0):
    # message_or_obj: Message or CallbackQuery.message
    # use tg_id to determine role
    user, err = get_user_role(tg_id)
    if err:
        await message_or_obj.reply_text(err)
        return
    role = user[4]

    offset = page * PAGE_SIZE
    cursor.execute("SELECT id, brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit, created_by FROM products ORDER BY id DESC LIMIT ? OFFSET ?", (PAGE_SIZE, offset))
    rows = cursor.fetchall()

    if not rows:
        await message_or_obj.reply_text("📭 محصولی برای نمایش وجود ندارد.")
        return

    text_lines = []
    for r in rows:
        text_lines.append(f"#{r[0]} — {r[1]} | {r[2]}  ({r[6]})")

    text = "📋 محصولات:\n\n" + "\n".join(text_lines)
    # create inline buttons for each product (view)
    kb = []
    for r in rows:
        pid = r[0]
        kb.append([InlineKeyboardButton(f"نمایش #{pid}", callback_data=f"view_prod:{pid}")])

    # pagination buttons
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"list_prod:{page-1}"))
    # check if more exist
    cursor.execute("SELECT COUNT(*) FROM products")
    total = cursor.fetchone()[0]
    max_page = (total - 1) // PAGE_SIZE
    if page < max_page:
        nav.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"list_prod:{page+1}"))
    if nav:
        kb.append(nav)

    kb.append([InlineKeyboardButton("🔙 بستن", callback_data="close_products")])
    await message_or_obj.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

# --- VIEW product ---
async def view_product_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    try:
        _, pid_s = cq.data.split(":")
        pid = int(pid_s)
    except:
        await cq.message.reply_text("خطا در شناسه محصول.")
        return

    cursor.execute("SELECT id, brand, name, description, manufacture_date, expire_date, quantity, price_entry, price_exit, created_by FROM products WHERE id=?", (pid,))
    row = cursor.fetchone()
    if not row:
        await cq.message.reply_text("محصول یافت نشد.")
        return

    user, err = get_user_role(update.effective_user.id)
    if err:
        await cq.message.reply_text(err)
        return
    role = user[4]

    text = format_product_row(row, role)
    # buttons: Edit, Delete, Back to list
    kb = [
        [
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_prod:{pid}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"del_prod:{pid}"),
        ],
        [InlineKeyboardButton("🔙 بازگشت به فهرست", callback_data="list_prod:0")],
    ]
    await cq.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    add_log(user[0], "VIEW_PRODUCT", f"product_id={pid}")

# --- DELETE product (confirm) ---
async def del_product_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    _, pid_s = cq.data.split(":")
    pid = int(pid_s)
    # show confirm
    kb = [
        [InlineKeyboardButton("✅ تایید حذف", callback_data=f"confirm_del:{pid}")],
        [InlineKeyboardButton("❌ انصراف", callback_data=f"view_prod:{pid}")],
    ]
    await cq.message.reply_text(f"⚠️ آیا از حذف محصول #{pid} اطمینان دارید؟", reply_markup=InlineKeyboardMarkup(kb))

async def confirm_del_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    _, pid_s = cq.data.split(":")
    pid = int(pid_s)
    # perform delete
    cursor.execute("SELECT created_by FROM products WHERE id=?", (pid,))
    row = cursor.fetchone()
    if not row:
        await cq.message.reply_text("محصولی برای حذف یافت نشد.")
        return
    # delete
    cursor.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    # log by actor (who pressed)
    user, _ = get_user_role(update.effective_user.id)
    add_log(user[0], "DELETE_PRODUCT", f"product_id={pid}")
    await cq.message.reply_text(f"🗑 محصول #{pid} حذف شد.")

# --- EDIT product (Conversation started by callback) ---
async def edit_product_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    _, pid_s = cq.data.split(":")
    pid = int(pid_s)
    context.user_data["edit_product_id"] = pid

    # present editable fields (price_exit only for admin/manager)
    user, err = get_user_role(update.effective_user.id)
    if err:
        await cq.message.reply_text(err)
        return ConversationHandler.END
    role = user[4]

    kb = [
        [InlineKeyboardButton("برند", callback_data=f"edit_field:brand:{pid}"),
         InlineKeyboardButton("نام", callback_data=f"edit_field:name:{pid}")],
        [InlineKeyboardButton("توضیحات", callback_data=f"edit_field:description:{pid}"),
         InlineKeyboardButton("تاریخ تولید", callback_data=f"edit_field:manufacture_date:{pid}")],
        [InlineKeyboardButton("تاریخ انقضا", callback_data=f"edit_field:expire_date:{pid}"),
         InlineKeyboardButton("مقدار", callback_data=f"edit_field:quantity:{pid}")],
        [InlineKeyboardButton("قیمت ورود", callback_data=f"edit_field:price_entry:{pid}")]
    ]
    # add price_exit only for manager/admin
    if role in ("manager", "admin"):
        kb[-1].append(InlineKeyboardButton("قیمت خروج", callback_data=f"edit_field:price_exit:{pid}"))

    kb.append([InlineKeyboardButton("✅ اتمام / بازگشت", callback_data=f"view_prod:{pid}")])
    await cq.message.reply_text("🔧 فیلد مورد نظر برای ویرایش را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
    return EDIT_SELECT_FIELD

async def edit_field_selected_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    # data: edit_field:FIELD:pid
    try:
        _, field, pid_s = cq.data.split(":")
    except:
        await cq.message.reply_text("خطا در درخواست ویرایش.")
        return ConversationHandler.END
    pid = int(pid_s)
    context.user_data["edit_product_id"] = pid
    context.user_data["edit_field"] = field

    await cq.message.reply_text(f"✍️ لطفاً مقدار جدید برای فیلد `{field}` را ارسال کنید:", parse_mode="Markdown")
    return EDIT_WAIT_VALUE

async def edit_receive_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_row, err = get_user_role(update.effective_user.id)
    if err:
        await update.message.reply_text(err)
        return ConversationHandler.END
    actor_id = user_row[0]

    field = context.user_data.get("edit_field")
    pid = context.user_data.get("edit_product_id")
    if not field or not pid:
        await update.message.reply_text("خطا: اطلاعات ویرایش نامشخص است.")
        return ConversationHandler.END

    new_val = update.message.text.strip()
    # validation for numeric fields
    if field in ("price_entry", "price_exit"):
        try:
            new_val_db = float(new_val)
        except:
            await update.message.reply_text("⚠️ مقدار نامعتبر است، لطفاً عدد وارد کنید.")
            return EDIT_WAIT_VALUE
    else:
        new_val_db = new_val

    # update DB
    cursor.execute(f"UPDATE products SET {field}=? WHERE id=?", (new_val_db, pid))
    conn.commit()
    add_log(actor_id, "EDIT_PRODUCT", f"product_id={pid} field={field} new={new_val}")

    await update.message.reply_text(f"✅ فیلد `{field}` برای محصول #{pid} با مقدار جدید ذخیره شد.", parse_mode="Markdown")
    # go back to edit menu for same product
    # rebuild keyboard
    role = user_row[4]
    kb = [
        [InlineKeyboardButton("برند", callback_data=f"edit_field:brand:{pid}"),
         InlineKeyboardButton("نام", callback_data=f"edit_field:name:{pid}")],
        [InlineKeyboardButton("توضیحات", callback_data=f"edit_field:description:{pid}"),
         InlineKeyboardButton("تاریخ تولید", callback_data=f"edit_field:manufacture_date:{pid}")],
        [InlineKeyboardButton("تاریخ انقضا", callback_data=f"edit_field:expire_date:{pid}"),
         InlineKeyboardButton("مقدار", callback_data=f"edit_field:quantity:{pid}")],
        [InlineKeyboardButton("قیمت ورود", callback_data=f"edit_field:price_entry:{pid}")]
    ]
    if role in ("manager", "admin"):
        kb[-1].append(InlineKeyboardButton("قیمت خروج", callback_data=f"edit_field:price_exit:{pid}"))
    kb.append([InlineKeyboardButton("✅ اتمام / بازگشت", callback_data=f"view_prod:{pid}")])
    await update.message.reply_text("🔧 انتخاب بعدی یا بازگشت به نمایش محصول:", reply_markup=InlineKeyboardMarkup(kb))
    return EDIT_SELECT_FIELD

# --- CLOSE handler ---
async def close_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # close products menu (for callbacks)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.delete()

# --- register handlers getter ---
def get_product_handlers():
    handlers = []

    # products menu (command + callback)
    handlers.append(CommandHandler("products_menu", products_menu))
    handlers.append(CallbackQueryHandler(products_menu, pattern="^products_menu$"))

    # callback to open add_product via button
    # Conversation for add product: entry from command or callback
    add_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add_product", add_product_start),
            CallbackQueryHandler(add_product_start, pattern="^add_product$"),
        ],
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
        fallbacks=[CommandHandler("cancel", lambda u,c: (await_cancel(u,c)))],
        allow_reentry=True,
    )
    handlers.append(add_conv)

    # list products (callback pages)
    handlers.append(CallbackQueryHandler(list_products_cb, pattern="^list_prod:\d+$"))

    # view product
    handlers.append(CallbackQueryHandler(view_product_cb, pattern="^view_prod:\d+$"))

    # delete product confirm
    handlers.append(CallbackQueryHandler(del_product_cb, pattern="^del_prod:\d+$"))
    handlers.append(CallbackQueryHandler(confirm_del_cb, pattern="^confirm_del:\d+$"))

    # edit product conversation: entry via callback edit_prod:id
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_product_start_cb, pattern="^edit_prod:\d+$")],
        states={
            EDIT_SELECT_FIELD: [CallbackQueryHandler(edit_field_selected_cb, pattern="^edit_field:")],
            EDIT_WAIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_receive_value)],
        },
        fallbacks=[CallbackQueryHandler(lambda u,c: (await_cancel_cb(u,c)), pattern="^view_prod:\d+$")],
        allow_reentry=True,
    )
    handlers.append(edit_conv)

    # close products menu
    handlers.append(CallbackQueryHandler(close_cb, pattern="^close_products$"))

    return handlers

# --- small helpers for async lambda fallbacks (since inline lambda can't await directly) ---
async def await_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def await_cancel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if callback provided, answer and end conv
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("❌ عملیات ویرایش لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
