# menus/menu_utils.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from db import cursor
from logs import add_log

# build help text and markup per role
def build_help_buttons(role):
    # buyer menu text
    buyer_buttons = [
        [InlineKeyboardButton("🛍 خریدهای من", callback_data="buyer:my_purchases")],
        [InlineKeyboardButton("📝 ثبت نظر", callback_data="buyer:feedback")],
        [InlineKeyboardButton("📩 پشتیبانی", callback_data="buyer:support")],
        [InlineKeyboardButton("💡 انتقاد/پیشنهاد", callback_data="buyer:suggest")],
        [InlineKeyboardButton("📥 درخواست محصول", callback_data="common:request")],
    ]

    # role-specific
    role_buttons = []
    if role == "seller":
        role_buttons = [
            [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
            [InlineKeyboardButton("📦 محصولات من", callback_data="seller:my_products")],
        ]
    elif role == "manager":
        role_buttons = [
            [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
            [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:manage_products")],
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="manager:users")],
        ]
    elif role == "admin":
        role_buttons = [
            [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:manage_products")],
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin:users")],
            [InlineKeyboardButton("📜 لاگ‌ها", callback_data="admin:logs")],
        ]
    elif role == "dev":
        role_buttons = [
            [InlineKeyboardButton("⚙️ Debug Tools", callback_data="dev:menu")],
            [InlineKeyboardButton("📜 لاگ‌ها (Dev)", callback_data="dev:logs")],
        ]

    # Compose final text and markup
    text = "📖 منوی راهنما:\n\n"
    text += "— منوی خریدار —\n"
    text += "🛍 خریدهای من\n📝 ثبت نظر\n📩 پشتیبانی\n💡 انتقاد/پیشنهاد\n📥 درخواست محصول\n\n"
    if role and role != "buyer":
        text += f"— منوی {role} —\n"
        # short textual description
        if role == "seller":
            text += "➕ افزودن محصول\n📦 محصولات من\n"
        elif role == "manager":
            text += "➕ افزودن محصول\n📦 مدیریت محصولات\n👥 مدیریت کاربران\n"
        elif role == "admin":
            text += "📦 مدیریت محصولات\n👥 مدیریت کاربران\n📜 لاگ‌ها\n"
        elif role == "dev":
            text += "⚙️ Debug Tools\n📜 لاگ‌ها (Dev)\n"

    # Build InlineKeyboardMarkup: buyer buttons first, then role buttons and a close button
    kb = buyer_buttons.copy()
    if role_buttons:
        kb.append([InlineKeyboardButton("────────", callback_data="noop")])
        kb.extend(role_buttons)
    kb.append([InlineKeyboardButton("🔙 بستن", callback_data="common:close")])
    return text, InlineKeyboardMarkup(kb)


# After successful login/register, send menus: buyer + role-specific buttons
async def send_role_menus_after_auth(update, context, phone):
    cursor.execute("SELECT id, firstname, lastname, role FROM users WHERE phonenumber=?", (phone,))
    row = cursor.fetchone()
    if not row:
        await update.message.reply_text("⚠️ خطا در بارگذاری منو.")
        return
    uid, firstname, lastname, role = row
    # build menu inline keyboard
    text = f"👋 سلام {firstname} {lastname} — نقش شما: {role}\n\nلطفاً یک بخش را انتخاب کنید:"
    # buyer buttons
    buyer_buttons = [
        [InlineKeyboardButton("🛍 خریدهای من", callback_data="buyer:my_purchases")],
        [InlineKeyboardButton("📝 ثبت درخواست/نظر", callback_data="buyer:request")],
        [InlineKeyboardButton("📩 پشتیبانی", callback_data="buyer:support")],
        [InlineKeyboardButton("💡 انتقاد/پیشنهاد", callback_data="buyer:suggest")],
    ]
    # role buttons
    role_buttons = []
    if role == "seller":
        role_buttons = [
            [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
            [InlineKeyboardButton("📦 محصولات من", callback_data="seller:my_products")],
        ]
    elif role == "manager":
        role_buttons = [
            [InlineKeyboardButton("➕ افزودن محصول", callback_data="products:add")],
            [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:manage_products")],
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="manager:users")],
        ]
    elif role == "admin":
        role_buttons = [
            [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin:manage_products")],
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin:users")],
            [InlineKeyboardButton("📜 لاگ‌ها", callback_data="admin:logs")],
        ]
    elif role == "dev":
        role_buttons = [
            [InlineKeyboardButton("⚙️ Debug Tools", callback_data="dev:menu")],
            [InlineKeyboardButton("📜 لاگ‌ها (Dev)", callback_data="dev:logs")],
        ]

    kb = []
    kb.extend(buyer_buttons)
    if role_buttons:
        kb.append([InlineKeyboardButton("────────", callback_data="noop")])
        kb.extend(role_buttons)
    kb.append([InlineKeyboardButton("🔙 خروج", callback_data="common:logout")])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    add_log(uid, "OPEN_MENU", f"role={role}")
