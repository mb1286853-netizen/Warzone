from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from config import ADMIN_IDS

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def create_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 کاربران", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 آمار", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🎁 Giveaway", callback_data="admin_giveaway")],
        [InlineKeyboardButton(text="📢 ارسال همگانی", callback_data="admin_broadcast")]
    ])

async def get_admin_stats():
    conn = sqlite3.connect('zone.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(zone_coin) FROM users')
    total_coins = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(zone_gem) FROM users')
    total_gems = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return f"📊 آمار ربات:\n👥 کاربران: {total_users}\n💰 سکه: {total_coins}\n💎 جم: {total_gems}"
