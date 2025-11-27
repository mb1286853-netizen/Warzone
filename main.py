import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
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

# ==================== اینلاین کیبوردها ====================

def main_inline_keyboard():
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🪐 جنگنده‌ها", callback_data="menu_fighters")],
            [types.InlineKeyboardButton(text="⛏️ ماینر ZP", callback_data="menu_miner")],
            [types.InlineKeyboardButton(text="🛒 فروشگاه", callback_data="menu_shop")],
            [types.InlineKeyboardButton(text="💎 فروشگاه ویژه", callback_data="menu_premium_shop")],
            [types.InlineKeyboardButton(text="🎡 گردونه رایگان", callback_data="menu_free_wheel")],
            [types.InlineKeyboardButton(text="🏆 رنکینگ", callback_data="menu_ranking")],
            [types.InlineKeyboardButton(text="👤 پروفایل", callback_data="menu_profile")],
            [types.InlineKeyboardButton(text="🛠️ پنل ادمین", callback_data="menu_admin")]
        ]
    )
    return keyboard

# ==================== مدیریت کلیک روی دکمه‌ها ====================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 یک ربات جنگی پیشرفته\n\n"
        "لطفا یک گزینه انتخاب کنید:",
        reply_markup=main_inline_keyboard()
    )

@dp.callback_query(F.data == "menu_profile")
async def profile_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👤 **پروفایل شما:**\n\n"
        "💎 سکه: 1,000\n"
        "💠 جم: 0\n" 
        "🪙 ZP: 0\n"
        "⭐ XP: 0\n"
        "🆙 سطح: 1\n"
        "💪 قدرت: 100\n"
        "🛡️ دفاع: سطح 1\n\n"
        "از گزینه‌های زیر استفاده کنید:",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_main")]
            ]
        )
    )

@dp.callback_query(F.data == "menu_miner")
async def miner_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⛏️ **ماینر ZonePoint**\n\n"
        "🔄 سطح ماینر: 1\n"
        "📊 تولید ساعتی: 100 ZP\n"
        "💳 موجودی فعلی: 0 ZP\n"
        "📈 انباشته شده: 0 ZP\n"
        "🫙 ظرفیت حداکثر: 300 ZP\n\n"
        "⏰ بعد از ۳ ساعت برداشت کنید!",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="💰 برداشت (0 ZP)", callback_data="miner_claim")],
                [types.InlineKeyboardButton(text="⬆️ ارتقا ماینر (500 ZP)", callback_data="miner_upgrade")],
                [types.InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_main")]
            ]
        )
    )

@dp.callback_query(F.data == "menu_shop")
async def shop_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛒 **فروشگاه WarZone**\n\n"
        "دسته مورد نظر را انتخاب کنید:",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="💣 موشک‌ها", callback_data="shop_missiles")],
                [types.InlineKeyboardButton(text="🚁 جنگنده‌ها", callback_data="shop_fighters")],
                [types.InlineKeyboardButton(text="🛡️ پدافندها", callback_data="shop_defense")],
                [types.InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_main")]
            ]
        )
    )

@dp.callback_query(F.data == "shop_missiles")
async def missiles_shop(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💣 **فروشگاه موشک‌ها**\n\n"
        "موشک‌های قابل خرید:\n"
        "• شهاب ۱ - ۵۰ damage - ۲۰۰ سکه\n"
        "• شهاب ۲ - ۷۰ damage - ۳۵۰ سکه\n"
        "• سومار - ۹۰ damage - ۵۰۰ سکه\n\n"
        "برای خرید روی موشک مورد نظر کلیک کنید:",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="شهاب ۱ - ۲۰۰ سکه", callback_data="buy_missile_1")],
                [types.InlineKeyboardButton(text="شهاب ۲ - ۳۵۰ سکه", callback_data="buy_missile_2")],
                [types.InlineKeyboardButton(text="سومار - ۵۰۰ سکه", callback_data="buy_missile_3")],
                [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_shop")]
            ]
        )
    )

@dp.callback_query(F.data == "menu_fighters")
async def fighters_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🪐 **منوی جنگنده‌ها**\n\n"
        "برای حمله به کاربران:\n"
        "روی پیام کاربر ریپلای کنید و از گزینه‌های زیر استفاده کنید:",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="💥 حمله تکی", callback_data="attack_single")],
                [types.InlineKeyboardButton(text="🎯 حمله ترکیبی", callback_data="attack_combo")],
                [types.InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_main")]
            ]
        )
    )

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔙 به منوی اصلی بازگشتید:\n\n"
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 یک ربات جنگی پیشرفته\n\n"
        "لطفا یک گزینه انتخاب کنید:",
        reply_markup=main_inline_keyboard()
    )

# ==================== وب سرور برای پورت ====================

async def handle_health_check(request):
    return web.Response(text="🤖 WarZone Bot is running!")

async def start_web_server():
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

async def main():
    logger.info("🤖 در حال راه‌اندازی ربات WarZone...")
    
    web_runner = await start_web_server()
    
    try:
        logger.info("🚀 ربات WarZone شروع به کار کرد!")
        await dp.start_polling(bot)
    finally:
        await web_runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
