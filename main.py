import os
import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== دیتابیس ساده ====================

def init_db():
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            zone_coin INTEGER DEFAULT 1000,
            zone_gem INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            power INTEGER DEFAULT 100,
            defense_level INTEGER DEFAULT 1
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
    conn.commit()
    conn.close()

init_db()

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

def init_user(user_id, username):
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (user_id, username)
    )
    
    # اضافه کردن موشک‌های اولیه
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
    
    conn.commit()
    conn.close()

# ==================== منوها ====================

def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👤 پروفایل", callback_data="profile")],
        [types.InlineKeyboardButton(text="🛒 فروشگاه", callback_data="shop")],
        [types.InlineKeyboardButton(text="⛏️ ماینر", callback_data="miner")],
        [types.InlineKeyboardButton(text="💥 حمله", callback_data="attack")]
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "ناشناس"
    
    init_user(user_id, username)
    
    await message.answer(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 یک ربات جنگی پیشرفته\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user(user_id)
    user_missiles = get_user_missiles(user_id)
    
    if not user_data:
        await callback.answer("❌ کاربر یافت نشد!")
        return
    
    # متن پروفایل کامل
    profile_text = (
        f"👤 **پروفایل کامل شما**\n\n"
        f"💎 **سکه:** {user_data[2]:,}\n"
        f"💠 **جم:** {user_data[3]}\n"
        f"⭐ **XP:** {user_data[4]:,}\n"
        f"🆙 **سطح:** {user_data[5]}\n"
        f"💪 **کاپ (قدرت):** {user_data[6]:,}\n"
        f"🛡️ **سطح دفاع:** {user_data[7]}\n\n"
        f"💣 **موشک‌های شما:**\n"
    )
    
    # اضافه کردن موشک‌ها
    if user_missiles:
        for missile_name, quantity in user_missiles:
            profile_text += f"• {missile_name}: {quantity} عدد\n"
    else:
        profile_text += "• هیچ موشکی ندارید\n"
    
    profile_text += f"\n📊 **مجموع موشک‌ها:** {sum(q for _, q in user_missiles)} عدد"
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 بروزرسانی", callback_data="profile")],
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 یک ربات جنگی پیشرفته\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "shop")
async def shop(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛒 **فروشگاه WarZone**\n\n"
        "به زودی آماده می‌شود...",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "miner")
async def miner(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⛏️ **ماینر ZP**\n\n"
        "به زودی آماده می‌شود...",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

@dp.callback_query(F.data == "attack")
async def attack(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💥 **سیستم حمله**\n\n"
        "برای حمله روی پیام کاربر ریپلای کنید",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ])
    )

# ==================== وب سرور ====================

async def health_check(request):
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info("🤖 ربات WarZone شروع به کار کرد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
