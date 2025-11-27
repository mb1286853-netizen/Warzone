import os

# تنظیمات اصلی
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '123456789').split(',')))

# کاربران محافظت شده (مالک + ربات‌ها)
PROTECTED_USERS = ADMIN_IDS + [777000, 136817688]

# تنظیمات بازی
INITIAL_COINS = 1000
INITIAL_GEMS = 10
INITIAL_LEVEL = 1
INITIAL_POWER = 100

# موشک‌های عادی
MISSILES = {
    "Tomahawk": {"damage": 900, "price": 500},
    "Brahmos": {"damage": 1300, "price": 800},
    "Iskander": {"damage": 2000, "price": 1200},
    "Scalp": {"damage": 1500, "price": 1000},
    "JASSM": {"damage": 1800, "price": 1100}
}

# موشک‌های ویژه (جم)
PREMIUM_MISSILES = {
    "DF-41": {"damage": 7500, "price_gem": 15},
    "RS-28 Sarmat": {"damage": 9000, "price_gem": 20},
    "AGM-183 ARRW": {"damage": 12000, "price_gem": 35},
    "3M22 Zircon": {"damage": 13000, "price_gem": 40},
    "Project Thor": {"damage": 20000, "price_gem": 100}
}

# پهپادها
DRONES = {
    "MQ-9 Reaper": {"bonus": 300, "price": 700},
    "Switchblade": {"bonus": 500, "price": 900},
    "Global Hawk": {"bonus": 700, "price": 1200},
    "X-47B": {"bonus": 1000, "price": 2000}
}
