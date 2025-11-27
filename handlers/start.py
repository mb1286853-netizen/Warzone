from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards.main_menu import main_inline_keyboard
from utils.database import init_user

start_router = Router()

@start_router.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "ناشناس"
    
    await init_user(user_id, username)
    
    await message.answer(
        "🚀 **به WarZone خوش آمدید!**\n\n"
        "🪐 یک ربات جنگی پیشرفته\n\n"
        "لطفا یک گزینه انتخاب کنید:",
        reply_markup=main_inline_keyboard()
    )
