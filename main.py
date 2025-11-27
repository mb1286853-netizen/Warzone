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
        CREATE TABLE IF NOT EXISTS user_fighters (
            user_id INTEGER,
            fighter_name TEXT,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, fighter_name)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_drones (
            user_id INTEGER,
            drone_name TEXT,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, drone_name)
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
    # 🟢 موشک‌های پیشرفته (لول ۱-۵)
    "شهاب ۱": {"damage": 50, "price": 200, "min_level": 1, "category": "پیشرفته"},
    "شهاب ۲": {"damage": 70, "price": 350, "min_level": 2, "category": "پیشرفته"},
    "سومار": {"damage": 90, "price": 500, "min_level": 3, "category": "پیشرفته"},
    "قدر": {"damage": 110, "price": 700, "min_level": 4, "category": "پیشرفته"},
    "فاتح": {"damage": 130, "price": 1000, "min_level": 5, "category": "پیشرفته"},
    
    # 🔵 موشک‌های فوق‌پیشرفته (لول ۶-۱۰)
    "زلزال": {"damage": 160, "price": 1500, "min_level": 6, "category": "فوق‌پیشرفته"},
    "نازعات": {"damage": 190, "price": 2000, "min_level": 7, "category": "فوق‌پیشرفته"},
    "صیاد": {"damage": 220, "price": 2500, "min_level": 8, "category": "فوق‌پیشرفته"},
    "رعد": {"damage": 250, "price": 3000, "min_level": 9, "category": "فوق‌پیشرفته"},
    "صاعقه": {"damage": 280, "price": 3500, "min_level": 10, "category": "فوق‌پیشرفته"},
    
    # 🟠 موشک‌های آتش‌زا (لول ۱۱-۱۵)
    "شعله": {"damage": 320, "price": 5000, "min_level": 11, "category": "آتش‌زا"},
    "آذر": {"damage": 350, "price": 6000, "min_level": 12, "category": "آتش‌زا"},
    "اخگر": {"damage": 380, "price": 7000, "min_level": 13, "category": "آتش‌زا"},
    "آتش": {"damage": 410, "price": 8000, "min_level": 14, "category": "آتش‌زا"},
    "اینفرنو": {"damage": 450, "price": 9000, "min_level": 15, "category": "آتش‌زا"},
    
    # 🔴 موشک‌های آخرالزمانی (لول ۱۶-۲۰)
    "آرماگدون": {"damage": 500, "price": 15000, "min_level": 16, "category": "آخرالزمانی"},
    "آپوکالیپس": {"damage": 580, "price": 18000, "min_level": 17, "category": "آخرالزمانی"},
    "رگناروک": {"damage": 660, "price": 22000, "min_level": 18, "category": "آخرالزمانی"},
    "دومزدی": {"damage": 750, "price": 28000, "min_level": 19, "category": "آخرالزمانی"},
    "آخرالزمان": {"damage": 850, "price": 35000, "min_level": 20, "category": "آخرالزمانی"},
    
    # 💎 موشک‌های ویژه (فقط با جم)
    "تایتان": {"damage": 1200, "price_gem": 20, "min_level": 25, "category": "ویژه"},
    "ابرنواختر": {"damage": 1500, "price_gem": 35, "min_level": 30, "category": "ویژه"},
    "سیاهچاله": {"damage": 2000, "price_gem": 50, "min_level": 35, "category": "ویژه"},
    "بیگ‌بنگ": {"damage": 3000, "price_gem": 100, "min_level": 40, "category": "ویژه"},
}

FIGHTERS = {
    "F-16 Falcon": {"bonus": 80, "price": 5000, "min_level": 3},
    "F-18 Hornet": {"bonus": 120, "price": 8000, "min_level": 5},
    "F-22 Raptor": {"bonus": 150, "price": 12000, "min_level": 8},
    "Su-57 Felon": {"bonus": 180, "price": 15000, "min_level": 10},
    "F-35 Lightning": {"bonus": 220, "price": 20000, "min_level": 12},
    "Su-75 Checkmate": {"bonus": 260, "price": 25000, "min_level": 14},
    "NGAD": {"bonus": 300, "price": 35000, "min_level": 16},
    "B-21 Raider": {"bonus": 350, "price": 45000, "min_level": 18},
    "F/A-XX": {"bonus": 400, "price_gem": 30, "min_level": 20, "category": "ویژه"},
    "SR-72 DarkStar": {"bonus": 500, "price_gem": 50, "min_level": 25, "category": "ویژه"},
}

DRONES = {
    "MQ-9 Reaper": {"bonus": 100, "price": 7000, "min_level": 4},
    "RQ-4 Global Hawk": {"bonus": 150, "price": 10000, "min_level": 6},
    "X-47B": {"bonus": 200, "price": 15000, "min_level": 8},
    "Loyal Wingman": {"bonus": 250, "price": 20000, "min_level": 10},
    "MQ-20 Avenger": {"bonus": 300, "price": 30000, "min_level": 12},
    "Valkyrie": {"bonus": 400, "price_gem": 25, "min_level": 15, "category": "ویژه"},
}

LEAGUES = {
    1: {"name": "🥉 برنز", "min_power": 0, "max_power": 1000, "reward": 100},
    2: {"name": "🥈 نقره", "min_power": 1000, "max_power": 3000, "reward": 300},
    3: {"name": "🥇 طلا", "min_power": 3000, "max_power": 6000, "reward": 600},
    4: {"name": "💎 پلاتین", "min_power": 6000, "max_power": 10000, "reward": 1000},
    5: {"name": "🏆 افسانه‌ای", "min_power": 10000, "max_power": 999999, "reward": 2000},
}

MINER_LEVELS = {
    1: {"zp_per_hour": 100, "upgrade_cost": 500, "max_capacity": 300},
    2: {"zp_per_hour": 200, "upgrade_cost": 1000, "max_capacity": 600},
    3: {"zp_per_hour": 350, "upgrade_cost": 2000, "max_capacity": 1050},
    4: {"zp_per_hour": 500, "upgrade_cost": 3500, "max_capacity": 1500},
    5: {"zp_per_hour": 700, "upgrade_cost": 5000, "max_capacity": 2100},
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

def get_user_fighters(user_id):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('SELECT fighter_name, quantity FROM user_fighters WHERE user_id = ?', (user_id,))
    fighters = cursor.fetchall()
    conn.close()
    return fighters

def get_user_drones(user_id):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('SELECT drone_name, quantity FROM user_drones WHERE user_id = ?', (user_id,))
    drones = cursor.fetchall()
    conn.close()
    return drones

def update_user_coins(user_id, amount):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET zone_coin = zone_coin + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def update_user_gems(user_id, amount):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET zone_gem = zone_gem + ? WHERE user_id = ?', (amount, user_id))
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

def update_user_xp(user_id, amount):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET xp = xp + ? WHERE user_id = ?', (amount, user_id))
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
    
    # موشک‌های اولیه
    initial_missiles = [
        (user_id, "شهاب ۱", 5),
        (user_id, "شهاب ۲", 3),
        (user_id, "سومار", 2)
    ]
    for missile in initial_missiles:
        cursor.execute('''
            INSERT OR REPLACE INTO user_missiles (user_id, missile_name, quantity)
            VALUES (?, ?, ?)
        ''', missile)
    
    # جنگنده‌های اولیه
    initial_fighters = [
        (user_id, "F-16 Falcon", 1)
    ]
    for fighter in initial_fighters:
        cursor.execute('''
            INSERT OR REPLACE INTO user_fighters (user_id, fighter_name, quantity)
            VALUES (?, ?, ?)
        ''', fighter)
    
    # پهپادهای اولیه
    initial_drones = [
        (user_id, "MQ-9 Reaper", 1)
    ]
    for drone in initial_drones:
        cursor.execute('''
            INSERT OR REPLACE INTO user_drones (user_id, drone_name, quantity)
            VALUES (?, ?, ?)
        ''', drone)
    
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
        [types.InlineKeyboardButton(text="🏆 لیگ‌ها", callback_data="leagues")],
        [types.InlineKeyboardButton(text="🛠️ ادمین", callback_data="admin_panel")]
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
        [types.InlineKeyboardButton(text="🛸 پهپادها", callback_data="shop_drones")],
        [types.InlineKeyboardButton(text="💎 ویژه", callback_data="shop_premium")],
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
        "🪐 ربات جنگی پیشرفته با تمام قابلیت‌ها\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "profile")
async def profile_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user(user_id)
    user_missiles = get_user_missiles(user_id)
    user_fighters = get_user_fighters(user_id)
    user_drones = get_user_drones(user_id)
    
    if not user_data:
        return
    
    # محاسبه لیگ
    user_power = user_data[7]
    current_league = "🥉 برنز"
    for league in LEAGUES.values():
        if league["min_power"] <= user_power < league["max_power"]:
            current_league = league["name"]
            break
    
    profile_text = (
        f"👤 **پروفایل کامل شما**\n\n"
        f"💎 **سکه:** {user_data[2]:,}\n"
        f"💠 **جم:** {user_data[3]}\n"
        f"🪙 **ZP:** {user_data[4]:,}\n"
        f"⭐ **XP:** {user_data[5]:,}\n"
        f"🆙 **سطح:** {user_data[6]}\n"
        f"💪 **کاپ:** {user_data[7]:,}\n"
        f"🏆 **لیگ:** {current_league}\n\n"
        f"💣 **موشک‌ها:**\n"
    )
    
    for missile, qty in user_missiles:
        missile_info = MISSILES.get(missile, {})
        category = missile_info.get('category', 'پیشرفته')
        profile_text += f"• {missile} ({category}): {qty} عدد\n"
    
    profile_text += f"\n🚁 **جنگنده‌ها:**\n"
    for fighter, qty in user_fighters:
        fighter_info = FIGHTERS.get(fighter, {})
        bonus = fighter_info.get('bonus', 0)
        profile_text += f"• {fighter}: {qty} عدد (+{bonus} damage)\n"
    
    profile_text += f"\n🛸 **پهپادها:**\n"
    for drone, qty in user_drones:
        drone_info = DRONES.get(drone, {})
        bonus = drone_info.get('bonus', 0)
        profile_text += f"• {drone}: {qty} عدد (+{bonus} damage)\n"
    
    profile_text += f"\n📊 **مجموع تجهیزات:** {sum(q for _, q in user_missiles) + sum(q for _, q in user_fighters) + sum(q for _, q in user_drones)} عدد"
    
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
    
    # گروه‌بندی موشک‌ها بر اساس دسته
    categories = {}
    for name, info in MISSILES.items():
        if info["min_level"] <= user_level:
            category = info.get("category", "پیشرفته")
            if category not in categories:
                categories[category] = []
            categories[category].append((name, info))
    
    for category, missiles in categories.items():
        text += f"**{category}:**\n"
        for name, info in missiles:
            if 'price_gem' in info:
                text += f"• {name} - {info['damage']} damage - {info['price_gem']} جم\n"
            else:
                text += f"• {name} - {info['damage']} damage - {info['price']} سکه\n"
        text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop")]
        ])
    )

@dp.callback_query(F.data == "shop_fighters")
async def shop_fighters_handler(callback: types.CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if not user_data:
        return
    
    user_level = user_data[6]
    text = "🚁 **فروشگاه جنگنده‌ها**\n\n"
    
    for name, info in FIGHTERS.items():
        if info["min_level"] <= user_level:
            if 'price_gem' in info:
                text += f"• {name} - +{info['bonus']} damage - {info['price_gem']} جم\n"
            else:
                text += f"• {name} - +{info['bonus']} damage - {info['price']} سکه\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop")]
        ])
    )

@dp.callback_query(F.data == "shop_drones")
async def shop_drones_handler(callback: types.CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if not user_data:
        return
    
    user_level = user_data[6]
    text = "🛸 **فروشگاه پهپادها**\n\n"
    
    for name, info in DRONES.items():
        if info["min_level"] <= user_level:
            if 'price_gem' in info:
                text += f"• {name} - +{info['bonus']} damage - {info['price_gem']} جم\n"
            else:
                text += f"• {name} - +{info['bonus']} damage - {info['price']} سکه\n"
    
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

@dp.callback_query(F.
