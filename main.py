import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN تنظیم نشده!")
    exit(1)

# ساخت بات با تنظیمات ویژه برای جلوگیری از conflict
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# ==================== کیبورد اصلی ====================

def main_inline_keyboard():
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🪐 جنگنده‌ها", callback_data="menu_fighters")],
            [types.InlineKeyboardButton(text="⛏️ ماینر ZP", callback_data="menu_miner")],
            [types.InlineKeyboardButton(text="🛒 فروشگاه", callback_data="menu_shop")],
            [types.InlineKeyboardButton(text="👤 پروفایل", callback_data="menu_profile")],
        ]
    )
    return keyboard

# ==================== دستورات ====================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "لطفا یک گزینه انتخاب کنید:",
        reply_markup=main_inline_keyboard()
    )

@dp.callback_query(F.data == "menu_profile")
async def profile_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👤 **پروفایل شما:**\n💎 سکه: 1,000\n🆙 سطح: 1",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")
            ]]
        )
    )

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "منوی اصلی:",
        reply_markup=main_inline_keyboard()
    )

# ==================== وب سرور ====================

async def health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 سرور روی پورت {port}")
    return runner

async def main():
    logger.info("🔄 راه‌اندازی ربات...")
    
    # استارت وب سرور
    runner = await start_web_server()
    
    try:
        # پاک کردن webhook قبل از شروع polling
        await bot.delete_webhook(drop_pending_updates=True)
        
        logger.info("🚀 ربات شروع به کار کرد!")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"خطا: {e}")
    finally:
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
