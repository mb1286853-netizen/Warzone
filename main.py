import os
import logging
import asyncio
import sqlite3
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
from datetime import datetime, timedelta
import json

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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_cooldowns (
            user_id INTEGER,
            cooldown_type TEXT,
            last_used TIMESTAMP,
            PRIMARY KEY (user_id, cooldown_type)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_defenses (
            user_id INTEGER,
            defense_type TEXT,
            level INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, defense_type)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ==================== داده‌های بازی ====================

MISSILES = {
    "شهاب ۱": {"damage": 50, "price": 200, "min_level": 1, "category": "پیشرفته"},
    "شهاب ۲": {"damage": 70, "price": 350, "min_level": 2, "category": "پیشرفته"},
    "سومار": {"damage": 90, "price": 500, "min_level": 3, "category": "پیشرفته"},
    "قدر": {"damage": 110, "price": 700, "min_level": 4, "category": "پیشرفته"},
    "فاتح": {"damage": 130, "price": 1000, "min_level": 5, "category": "پیشرفته"},
    "زلزال": {"damage": 160, "price": 1500, "min_level": 6, "category": "فوق‌پیشرفته"},
    "نازعات": {"damage": 190, "price": 2000, "min_level": 7, "category": "فوق‌پیشرفته"},
    "صیاد": {"damage": 220, "price": 2500, "min_level": 8, "category": "فوق‌پیشرفته"},
    "شعله": {"damage": 320, "price": 5000, "min_level": 11, "category": "آتش‌زا"},
    "آتش": {"damage": 410, "price": 8000, "min_level": 14, "category": "آتش‌زا"},
    "آرماگدون": {"damage": 500, "price": 15000, "min_level": 16, "category": "آخرالزمانی"},
    "رگناروک": {"damage": 660, "price": 25000, "min_level": 18, "category": "آخرالزمانی"},
    "تایتان": {"damage": 1200, "price_gem": 20, "min_level": 25, "category": "ویژه"},
    "ابرنواختر": {"damage": 2000, "price_gem": 50, "min_level": 30, "category": "ویژه"},
}

FIGHTERS = {
    "F-16 Falcon": {"bonus": 80, "price": 5000, "min_level": 10},
    "F-22 Raptor": {"bonus": 150, "price": 12000, "min_level": 12},
    "Su-57 Felon": {"bonus": 220, "price": 25000, "min_level": 14},
    "F-35 Lightning": {"bonus": 300, "price": 50000, "min_level": 16},
}

DEFENSES = {
    "پدافند موشکی": {"reduction": 0.15, "price": 3000, "max_level": 10},
    "پدافند الکترونیک": {"reduction": 0.10, "price": 2000, "max_level": 8},
    "پدافند ضد جنگنده": {"reduction": 0.12, "price": 4000, "max_level": 6},
    "امنیت سایبری": {"reduction": 0.20, "price": 5000, "max_level": 5},
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

def get_user_combinations(user_id):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_combinations WHERE user_id = ? ORDER BY combo_id', (user_id,))
    combos = cursor.fetchall()
    conn.close()
    return combos

def get_user_defenses(user_id):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('SELECT defense_type, level FROM user_defenses WHERE user_id = ?', (user_id,))
    defenses = cursor.fetchall()
    conn.close()
    return defenses

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

def update_user_level(user_id, level):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET level = ? WHERE user_id = ?', (level, user_id))
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
    
    initial_combos = [
        (user_id, 1, "ترکیب سریع", '["شهاب ۱", "شهاب ۱"]', '[]'),
        (user_id, 2, "ترکیب قدرتمند", '["شهاب ۲", "شهاب ۲"]', '[]'),
        (user_id, 3, "ترکیب ویژه", '["شهاب ۱", "شهاب ۲"]', '[]')
    ]
    for combo in initial_combos:
        cursor.execute('INSERT OR REPLACE INTO user_combinations VALUES (?, ?, ?, ?, ?)', combo)
    
    conn.commit()
    conn.close()

# ==================== منوها ====================

def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👤 پروفایل", callback_data="profile")],
        [types.InlineKeyboardButton(text="🛒 فروشگاه", callback_data="shop")],
        [types.InlineKeyboardButton(text="⛏️ ماینر ZP", callback_data="miner")],
        [types.InlineKeyboardButton(text="💥 سیستم حمله", callback_data="attack_menu")],
        [types.InlineKeyboardButton(text="🛡️ پدافندها", callback_data="defenses")],
        [types.InlineKeyboardButton(text="🎡 گردونه", callback_data="wheel")],
        [types.InlineKeyboardButton(text="🏆 لیگ‌ها", callback_data="leagues")],
        [types.InlineKeyboardButton(text="🛠️ ادمین", callback_data="admin_panel")]
    ])

def attack_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⚔️ حمله تکی", callback_data="single_attack_info")],
        [types.InlineKeyboardButton(text="🧩 حمله ترکیبی", callback_data="combo_attack_info")],
        [types.InlineKeyboardButton(text="🔧 ترکیب‌های من", callback_data="my_combinations")],
        [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
    ])

def shop_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💣 موشک‌ها", callback_data="shop_missiles")],
        [types.InlineKeyboardButton(text="🚁 جنگنده‌ها", callback_data="shop_fighters")],
        [types.InlineKeyboardButton(text="🛡️ پدافند", callback_data="shop_defense")],
        [types.InlineKeyboardButton(text="💎 ویژه", callback_data="shop_premium")],
        [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
    ])

def admin_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💰 افزودن سکه", callback_data="admin_add_coins")],
        [types.InlineKeyboardButton(text="💎 افزودن جم", callback_data="admin_add_gems")],
        [types.InlineKeyboardButton(text="🆙 تنظیم لول", callback_data="admin_set_level")],
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
    user_defenses = get_user_defenses(user_id)
    
    if not user_data:
        return
    
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
        f"🏆 **لیگ:** {current_league}\n"
        f"🛡️ **سطح دفاع:** {user_data[8]}\n"
        f"🔒 **امنیت:** {user_data[9]}\n"
        f"🕵️ **خرابکاری:** {user_data[10]}\n\n"
        f"💣 **موشک‌ها:**\n"
    )
    
    for missile, qty in user_missiles[:5]:
        profile_text += f"• {missile}: {qty} عدد\n"
    
    if len(user_missiles) > 5:
        profile_text += f"• و {len(user_missiles) - 5} موشک دیگر...\n"
    
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
            price = info.get('price_gem', info.get('price'))
            currency = "جم" if 'price_gem' in info else "سکه"
            text += f"• {name} - {info['damage']} damage - {price} {currency}\n"
    
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

@dp.callback_query(F.data == "combo_attack_info")
async def combo_attack_info_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🧩 **حمله ترکیبی**\n\n"
        "برای حمله ترکیبی:\n"
        "۱. روی پیام کاربر ریپلای کنید\n"
        "۲. دستور زیر را ارسال کنید:\n"
        "`حمله ترکیبی [شماره ترکیب]`\n\n"
        "مثال:\n"
        "`حمله ترکیبی ۱`\n\n"
        "❌ به مالک و ربات‌ها نمی‌توان حمله کرد!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="attack_menu")]
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
    elif prize["type"] == "gems":
        update_user_gems(user_id, prize["value"])
    
    set_feature_cooldown(user_id, "wheel")
    
    await callback.message.edit_text(
        f"🎡 **گردونه شانس**\n\n"
        f"🎁 جایزه شما: **{prize['name']}**!\n\n"
        f"⏰ می‌توانید ۲۴ ساعت دیگر دوباره گردونه بچرخانید.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "leagues")
async def leagues_handler(callback: types.CallbackQuery):
    text = "🏆 **لیگ‌های WarZone**\n\n"
    
    for league_id, league in LEAGUES.items():
        text += f"{league['name']}: {league['min_power']:,} - {league['max_power']:,} قدرت\n"
    
    text += "\n🎯 هر لیگ جوایز مخصوص خود را دارد!"
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "defenses")
async def defenses_handler(callback: types.CallbackQuery):
    user_defenses = get_user_defenses(callback.from_user.id)
    
    text = "🛡️ **سیستم پدافند**\n\n"
    
    if user_defenses:
        for defense_type, level in user_defenses:
            defense_info = DEFENSES.get(defense_type, {})
            reduction = defense_info.get('reduction', 0)
