import os
import json

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '123456789').split(',')))

# تنظیمات بازی
INITIAL_COINS = 1000
INITIAL_GEMS = 0
INITIAL_LEVEL = 1
INITIAL_POWER = 100

# بارگذاری داده‌ها
with open('data/missiles.json', 'r', encoding='utf-8') as f:
    MISSILES = json.load(f)

with open('data/fighters.json', 'r', encoding='utf-8') as f:
    FIGHTERS = json.load(f)

# سیستم کاپ و سکه
MAX_COIN_LOSS_PERCENT = 0.33  # حداکثر 1/3 ذخایر
CAP_LOSS_MULTIPLIER = 0.1    # ضریب کاهش کاپ
MIN_COIN_LOSS = 50           # حداقل سکه از دست رفته
