import os
import logging
import asyncio
import requests
import threading
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== Keep Alive ====================

def keep_alive():
    def ping():
        while True:
            try:
                # جای YOUR-BOT-URL رو با آدرس واقعی رباتت عوض کن
                requests.get("https://warzone-bot.onrender.com/")
                logger.info("🔄 پینگ ارسال شد")
            except Exception as e:
                logger.error(f"❌ خطا در پینگ: {e}")
            time.sleep(300)  # هر 5 دقیقه
    
    thread = threading.Thread(target=ping, daemon=True)
    thread.start()
    logger.info("✅ سیستم Keep-Alive فعال شد")

# ==================== منوها ====================

def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👤 پروفایل", callback_data="profile")],
        [types.InlineKeyboardButton(text="🛒 فروشگاه", callback_data="shop")],
        [types.InlineKeyboardButton(text="⛏️ ماینر", callback_data="miner")]
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🚀 به WarZone خوش آمدید!", reply_markup=main_menu())

@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    await callback.message.edit_text("👤 پروفایل شما", reply_markup=main_menu())

# ==================== وب سرور ====================

async def web_handler(request):
    return web.Response(text="🤖 WarZone Bot - Active")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', web_handler)
    app.router.add_get('/health', web_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 سرور روی پورت {port}")
    return runner

async def main():
    # شروع keep-alive
    keep_alive()
    
    # شروع وب سرور
    runner = await start_web_server()
    
    try:
        logger.info("🚀 ربات WarZone شروع به کار کرد!")
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
