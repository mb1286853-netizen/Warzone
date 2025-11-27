from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import MISSILES

def main_inline_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🪐 جنگنده‌ها", callback_data="menu_fighters")],
            [InlineKeyboardButton(text="⛏️ ماینر ZP", callback_data="menu_miner")],
            [InlineKeyboardButton(text="🛒 فروشگاه", callback_data="menu_shop")],
            [InlineKeyboardButton(text="💎 فروشگاه ویژه", callback_data="menu_premium_shop")],
            [InlineKeyboardButton(text="🎡 گردونه رایگان", callback_data="menu_free_wheel")],
            [InlineKeyboardButton(text="🏆 رنکینگ", callback_data="menu_ranking")],
            [InlineKeyboardButton(text="👤 پروفایل", callback_data="menu_profile")],
            [InlineKeyboardButton(text="🛠️ پنل ادمین", callback_data="menu_admin")]
        ]
    )
    return keyboard

def shop_inline_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💣 موشک‌ها", callback_data="shop_missiles")],
            [InlineKeyboardButton(text="🚁 جنگنده‌ها", callback_data="shop_fighters")],
            [InlineKeyboardButton(text="🛡️ پدافندها", callback_data="shop_defense")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ]
    )
    return keyboard

def missiles_inline_keyboard(user_level: int):
    buttons = []
    for name, info in MISSILES.items():
        if info["min_level"] <= user_level:
            buttons.append([InlineKeyboardButton(
                text=f"{name} - {info['price']} سکه", 
                callback_data=f"buy_missile_{name}"
            )])
    
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_shop")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
