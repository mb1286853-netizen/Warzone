import os
import logging
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# ایمپورت ماژول‌های خودمان
from config import BOT_TOKEN, ADMIN_IDS, PROTECTED_USERS, is_admin
from handlers.admin_panel import create_admin_keyboard, get_admin_stats
from handlers.user_commands import get_user_profile, get_shop_items, get_premium_shop
from utils.database import get_user, update_coins, update_gems, update_level, get_all_users
from keyboards.main_menu import main_menu

# تنظیمات logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN تنظیم نشده!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# دیتابیس
def init_db():
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            zone_coin INTEGER DEFAULT 1000,
            zone_gem INTEGER DEFAULT 10,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            power INTEGER DEFAULT 100,
            defense_level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("✅ دیتابیس آماده شد")

init_db()

# ==================== دستورات کاربران ====================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "ناشناس"
    
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (user_id, username)
    )
    conn.commit()
    conn.close()
    
    await message.answer(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "⚔️ ربات جنگی پیشرفته\n\n"
        "دستورات اصلی:\n"
        "/profile - پروفایل\n"
        "/shop - فروشگاه\n"
        "/premium_shop - فروشگاه ویژه\n"
        "/attack - حمله\n"
        "/admin - پنل مدیریت\n\n"
        "✅ میزبانی شده روی Render",
        reply_markup=main_menu()
    )

@dp.message(Command("profile"))
async def profile_command(message: types.Message):
    profile_text = await get_user_profile(message.from_user.id)
    await message.answer(profile_text)

@dp.message(Command("shop"))
async def shop_command(message: types.Message):
    await message.answer(get_shop_items())

@dp.message(Command("premium_shop"))
async def premium_shop_command(message: types.Message):
    await message.answer(get_premium_shop())

@dp.message(Command("attack"))
async def attack_command(message: types.Message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        if target.id in PROTECTED_USERS or target.is_bot:
            await message.answer("❌ به این کاربر نمی‌توان حمله کرد! (محافظت شده)")
            return
        
        await message.answer(f"⚔️ حمله به {target.first_name} موفق بود! 🎯")
    else:
        await message.answer("برای حمله روی پیام کاربر ریپلای کن!")

# ==================== دستورات ادمین ====================

@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ دسترسی denied!")
        return
    
    stats_text = await get_admin_stats()
    keyboard = create_admin_keyboard()
    
    await message.answer(stats_text, reply_markup=keyboard)

@dp.message(Command("addcoins"))
async def add_coins_command(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer("❌ فرمت: /addcoins user_id amount")
            return
        
        user_id, amount = int(args[1]), int(args[2])
        
        if not get_user(user_id):
            await message.answer("❌ کاربر یافت نشد!")
            return
        
        update_coins(user_id, amount)
        await message.answer(f"✅ {amount:,} سکه به کاربر {user_id} اضافه شد!")
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

@dp.message(Command("addgems"))
async def add_gems_command(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer("❌ فرمت: /addgems user_id amount")
            return
        
        user_id, amount = int(args[1]), int(args[2])
        
        if not get_user(user_id):
            await message.answer("❌ کاربر یافت نشد!")
            return
        
        update_gems(user_id, amount)
        await message.answer(f"✅ {amount} جم به کاربر {user_id} اضافه شد!")
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

@dp.message(Command("setlevel"))
async def set_level_command(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer("❌ فرمت: /setlevel user_id level")
            return
        
        user_id, level = int(args[1]), int(args[2])
        
        if not get_user(user_id):
            await message.answer("❌ کاربر یافت نشد!")
            return
        
        update_level(user_id, level)
        await message.answer(f"✅ سطح کاربر {user_id} به {level} تنظیم شد!")
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        broadcast_text = message.text.replace('/broadcast ', '')
        users = get_all_users()
        
        success = 0
        for user_id in users:
            try:
                await bot.send_message(user_id, broadcast_text)
                success += 1
            except:
                pass
        
        await message.answer(f"📢 ارسال همگانی:\n✅ موفق: {success} کاربر\n📊 کل: {len(users)} کاربر")
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

# ==================== اجرای ربات ====================

async def main():
    logger.info("🤖 WarZone Bot Starting on Render...")
    logger.info(f"👑 ادمین‌ها: {ADMIN_IDS}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
