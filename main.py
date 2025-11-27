import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import socket
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN تنظیم نشده!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ایجاد یک سرور HTTP ساده برای پورت binding
async def handle_health_check(request):
    return web.Response(text="🤖 WarZone Bot is running!")

async def start_web_server():
    """شروع یک سرور وب ساده برای پورت binding"""
    app = web.Application()
    app.router.add_get('/health', handle_health_check)
    app.router.add_get('/', handle_health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 سرور وب روی پورت {port} شروع شد")
    return runner

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 ربات جنگی پیشرفته\n\n"
        "دستورات در دسترس:\n"
        "/start - نمایش این پیام\n"
        "/profile - پروفایل شما\n"
        "/miner - ماینر ZP\n"
        "/shop - فروشگاه"
    )

@dp.message(Command("profile"))
async def profile_command(message: types.Message):
    await message.answer("👤 **پروفایل شما:**\n💎 سکه: 1,000\n🆙 سطح: 1\n💪 قدرت: 100")

@dp.message(Command("miner"))
async def miner_command(message: types.Message):
    await message.answer("⛏️ **ماینر ZP:**\nسطح ۱ - ۱۰۰ ZP/ساعت\n💰 موجودی: ۰ ZP")

@dp.message(Command("shop"))
async def shop_command(message: types.Message):
    await message.answer("🛒 **فروشگاه:**\n💣 موشک‌ها\n🚁 جنگنده‌ها\n🛡️ پدافندها")

async def main():
    logger.info("🤖 در حال راه‌اندازی ربات WarZone...")
    
    # شروع سرور وب برای پورت binding
    web_runner = await start_web_server()
    
    try:
        logger.info("🚀 ربات WarZone شروع به کار کرد!")
        await dp.start_polling(bot)
    finally:
        await web_runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
