from aiogram import Router, types, F
from aiogram.filters import Command
from config import ADMIN_IDS
from utils.database import get_user, update_user_coins, update_user_gems, update_user_level, update_user_zp

admin_router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@admin_router.message(Command("admin"))
async def admin_command(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ دسترسی denied!")
        return
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="💰 افزودن سکه", callback_data="admin_add_coins")],
            [types.InlineKeyboardButton(text="💎 افزودن جم", callback_data="admin_add_gems")],
            [types.InlineKeyboardButton(text="🪙 افزودن ZP", callback_data="admin_add_zp")],
            [types.InlineKeyboardButton(text="🆙 تنظیم لول", callback_data="admin_set_level")]
        ]
    )
    
    await message.answer("🛠️ **پنل مدیریت**", reply_markup=keyboard)

@admin_router.message(Command("addcoins"))
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
        
        update_user_coins(user_id, amount)
        await message.answer(f"✅ {amount:,} سکه به کاربر {user_id} اضافه شد!")
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")
