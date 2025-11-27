from aiogram import Router, types, F
from datetime import datetime, timedelta
from utils.database import get_user, update_user_zp, update_miner_level
import sqlite3

miner_router = Router()

MINER_LEVELS = {
    1: {"zp_per_hour": 100, "upgrade_cost": 500, "max_capacity": 300},
    2: {"zp_per_hour": 200, "upgrade_cost": 1000, "max_capacity": 600},
    3: {"zp_per_hour": 350, "upgrade_cost": 2000, "max_capacity": 1050},
    # ... تا لول ۱۵
}

@miner_router.callback_query(F.data == "menu_miner")
async def miner_menu(callback: types.CallbackQuery):
    user_data = get_user(callback.from_user.id)
    if not user_data:
        return
    
    miner_level = user_data[12]
    last_claim = user_data[13]
    current_zp = user_data[3]
    
    miner_info = MINER_LEVELS.get(miner_level, MINER_LEVELS[1])
    
    # محاسبه ZP انباشته شده
    if last_claim:
        last_claim_time = datetime.fromisoformat(last_claim)
        hours_passed = (datetime.now() - last_claim_time).total_seconds() / 3600
        accumulated_zp = min(hours_passed * miner_info["zp_per_hour"], miner_info["max_capacity"])
    else:
        accumulated_zp = 0
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=f"💰 برداشت ({int(accumulated_zp)} ZP)", callback_data="miner_claim")],
            [types.InlineKeyboardButton(text=f"⬆️ ارتقا ماینر ({miner_info['upgrade_cost']} ZP)", callback_data="miner_upgrade")],
            [types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")]
        ]
    )
    
    await callback.message.edit_text(
        f"⛏️ **ماینر ZonePoint**\n\n"
        f"🔄 سطح ماینر: {miner_level}\n"
        f"📊 تولید ساعتی: {miner_info['zp_per_hour']} ZP\n"
        f"💳 موجودی فعلی: {current_zp} ZP\n"
        f"📈 انباشته شده: {int(accumulated_zp)} ZP\n"
        f"🫙 ظرفیت حداکثر: {miner_info['max_capacity']} ZP\n\n"
        f"⏰ بعد از ۳ ساعت برداشت کنید!",
        reply_markup=keyboard
    )
