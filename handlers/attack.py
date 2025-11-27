from aiogram import Router, types, F
from aiogram.filters import Command
from utils.database import get_user, update_user_coins, update_user_power
from utils.calculations import calculate_attack_damage, calculate_cap_loss, calculate_coin_loss
import sqlite3

attack_router = Router()

@attack_router.message(Command("attack"))
async def attack_command(message: types.Message):
    if not message.reply_to_message:
        await message.answer("❌ برای حمله روی پیام کاربر ریپلای کن!")
        return
    
    target = message.reply_to_message.from_user
    attacker = message.from_user
    
    if target.id in ADMIN_IDS or target.is_bot:
        await message.answer("❌ به این کاربر نمی‌توان حمله کرد!")
        return
    
    # دریافت اطلاعات مهاجم و مدافع
    attacker_data = get_user(attacker.id)
    defender_data = get_user(target.id)
    
    if not attacker_data or not defender_data:
        await message.answer("❌ خطا در دریافت اطلاعات!")
        return
    
    # محاسبات حمله
    damage = 1200  # دمیج پایه
    defender_coins = defender_data[2]
    defender_cap = defender_data[6]
    
    # محاسبه ضرر مدافع
    cap_loss = calculate_cap_loss(defender_cap, damage)
    coin_loss = calculate_coin_loss(defender_coins, damage)
    
    # آپدیت اطلاعات
    update_user_coins(defender_data[0], -coin_loss)
    update_user_coins(attacker_data[0], coin_loss)
    update_user_power(defender_data[0], -cap_loss)
    update_user_power(attacker_data[0], cap_loss // 2)
    
    await message.answer(
        f"⚔️ **حمله موفق!**\n\n"
        f"🎯 هدف: {target.first_name}\n"
        f"💥 خسارت: {damage:,}\n"
        f"📉 کاپ از دست رفته: {cap_loss}\n"
        f"💰 سکه غنیمتی: {coin_loss}\n"
        f"⭐ XP کسب شده: ۵۰"
    )
