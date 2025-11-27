from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ حمله"), KeyboardButton(text="👤 پروفایل")],
            [KeyboardButton(text="🛒 فروشگاه"), KeyboardButton(text="🎯 لیگ‌ها")],
            [KeyboardButton(text="💎 فروشگاه ویژه"), KeyboardButton(text="🛠 ادمین")]
        ],
        resize_keyboard=True
    )
