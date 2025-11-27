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
    
    # آتش‌زا (لول ۱۱-۱۵)
    "شعله": {"damage": 320, "price": 5000, "min_level": 11, "category": "آتش‌زا"},
    "آتش": {"damage": 410, "price": 8000, "min_level": 14, "category": "آتش‌زا"},
    
    # آخرالزمانی (لول ۱۶-۲۰)
    "آرماگدون": {"damage": 500, "price": 15000, "min_level": 16, "category": "آخرالزمانی"},
    "رگناروک": {"damage": 660, "price": 25000, "min_level": 18, "category": "آخرالزمانی"},
    
    # ویژه (فقط با جم)
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
    """بررسی امکان استفاده از قابلیت‌ها"""
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
    """تنظیم کول‌داون"""
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
    initial_missiles = [(user_id, "شهاب ۱", 5), (user_id, "شهاب ۲", 3)]
    for missile in initial_missiles:
        cursor.execute('''
            INSERT OR REPLACE INTO user_missiles (user_id, missile_name, quantity)
            VALUES (?, ?, ?)
        ''', missile)
    
    # ترکیب‌های اولیه
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
        f"🏆 **لیگ:** {current_league}\n"
        f"🛡️ **سطح دفاع:** {user_data[8]}\n"
        f"🔒 **امنیت:** {user_data[9]}\n"
        f"🕵️ **خرابکاری:** {user_data[10]}\n\n"
        f"💣 **موشک‌ها:**\n"
    )
    
    for missile, qty in user_missiles[:5]:  # فقط ۵ موشک اول
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
    
    # بررسی وجود موشک
    user_missiles = get_user_missiles(attacker.id)
    has_missile = any(missile[0] == missile_name for missile in user_missiles)
    
    if not has_missile:
        await message.answer(f"❌ موشک {missile_name} را ندارید!")
        return
    
    # محاسبات حمله
    damage = MISSILES.get(missile_name, {}).get("damage", 100)
    coin_loss = min(damage * 2, 500)
    cap_gain = damage // 10
    xp_gain = damage // 5
    
    # آپدیت کاربران
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

@dp.message(F.text.startswith("حمله ترکیبی "))
async def combo_attack_handler(message: types.Message):
    if not message.reply_to_message:
        await message.answer("❌ برای حمله روی پیام کاربر ریپلای کنید!")
        return
    
    target = message.reply_to_message.from_user
    attacker = message.from_user
    
    if target.id == attacker.id:
        await message.answer("❌ نمیتونی به خودت حمله کنی!")
        return
    
    if target.id in ADMIN_IDS or target.is_bot:
        await message.answer("❌ به این کاربر نمی‌توان حمله کرد!")
        return
    
    combo_id = message.text.replace("حمله ترکیبی ", "").strip()
    if not combo_id.isdigit() or int(combo_id) not in [1, 2, 3]:
        await message.answer("❌ شماره ترکیب باید ۱، ۲ یا ۳ باشد!")
        return
    
    combo_id = int(combo_id)
    user_combos = get_user_combinations(attacker.id)
    selected_combo = next((combo for combo in user_combos if combo[1] == combo_id), None)
    
    if not selected_combo:
        await message.answer("❌ ترکیب مورد نظر یافت نشد!")
        return
    
    # محاسبات حمله ترکیبی
    total_damage = 500  # دمیج ثابت برای تست
    coin_loss = min(total_damage * 3, 1000)
    cap_gain = total_damage // 8
    xp_gain = total_damage // 4
    
    # آپدیت کاربران
    update_user_coins(attacker.id, coin_loss)
    update_user_coins(target.id, -coin_loss)
    update_user_power(attacker.id, cap_gain)
    update_user_power(target.id, -cap_gain // 2)
    
    await message.answer(
        f"🧩 **حمله ترکیبی موفق!**\n\n"
        f"🎯 هدف: {target.first_name}\n"
        f"💥 ترکیب: {selected_combo[2]}\n"
        f"💥 خسارت کل: {total_damage}\n"
        f"💰 سکه غنیمتی: {coin_loss}\n"
        f"💪 کاپ کسب شده: {cap_gain}\n"
        f"⭐ XP: {xp_gain}"
    )

# ==================== سیستم گردونه ====================

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
    
    # اعطای جایزه
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

# ==================== سیستم ادمین ====================

def is_admin(user_id):
    return user_id in ADMIN_IDS

@dp.callback_query(F.data == "admin_panel")
async def admin_panel_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ دسترسی denied!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🛠️ **پنل مدیریت WarZone**\n\n"
        "گزینه مورد نظر را انتخاب کنید:",
        reply_markup=admin_menu()
    )

@dp.message(Command("addcoins"))
async def admin_add_coins(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer("❌ فرمت: /addcoins user_id amount")
            return
        
        user_id, amount = int(args[1]), int(args[2])
        
        if not get_user(user_id):
            await message.answer(
