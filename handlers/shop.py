from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards.main_menu import shop_inline_keyboard, missiles_inline_keyboard
from config import MISSILES, FIGHTERS
from utils.database import get_user, update_user_coins, add_user_missile

shop_router = Router()

@shop_router.callback_query(F.data == "menu_shop")
async def shop_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛒 **فروشگاه WarZone**\n\n"
        "دسته مورد نظر را انتخاب کنید:",
        reply_markup=shop_inline_keyboard()
    )

@shop_router.callback_query(F.data == "shop_missiles")
async def missiles_shop(callback: types.CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if not user_data:
        return
    
    user_level = user_data[6]
    
    available_missiles = ""
    for name, info in MISSILES.items():
        if info["min_level"] <= user_level:
            available_missiles += f"• {name} - {info['damage']} damage - {info['price']} سکه\n"
    
    await callback.message.edit_text(
        f"💣 **فروشگاه موشک‌ها**\n\n"
        f"سطح شما: {user_level}\n\n"
        f"موشک‌های قابل خرید:\n{available_missiles}",
        reply_markup=missiles_inline_keyboard(user_level)
    )
