import os
import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
from datetime import datetime, timedelta
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [123456789]  # آیدی خودت رو بذار

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN تنظیم نشده!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== دیتابیس پیشرفته ====================

def init_db():
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            zone_coin INTEGER DEFAULT 1000,
            zone_gem INTEGER DEFAULT 0,
            zone_point INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            power INTEGER DEFAULT 100,
            defense_level INTEGER DEFAULT 1,
            cyber_level INTEGER DEFAULT 1,
            sabotage_level INTEGER DEFAULT 1,
            miner_level INTEGER DEFAULT 1,
            last_miner_claim TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_missiles (
            user_id INTEGER,
            missile_name TEXT,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, missile_name)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_combinations (
            user_id INTEGER,
            combo_id INTEGER,
            combo_name TEXT,
            missiles TEXT,
            fighters TEXT,
            PRIMARY KEY (user_id, combo_id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ==================== داده‌های بازی ====================

MISSILES = {
    # پیشرفته (لول ۱-۵)
    "شهاب ۱": {"damage": 50, "price": 200, "min_level": 1, "category": "پیشرفته"},
    "شهاب ۲": {"damage": 70, "price": 350, "min_level": 2, "category": "پیشرفته"},
    "سومار": {"damage": 90, "price": 500, "min_level": 3, "category": "پیشرفته"},
    "قدر": {"damage": 110, "price": 700, "min_level": 4, "category": "پیشرفته"},
    "فاتح": {"damage": 130, "price": 1000, "min_level": 5, "category": "پیشرفته"},
    
    # فوق‌پیشرفته (لول ۶-۱۰)
    "زلزال": {"damage": 160, "price": 1500, "min_level": 6, "category": "فوق‌پیشرفته"},
    "نازعات": {"damage": 190, "price": 2000, "min_level": 7, "category": "فوق‌پیشرفته"},
    "صیاد": {"damage": 220, "price": 2500, "min_level": 8, "category": "فوق‌پیشرفته"},
}

FIGHTERS = {
    "F-16 Falcon": {"bonus": 80, "price": 5000, "min_level": 10},
    "F-22 Raptor": {"bonus": 150, "price": 12000, "min_level": 12},
    "Su-57 Felon": {"bonus": 220, "price": 25000, "min_level": 14},
}

MINER_LEVELS = {
    1: {"zp_per_hour": 100, "upgrade_cost": 500, "max_capacity": 300},
    2: {"zp_per_hour": 200, "upgrade_cost": 1000, "max_capacity": 600},
    3: {"zp_per_hour": 350, "upgrade_cost": 2000, "max_capacity": 1050},
}

# ==================== توابع دیتابیس ====================

def get_user(user_id):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_missiles(user_id):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('SELECT missile_name, quantity FROM user_missiles WHERE user_id = ?', (user_id,))
    missiles = cursor.fetchall()
    conn.close()
    return missiles

def update_user_coins(user_id, amount):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET zone_coin = zone_coin + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def update_user_zp(user_id, amount):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET zone_point = zone_point + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def update_user_power(user_id, amount):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET power = power + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def init_user(user_id, username):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    
    # موشک‌های اولیه
    initial_missiles = [
        (user_id, "شهاب ۱", 5),
        (user_id, "شهاب ۲", 3),
    ]
    for missile in initial_missiles:
        cursor.execute('INSERT OR REPLACE INTO user_missiles VALUES (?, ?, ?)', missile)
    
    conn.commit()
    conn.close()

# ==================== منوها ====================

def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👤 پروفایل", callback_data="profile")],
        [types.InlineKeyboardButton(text="🛒 فروشگاه", callback_data="shop")],
        [types.InlineKeyboardButton(text="⛏️ ماینر ZP", callback_data="miner")],
        [types.InlineKeyboardButton(text="💥 سیستم حمله", callback_data="attack_menu")],
        [types.InlineKeyboardButton(text="🎡 گردونه", callback_data="wheel")],
    ])

def attack_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⚔️ حمله تکی", callback_data="single_attack_info")],
        [types.InlineKeyboardButton(text="🧩 حمله ترکیبی", callback_data="combo_attack_info")],
        [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
    ])

def shop_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💣 موشک‌ها", callback_data="shop_missiles")],
        [types.InlineKeyboardButton(text="🚁 جنگنده‌ها", callback_data="shop_fighters")],
        [types.InlineKeyboardButton(text="🛡️ پدافند", callback_data="shop_defense")],
        [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
    ])

# ==================== دستورات اصلی ====================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "ناشناس"
    init_user(user_id, username)
    
    await message.answer(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 ربات جنگی پیشرفته با قابلیت‌های کامل\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "profile")
async def profile_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user(user_id)
    user_missiles = get_user_missiles(user_id)
    
    if not user_data:
        return
    
    profile_text = (
        f"👤 **پروفایل کامل شما**\n\n"
        f"💎 **سکه:** {user_data[2]:,}\n"
        f"💠 **جم:** {user_data[3]}\n"
        f"🪙 **ZP:** {user_data[4]:,}\n"
        f"⭐ **XP:** {user_data[5]:,}\n"
        f"🆙 **سطح:** {user_data[6]}\n"
        f"💪 **کاپ:** {user_data[7]:,}\n"
        f"🛡️ **دفاع:** سطح {user_data[8]}\n\n"
        f"💣 **موشک‌ها:**\n"
    )
    
    for missile, qty in user_missiles:
        profile_text += f"• {missile}: {qty} عدد\n"
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 بروزرسانی", callback_data="profile")],
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "shop")
async def shop_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛒 **فروشگاه WarZone**\n\n"
        "دسته مورد نظر را انتخاب کنید:",
        reply_markup=shop_menu()
    )

@dp.callback_query(F.data == "shop_missiles")
async def shop_missiles_handler(callback: types.CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if not user_data:
        return
    
    user_level = user_data[6]
    text = "💣 **فروشگاه موشک‌ها**\n\n"
    
    for name, info in MISSILES.items():
        if info["min_level"] <= user_level:
            text += f"• {name} - {info['damage']} damage - {info['price']} سکه\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop")]
        ])
    )

@dp.callback_query(F.data == "miner")
async def miner_handler(callback: types.CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if not user_data:
        return
    
    miner_level = user_data[12]
    miner_info = MINER_LEVELS.get(miner_level, MINER_LEVELS[1])
    
    # محاسبه ZP انباشته شده
    last_claim = user_data[13]
    accumulated_zp = 0
    if last_claim:
        last_claim_time = datetime.fromisoformat(last_claim)
        hours_passed = (datetime.now() - last_claim_time).total_seconds() / 3600
        accumulated_zp = min(hours_passed * miner_info["zp_per_hour"], miner_info["max_capacity"])
    
    await callback.message.edit_text(
        f"⛏️ **ماینر ZonePoint**\n\n"
        f"🔄 سطح: {miner_level}\n"
        f"📊 تولید: {miner_info['zp_per_hour']} ZP/ساعت\n"
        f"💳 موجودی: {user_data[4]} ZP\n"
        f"📈 انباشته: {int(accumulated_zp)} ZP\n"
        f"🫙 ظرفیت: {miner_info['max_capacity']} ZP\n\n"
        f"⏰ بعد از ۳ ساعت برداشت کنید!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=f"💰 برداشت ({int(accumulated_zp)} ZP)", callback_data="miner_claim")],
            [types.InlineKeyboardButton(text=f"⬆️ ارتقا ({miner_info['upgrade_cost']} ZP)", callback_data="miner_upgrade")],
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "attack_menu")
async def attack_menu_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💥 **سیستم حمله WarZone**\n\n"
        "نوع حمله را انتخاب کنید:",
        reply_markup=attack_menu()
    )

@dp.callback_query(F.data == "single_attack_info")
async def single_attack_info_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⚔️ **حمله تکی**\n\n"
        "برای حمله تکی:\n"
        "۱. روی پیام کاربر ریپلای کنید\n"
        "۲. دستور زیر را ارسال کنید:\n"
        "`حمله [نام موشک]`\n\n"
        "مثال:\n"
        "`حمله شهاب ۱`\n\n"
        "❌ به مالک و ربات‌ها نمی‌توان حمله کرد!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="attack_menu")]
        ])
    )

@dp.callback_query(F.data == "wheel")
async def wheel_handler(callback: types.CallbackQuery):
    prizes = ["۱۰۰ سکه", "۵۰ ZP", "موشک شهاب ۱", "۱۰۰ XP"]
    prize = random.choice(prizes)
    
    await callback.message.edit_text(
        f"🎡 **گردونه شانس**\n\n"
        f"🎁 جایزه شما: **{prize}**!\n\n"
        f"می‌توانید هر ۲۴ ساعت یکبار گردونه بچرخانید.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 چرخاندن مجدد", callback_data="wheel")],
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 ربات جنگی پیشرفته با قابلیت‌های کامل\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu()
    )

# ==================== سیستم حمله ====================

@dp.message(F.text.startswith("حمله "))
async def single_attack_handler(message: types.Message):
    if not message.reply_to_message:
        await message.answer("❌ برای حمله روی پیام کاربر ریپلای کنید!")
        return
    
    target = message.reply_to_message.from_user
    attacker = message.from_user
    
    if target.id in ADMIN_IDS or target.is_bot:
        await message.answer("❌ به این کاربر نمی‌توان حمله کرد!")
        return
    
    missile_name = message.text.replace("حمله ", "").strip()
    
    # محاسبات حمله
    damage = 120
    coin_loss = 150
    cap_gain = 10
    xp_gain = 25
    
    await message.answer(
        f"⚔️ **حمله تکی موفق!**\n\n"
        f"🎯 هدف: {target.first_name}\n"
        f"💣 موشک: {missile_name}\n"
        f"💥 خسارت: {damage}\n"
        f"💰 سکه غنیمتی: {coin_loss}\n"
        f"💪 کاپ کسب شده: {cap_gain}\n"
        f"⭐ XP: {xp_gain}"
    )

# ==================== وب سرور ====================

async def health_check(request):
    return web.Response(text="🤖 WarZone Bot - Active")

async def main():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info("🤖 ربات WarZone با قابلیت‌های کامل شروع به کار کرد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
