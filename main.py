import os
import logging
import asyncio
import sqlite3
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [123456789]  # آیدی خودت رو بذار

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN تنظیم نشده!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== دیتابیس ====================

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
        CREATE TABLE IF NOT EXISTS user_cooldowns (
            user_id INTEGER,
            cooldown_type TEXT,
            last_used TIMESTAMP,
            PRIMARY KEY (user_id, cooldown_type)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ==================== داده‌های بازی ====================

MISSILES = {
    "شهاب ۱": {"damage": 50, "price": 200, "min_level": 1},
    "شهاب ۲": {"damage": 70, "price": 350, "min_level": 2},
    "سومار": {"damage": 90, "price": 500, "min_level": 3},
    "قدر": {"damage": 110, "price": 700, "min_level": 4},
    "فاتح": {"damage": 130, "price": 1000, "min_level": 5},
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

def can_use_feature(user_id, feature_type, cooldown_hours=24):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT last_used FROM user_cooldowns WHERE user_id = ? AND cooldown_type = ?',
        (user_id, feature_type)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return True, 0
    
    last_used = datetime.fromisoformat(result[0])
    now = datetime.now()
    remaining = (last_used + timedelta(hours=cooldown_hours) - now).total_seconds() / 3600
    
    return remaining <= 0, max(0, remaining)

def set_feature_cooldown(user_id, feature_type):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_cooldowns (user_id, cooldown_type, last_used)
        VALUES (?, ?, ?)
    ''', (user_id, feature_type, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def init_user(user_id, username):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    
    initial_missiles = [(user_id, "شهاب ۱", 5), (user_id, "شهاب ۲", 3)]
    for missile in initial_missiles:
        cursor.execute('''
            INSERT OR REPLACE INTO user_missiles (user_id, missile_name, quantity)
            VALUES (?, ?, ?)
        ''', missile)
    
    conn.commit()
    conn.close()

# ==================== منوها ====================

def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👤 پروفایل", callback_data="profile")],
        [types.InlineKeyboardButton(text="🛒 فروشگاه", callback_data="shop")],
        [types.InlineKeyboardButton(text="⛏️ ماینر ZP", callback_data="miner")],
        [types.InlineKeyboardButton(text="🎡 گردونه", callback_data="wheel")],
    ])

# ==================== دستورات اصلی ====================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "ناشناس"
    init_user(user_id, username)
    
    await message.answer(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 ربات جنگی پیشرفته\n\n"
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
        f"💪 **کاپ:** {user_data[7]:,}\n\n"
        f"💣 **موشک‌ها:**\n"
    )
    
    for missile, qty in user_missiles:
        profile_text += f"• {missile}: {qty} عدد\n"
    
    profile_text += f"\n📊 **مجموع موشک‌ها:** {sum(q for _, q in user_missiles)} عدد"
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 بروزرسانی", callback_data="profile")],
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "shop")
async def shop_handler(callback: types.CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if not user_data:
        return
    
    user_level = user_data[6]
    text = "🛒 **فروشگاه موشک‌ها**\n\n"
    
    for name, info in MISSILES.items():
        if info["min_level"] <= user_level:
            text += f"• {name} - {info['damage']} damage - {info['price']} سکه\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "miner")
async def miner_handler(callback: types.CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if not user_data:
        return
    
    miner_level = user_data[12]
    miner_info = MINER_LEVELS.get(miner_level, MINER_LEVELS[1])
    
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

@dp.callback_query(F.data == "wheel")
async def wheel_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    can_use, remaining = can_use_feature(user_id, "wheel", 24)
    
    if not can_use:
        await callback.answer(f"⏰ باید {remaining:.1f} ساعت صبر کنید!", show_alert=True)
        return
    
    prizes = [
        {"name": "۱۰۰ سکه", "type": "coins", "value": 100},
        {"name": "۵۰ ZP", "type": "zp", "value": 50},
        {"name": "موشک شهاب ۱", "type": "missile", "value": "شهاب ۱"},
        {"name": "۱۰۰ XP", "type": "xp", "value": 100},
        {"name": "۵ جم", "type": "gems", "value": 5},
    ]
    
    prize = random.choice(prizes)
    
    if prize["type"] == "coins":
        update_user_coins(user_id, prize["value"])
    elif prize["type"] == "zp":
        update_user_zp(user_id, prize["value"])
    elif prize["type"] == "missile":
        conn = sqlite3.connect('zone.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_missiles (user_id, missile_name, quantity)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, missile_name) 
            DO UPDATE SET quantity = quantity + 1
        ''', (user_id, prize["value"]))
        conn.commit()
        conn.close()
    
    set_feature_cooldown(user_id, "wheel")
    
    await callback.message.edit_text(
        f"🎡 **گردونه شانس**\n\n"
        f"🎁 جایزه شما: **{prize['name']}**!\n\n"
        f"⏰ می‌توانید ۲۴ ساعت دیگر دوباره گردونه بچرخانید.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 ربات جنگی پیشرفته\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu()
    )

# ==================== سیستم حمله ====================

@dp.message(F.text.startswith("حمله "))
async def single_attack_handler(message: types.Message):
    if not message.reply_to_message:
        await message.answer("❌ برای حمله روی پیام کاربر ریپلای کنید!")
        return
    
    if not message.reply_to_message.from_user:
        await message.answer("❌ روی پیام یک کاربر ریپلای کنید!")
        return
    
    target = message.reply_to_message.from_user
    attacker = message.from_user
    
    if target.id == attacker.id:
        await message.answer("❌ نمیتونی به خودت حمله کنی!")
        return
    
    if target.id in ADMIN_IDS or target.is_bot:
        await message.answer("❌ به این کاربر نمی‌توان حمله کرد!")
        return
    
    missile_name = message.text.replace("حمله ", "").strip()
    
    user_missiles = get_user_missiles(attacker.id)
    has_missile = any(missile[0] == missile_name for missile in user_missiles)
    
    if not has_missile:
        await message.answer(f"❌ موشک {missile_name} را ندارید!")
        return
    
    damage = MISSILES.get(missile_name, {}).get("damage", 100)
    coin_loss = min(damage * 2, 500)
    cap_gain = damage // 10
    xp_gain = damage // 5
    
    update_user_coins(attacker.id, coin_loss)
    update_user_coins(target.id, -coin_loss)
    update_user_power(attacker.id, cap_gain)
    update_user_power(target.id, -cap_gain // 2)
    
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
    
    logger.info("🤖 ربات WarZone شروع به کار کرد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
