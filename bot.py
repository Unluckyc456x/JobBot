import asyncio
import random
import html
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from flask import Flask
from threading import Thread
from supabase import create_client, Client

# === Веб-сервер для Render (keep_alive) ===
app_web = Flask('')

@app_web.route('/')
def home():
    return "Бот Джоб v2.3 работает!"

def run_web():
    port = int(os.environ.get('PORT', 5000))
    app_web.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()
# =========================================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6990974323  # Твой Telegram ID

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Глобальный словарь для подкрутки роллов (доступен главному админу)
forced_next_cards = {}

# База карт (60 шт с поддержкой OLD)
CARDS_DATA = [
    # --- СУЩЕСТВУЮЩИЕ КАРТЫ (1-30) ---
    (1, "Хоумлендер", "The Boys", "null", "https://i.postimg.cc/ZqY9CWHx/f07a37afacdd14bce8c62a8338cc6cc2.jpg", "Я здесь бог.", 3333),
    (2, "Мясник", "The Boys", "mythic", "https://i.postimg.cc/pdb7CH2M/IMG-20260612-221039-579.jpg", "Мы спасём эту чёртовую страну!", 2332),
    (3, "Декстер Морган", "Dexter", "mythic", "https://i.postimg.cc/tgczkddt/IMG-20260612-221039-343.jpg", "Сегодня ночью — охота.", 1777),
    (4, "Тони Сопрано", "The Sopranos", "mythic", "https://i.postimg.cc/NM7kthqK/IMG-20260612-221045-473.jpg", "Я пришёл за утками.", 1919),
    (5, "Ганнибал Лектер", "Hannibal", "mythic", "https://i.postimg.cc/Dzn6myv5/IMG-20260612-221039-738.jpg", "Печень — с бобами.", 2700),
    (6, "Хайзенберг", "Breaking Bad", "mythic", "https://i.postimg.cc/gJknx1L6/IMG-20260612-221052-546.jpg", "Я — тот, кто стучит.", 2500),
    (7, "Королева Мэйв", "The Boys", "legendary", "https://i.postimg.cc/zBP4nRvP/IMG-20260612-221045-477.jpg", "Хватит притворяться, Хоумлендер.", 1636),
    (8, "Джесси Пинкман", "Breaking Bad", "legendary", "https://i.postimg.cc/CLvnbhs1/IMG-20260612-221039-831.jpg", "Наука, bitch!", 1455),
    (9, "Артур Митчелл (Троица)", "Dexter", "legendary", "https://i.postimg.cc/vHmLJSPf/IMG-20260612-221053-114.jpg", "Всё кончено, Декстер.", 800),
    (10, "Сол Гудман", "Better Call Saul", "legendary", "https://i.postimg.cc/KzswbyDB/IMG-20260612-221045-610.jpg", "Позвоните Солу!", 1321),
    (11, "Уилл Грэм", "Hannibal", "legendary", "https://i.postimg.cc/rmc5Qh0W/IMG-20260612-221053-281.jpg", "Это красиво.", 1111),
    (12, "Энни (Старлайт)", "The Boys", "epic", "https://i.postimg.cc/SRV0Jt8d/IMG-20260612-221052-889.jpg", "Я верю в добро, даже если его почти не осталось.", 609),
    (13, "Дебра Морган", "Dexter", "epic", "https://i.postimg.cc/TYvCBczN/IMG-20260612-221039-420.jpg", "Ты мне отвратителен, но я люблю тебя, брат.", 512),
    (14, "Кристофер Молтисанти", "The Sopranos", "epic", "https://i.postimg.cc/ZRCJtmdz/IMG-20260612-221045-723.jpg", "Моя судьба — кино, а не это дерьмо.", 464),
    (15, "Ким Уэкслер", "Better Call Saul", "epic", "https://i.postimg.cc/NFS36wKZ/IMG-20260612-221045-353.jpg", "Ты в деле, Сол.", 400),
    (16, "Гус Фринг", "Breaking Bad", "epic", "https://i.postimg.cc/7LKRkT3D/IMG-20260612-221039-593.jpg", "Всё, что я делаю, я делаю для бизнеса.", 444),
    (17, "Подводник (The Deep)", "The Boys", "rare", "https://i.postimg.cc/52RvW4X7/IMG-20260612-221039-607.jpg", "Меня никто не уважает… даже осьминог.", 277),
    (18, "Сержант Докс", "Dexter", "rare", "https://i.postimg.cc/dtJSLB5Q/IMG-20260612-221045-533.jpg", "Я узнаю убийцу, когда вижу его.", 400),
    (19, "Поли Уолнатс", "The Sopranos", "rare", "https://i.postimg.cc/hvLwNZMb/IMG-20260612-221045-287.jpg", "Что ты там говоришь?", 217),
    (20, "Лало Саламанка", "Better Call Saul", "rare", "https://i.postimg.cc/7hRkK2Wt/IMG-20260612-221044-998.jpg", "Расскажи это снова.", 389),
    (21, "Хэнк Шрейдер", "Breaking Bad", "rare", "https://i.postimg.cc/bNTYtm8M/IMG-20260612-221052-912.jpg", "Я найду тебя, Хайзенберг.", 323),
    (22, "Эбигейл Хоббс", "Hannibal", "rare", "https://i.postimg.cc/02cxQrdt/IMG-20260612-221053-261.jpg", "Я не хотела этого.", 247),
    (23, "Ханна Маккей", "Dexter", "uncommon", "https://i.postimg.cc/bwxJ3qQ0/IMG-20260612-221052-516.jpg", "Мы созданы друг для друга, Декстер.", 167),
    (24, "Кармела Сопрано", "The Sopranos", "uncommon", "https://i.postimg.cc/63YtF333/IMG-20260612-221039-861.jpg", "Я знаю, кто ты, Тони.", 111),
    (25, "Майк Эрмантраут", "Better Call Saul", "uncommon", "https://i.postimg.cc/Dwvk3h96/IMG-20260612-221045-690.jpg", "Я просчитываю каждый шаг.", 129),
    (26, "Тодд Алкист", "Breaking Bad", "uncommon", "https://i.postimg.cc/MKstX8cF/IMG-20260612-221045-373.jpg", "Ничего личного.", 100),
    (27, "Французик", "The Boys", "common", "https://i.postimg.cc/tTXVhYwd/IMG-20260612-221052-794.jpg", "Я люблю этот мир, но он не любит меня.", 100),
    (28, "Винс Масука", "Dexter", "common", "https://i.postimg.cc/nLJR7GkM/IMG-20260612-221039-163.jpg", "Это отличный день, чтобы быть живым!", 69),
    (29, "Дядя Джуниор", "The Sopranos", "common", "https://i.postimg.cc/R0w0p4Kf/IMG-20260612-221039-310.jpg", "У тебя никогда не было яиц.", 55),
    (30, "Чак Макгилл", "Better Call Saul", "common", "https://i.postimg.cc/B6H4QgMK/IMG-20260612-221052-846.jpg", "Люди не меняются.", 50),

    # --- НОВЫЕ КАРТЫ (31-60) ---
    (31, "Танос", "Marvel", "null", "https://i.postimg.cc/jjGrB9DG/IMG-20260822-210720-068.jpg", "Я сама неизбежность.", 3500),
    (32, "Шерлок Холмс", "Приключения Шерлока Холмса", "old", "https://i.postimg.cc/pThLFzFk/IMG-20260822-210719-469.jpg", "Элементарно, Ватсон!", 2100),
    (33, "Джек Воробей", "Пираты Карибского моря", "old", "https://i.postimg.cc/Z5wbsVPG/S600x-U-2x.jpg", "Вам запечатлеть этот день, когда чуть не был пленён Капитан Джек Воробей!", 2050),
    (34, "Терминатор T-800", "Терминатор", "old", "https://i.postimg.cc/Hn0Hw2sZ/Terminator-in-Madame-Tussaud-London-(33465711484).jpg", "I'll be back.", 2200),
    (35, "Кевин Маккаллистер", "Один дома", "old", "https://i.postimg.cc/GmmrDv0H/fbba1d8d6eff23b8cd01f290cd3184ab.jpg", "Это мой дом. Я должен его защищать!", 1950),
    (36, "Солдатик", "The Boys", "mythic", "https://i.postimg.cc/7hN8GZm1/56cd3f43798077ace1e4f5fb7bbb0404.jpg", "Я не отступаю, я иду напролом.", 2400),
    (37, "Гектор Саламанка", "Breaking Bad", "mythic", "https://i.postimg.cc/0jPhsqPr/IMG-20260822-210720-037.jpg", "Дзинь-дзинь-дзинь!", 1850),
    (38, "Тор", "Marvel", "mythic", "https://i.postimg.cc/4N8qrMMw/IMG-20260822-210719-433.jpg", "Я — Тор, сын Одина!", 2350),
    (39, "Чёрный Нуар", "The Boys", "legendary", "https://i.postimg.cc/d0CfZ005/w1500-50245845-(4).jpg", "...", 1500),
    (40, "Человек-паук", "Marvel", "legendary", "https://i.postimg.cc/tJqvctNw/IMG-20260822-210719-595.jpg", "С большой силой приходит большая ответственность.", 1400),
    (41, "Тони Старк", "Marvel", "legendary", "https://i.postimg.cc/jjy8dkgr/IMG-20260820-240.jpg", "Я — Железный человек.", 1600),
    (42, "Начо Варга", "Better Call Saul", "legendary", "https://i.postimg.cc/0QW78YqF/IMG-20260822-210720-119.jpg", "Я сам решаю свою судьбу.", 1250),
    (43, "Сильвио Данте", "The Sopranos", "legendary", "https://i.postimg.cc/MZn9nTrH/IMG-20260822-210719-549.jpg", "И когда я думал, что завязал...", 1300),
    (44, "Виктория Ньюман", "The Boys", "epic", "https://i.postimg.cc/LsszGCc4/IMG-20260822-210719-394.jpg", "Главное — держать голову на плечах.", 580),
    (45, "Говард Хэмлин", "Better Call Saul", "epic", "https://i.postimg.cc/N0LHdyXx/Better-Call-Saul-Howard-Hamlin.jpg", "Charlie Hustle, ты зашел слишком далеко.", 450),
    (46, "Оливер Саксон", "Dexter", "epic", "https://i.postimg.cc/RZYFVg3d/4c62a5b03733e98808826ae85c64b0de.jpg", "У всех есть слабости.", 520),
    (47, "Мейсон Верджер", "Hannibal", "epic", "https://i.postimg.cc/R0fMC4xC/IMG-20260822-210719-662.jpg", "Деньги решают всё.", 620),
    (48, "Фредерик Чилтон", "Hannibal", "epic", "https://i.postimg.cc/DfCKT84P/b7f6be3fc7370f479859bc523a677317.jpg", "Я знаю, как устроены их умы.", 420),
    (49, "Экспресс", "The Boys", "rare", "https://i.postimg.cc/TYZFdmd5/IMG-20260822-214043.jpg", "Ты не сможешь убежать.", 310),
    (50, "Фурио Джунта", "The Sopranos", "rare", "https://i.postimg.cc/W1LYLv8t/i.jpg", "В Неаполе мы решаем вопросы иначе.", 280),
    (51, "Туко Саламанка", "Breaking Bad", "rare", "https://i.postimg.cc/500nqN9M/43b9b68c200dbba0699dc2472043a98d.jpg", "Плотно! Ох, как плотно!", 350),
    (52, "Джои Куинн", "Dexter", "rare", "https://i.postimg.cc/13Sx06Lb/21d35512d4a58021ee56cfb81a29b799.jpg", "Я просто делаю свою работу.", 260),
    (53, "Алана Блум", "Hannibal", "rare", "https://i.postimg.cc/JhddFBdT/a70e977447ef831847c293f979f191b2.jpg", "Я пытаюсь понять тебя.", 230),
    (54, "Анхель Батиста", "Dexter", "uncommon", "https://i.postimg.cc/3JCfTqcf/1920x.jpg", "Страсть делает нас людьми.", 150),
    (55, "Барсук и Тощий Пит", "Breaking Bad", "uncommon", "https://i.postimg.cc/63vz1bZS/i-(1).jpg", "Чувак, это самый лучший сценарий!", 140),
    (56, "Беверли Катц", "Hannibal", "uncommon", "https://i.postimg.cc/3wyZdfnt/IMG-20260823-113550.jpg", "Улики не врут.", 130),
    (57, "Арти Букко", "The Sopranos", "common", "https://i.postimg.cc/jq64w74R/IMG-20260823-113711.jpg", "Телятина сегодня восхитительна!", 60),
    (58, "Стейси Эрмантраут", "Better Call Saul", "common", "https://i.postimg.cc/s2ZpVQ2C/i-(2).jpg", "Спасибо за помощь, Майк.", 50),
    (59, "Соколиный глаз", "Marvel", "common", "https://i.postimg.cc/RhvfQgL9/683868eea8b2b356f7787c6a9038e41d.jpg", "Я никогда не промахиваюсь.", 75),
    (60, "Нед Лидс", "Marvel", "common", "https://i.postimg.cc/02QKkMW2/i-(3).jpg", "Я чувак в кресле!", 45)
]

CARDS_DICT = {
    c[0]: {"id": c[0], "name": c[1], "series": c[2], "rarity": c[3], "image_url": c[4], "quote": c[5], "jobs_award": c[6]}
    for c in CARDS_DATA
}

RARITY_CHANCES = {"common":0.54, "uncommon":0.24, "rare":0.11, "epic":0.06, "legendary":0.025, "mythic":0.013, "old":0.005, "null":0.002}
RARITY_POWDER = {"common":10, "uncommon":25, "rare":50, "epic":100, "legendary":250, "mythic":500, "old":750, "null":1000}
RARITY_EMOJI = {"common":"⚪", "uncommon":"🟢", "rare":"🔵", "epic":"🟣", "legendary":"🟠", "mythic":"🔴", "old":"🟤", "null":"⚫"}
RARITY_RU = {"common":"Простые", "uncommon":"Необычные", "rare":"Редкие", "epic":"Эпические", "legendary":"Легендарные", "mythic":"Мифические", "old":"Old", "null":"Null"}
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic", "old", "null"]

# Титулы за обычную валюту
TITLES_SHOP = {
    "cinema": {"name": "✋ Absolutely Cinema 🤚", "price": 2500},
    "netflix": {"name": "👑 King of Netflix", "price": 2500},
    "binge": {"name": "🍿 Professional Binge-Watcher", "price": 2500},
    "spoilers": {"name": "🎬 Master of Spoilers", "price": 2500},
    "vip": {"name": "🎟️ VIP Ticket Holder", "price": 2500}
}

# Донатные титулы и Эксклюзив Создателя
DONATE_TITLES = {
    1: {"name": "🌌 [ Celestial Backer ]", "level": 1, "cost": "15 ⭐"},
    2: {"name": "⚡ [ Director of the Universe ]", "level": 2, "cost": "50 ⭐"},
    3: {"name": "👑 [ Absolute Overlord ]", "level": 3, "cost": "100 ⭐"}
}
CREATOR_TITLE = "💻⚡ Job Developer"

# Магазин рамок (с категориями)
FRAMES_SHOP = {
    "shield": {"emoji": "🛡️", "price": 500, "type": "single", "cat": "normal"},
    "fire": {"emoji": "🔥", "price": 500, "type": "single", "cat": "normal"},
    "zap": {"emoji": "⚡", "price": 500, "type": "single", "cat": "normal"},
    "star": {"emoji": "⭐", "price": 500, "type": "single", "cat": "normal"},
    "cat": {"emoji": "🐱", "price": 500, "type": "single", "cat": "normal"},
    "zzz": {"emoji": "💤", "price": 500, "type": "single", "cat": "normal"},
    "hot": {"emoji": "🥵", "price": 500, "type": "single", "cat": "normal"},
    "yawn": {"emoji": "🥱", "price": 500, "type": "single", "cat": "normal"},
    "moyai": {"emoji": "🗿", "price": 500, "type": "single", "cat": "normal"},
    "poop": {"emoji": "💩", "price": 500, "type": "single", "cat": "normal"},
    
    "moon": {"emoji_left": "🌚", "emoji_right": "🌝", "price": 750, "type": "pair", "cat": "pair"},
    "monkeys": {"emoji_left": "🙊", "emoji_right": "🙉", "price": 750, "type": "pair", "cat": "pair"},
    "wind": {"emoji_left": "🌬️", "emoji_right": "💨", "price": 750, "type": "pair", "cat": "pair"},
    "apples": {"emoji_left": "🍎", "emoji_right": "🍏", "price": 750, "type": "pair", "cat": "pair"},
    "disks": {"emoji_left": "📀", "emoji_right": "💿", "price": 750, "type": "pair", "cat": "pair"},
    
    "ban": {"emoji_left": "🚫", "emoji_right": "🚫", "price": 1000, "type": "pair", "cat": "toxic"},
    "rose": {"emoji_left": "🥀", "emoji_right": "🥀", "price": 1000, "type": "pair", "cat": "toxic"},
    "warn": {"emoji_left": "⚠️", "emoji_right": "⚠️", "price": 1000, "type": "pair", "cat": "toxic"},
    "preg": {"emoji_left": "🔝", "emoji_right": "🫄", "price": 1000, "type": "pair", "cat": "toxic"},
    "clown_down": {"emoji_left": "🤡", "emoji_right": "⬇️", "price": 1000, "type": "pair", "cat": "toxic"},
    "clown_you": {"emoji_left": "🫵", "emoji_right": "🤡", "price": 1000, "type": "pair", "cat": "toxic"},
    
    "dragon": {"emoji": "🐲", "price": 3000, "type": "single", "cat": "elite"},
    "gem": {"emoji": "💎", "price": 3000, "type": "single", "cat": "elite"},
    "diamond": {"emoji": "♦️", "price": 3000, "type": "single", "cat": "elite"},
    "gear": {"emoji": "⚙️", "price": 3000, "type": "single", "cat": "elite"},
    "saturn": {"emoji": "🪐", "price": 3000, "type": "single", "cat": "elite"},
    "banana": {"emoji": "🍌", "price": 3000, "type": "single", "cat": "elite"},
    "slot": {"emoji": "🎰", "price": 3000, "type": "single", "cat": "elite"}
}

user_request_timestamps = defaultdict(list)
user_command_history = defaultdict(list)

def register_user(user_id, username, first_name=""):
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not res.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "username": username or "no_name",
            "first_name": first_name or "",
            "is_frozen": False, "is_banned": False, "is_admin": False,
            "jobs_balance": 0, "powder_balance": 0, "casino_balance": 0,
            "active_frame": None, "active_title": None, "unlocked_titles": [],
            "boost_until": None, "luck_rolls_2x": 0, "luck_rolls_5x": 0,
            "casino_bets_today": 0, "null_cards_count": 0
        }).execute()
    else:
        supabase.table("users").update({
            "username": username or "no_name",
            "first_name": first_name or ""
        }).eq("user_id", user_id).execute()

def is_user_blocked(user_id):
    res = supabase.table("users").select("is_frozen, is_banned").eq("user_id", user_id).execute()
    if res.data:
        row = res.data[0]
        return bool(row.get("is_frozen")) or bool(row.get("is_banned"))
    return False

def is_admin(user_id):
    if user_id == ADMIN_ID: return True
    res = supabase.table("users").select("is_admin").eq("user_id", user_id).execute()
    return bool(res.data[0].get("is_admin")) if res.data else False

async def check_antispam(message: Message, bot: Bot) -> bool:
    msg_date = message.date.replace(tzinfo=timezone.utc) if message.date.tzinfo is None else message.date
    if (datetime.now(timezone.utc) - msg_date).total_seconds() > 300:
        return True

    user_id = message.from_user.id
    if user_id == ADMIN_ID or is_admin(user_id) or is_user_blocked(user_id):
        return is_user_blocked(user_id)

    now = datetime.now()
    cmd_text = message.text.strip().lower() if message.text else ""

    timestamps = [t for t in user_request_timestamps[user_id] if now - t <= timedelta(seconds=5)]
    timestamps.append(now)
    user_request_timestamps[user_id] = timestamps

    cmd_history = [(t, c) for t, c in user_command_history[user_id] if now - t <= timedelta(minutes=10)]
    cmd_history.append((now, cmd_text))
    user_command_history[user_id] = cmd_history

    same_cmd_count = sum(1 for t, c in cmd_history if c == cmd_text)

    if len(timestamps) >= 7 or same_cmd_count >= 10:
        tier_label = "Tier 2 (>7 за 5 сек)" if len(timestamps) >= 7 else f"Tier 3 (10x '{cmd_text}')"
        supabase.table("users").update({"is_frozen": True, "freeze_reason": tier_label}).eq("user_id", user_id).execute()
        return True
    elif len(timestamps) > 1:
        return True
    return False

async def verify_cb_owner(cb: CallbackQuery, target_uid: int) -> bool:
    if cb.from_user.id != target_uid:
        await cb.answer("❌ Это меню не ваше!", show_alert=True)
        return False
    return True

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.callback_query(F.data == "close_menu")
async def close_menu_cb(cb: CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        await cb.answer("Сообщение устарело.")

def format_user_display(user_row):
    uname = user_row.get("username")
    fname = user_row.get("first_name") or "Игрок"
    name = uname if uname and uname != "no_name" else fname
    
    frame = user_row.get("active_frame")
    if frame and frame in FRAMES_SHOP:
        f_info = FRAMES_SHOP[frame]
        if f_info["type"] == "single":
            name = f"{f_info['emoji']} {name} {f_info['emoji']}"
        else:
            name = f"{f_info['emoji_left']} {name} {f_info['emoji_right']}"
    return html.escape(name)
# ================= КОМАНДЫ =================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if await check_antispam(message, bot): return
    register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        "📺 <b>Добро пожаловать в коллекцию карт «Джоб v2.3»!</b>\n\n"
        "🎴 <b>Команды:</b>\n"
        "• /roll — Выбить карту (раз в 2 ч)\n"
        "• /profile — Профиль и ачивки\n"
        "• /balance — Просмотр всех валют\n"
        "• /powder — Сжечь дубликаты в порошок\n"
        "• /blackmarket — Чёрный рынок бустов\n"
        "• /shop — Магазин рамок и титулов\n"
        "• /casino — Казино «У Джоба»\n"
        "• /topjobs — Топ игроков",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    if await check_antispam(message, bot): return
    register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    res = supabase.table("users").select("jobs_balance, powder_balance").eq("user_id", message.from_user.id).execute()
    data = res.data[0] if res.data else {"jobs_balance":0, "powder_balance":0}
    text = (
        "💳 <b>Ваш баланс:</b>\n"
        f"• Джобсы (🪙): <b>{data.get('jobs_balance', 0)}</b>\n"
        f"• Карточный порошок (✨): <b>{data.get('powder_balance', 0)}</b>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

def can_roll(user_id):
    res = supabase.table("users").select("last_roll_time").eq("user_id", user_id).execute()
    if not res.data or not res.data[0].get("last_roll_time"):
        return True, None
    last = datetime.fromisoformat(res.data[0]["last_roll_time"].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    if now - last >= timedelta(hours=2):
        return True, None
    rem = timedelta(hours=2) - (now - last)
    return False, f"{rem.seconds // 3600} ч {(rem.seconds % 3600) // 60} мин"

@dp.message(Command("roll"))
async def roll_card(message: Message):
    if await check_antispam(message, bot): return
    uid = message.from_user.id
    register_user(uid, message.from_user.username, message.from_user.first_name)

    ok, rem = can_roll(uid)
    if not ok:
        await message.answer(f"⏳ У Джоба больше нет карт сейчас для вас, отдыхайте, но приходите через ({rem})")
        return

    u_res = supabase.table("users").select("*").eq("user_id", uid).execute()
    u_data = u_res.data[0]
    
    # Проверка подкрутки роллов (если администратор использовал /rig_roll)
    if uid in forced_next_cards and forced_next_cards[uid]:
        forced_cid = forced_next_cards[uid].pop(0)
        chosen = CARDS_DICT.get(forced_cid, CARDS_DICT[1])
    else:
        chances = RARITY_CHANCES.copy()
        if u_data.get("luck_rolls_5x", 0) > 0:
            chances["epic"] *= 5
            supabase.table("users").update({"luck_rolls_5x": u_data["luck_rolls_5x"] - 1}).eq("user_id", uid).execute()
        elif u_data.get("luck_rolls_2x", 0) > 0:
            for r in chances: chances[r] *= 2
            supabase.table("users").update({"luck_rolls_2x": u_data["luck_rolls_2x"] - 1}).eq("user_id", uid).execute()

        total_w = sum(chances.values())
        norm_chances = {r: w / total_w for r, w in chances.items()}

        r = random.random()
        cum = 0
        chosen_rarity = "common"
        for rarity, chance in norm_chances.items():
            cum += chance
            if r <= cum:
                chosen_rarity = rarity
                break

        matching = [c for c in CARDS_DATA if c[3] == chosen_rarity] or CARDS_DATA
        chosen = CARDS_DICT[random.choice(matching)[0]]

    award = chosen['jobs_award']
    boost_until = u_data.get("boost_until")
    if boost_until and datetime.fromisoformat(boost_until.replace('Z', '+00:00')) > datetime.now(timezone.utc):
        award = int(award * 1.5)

    now_iso = datetime.now(timezone.utc).isoformat()
    supabase.table("user_cards").insert({"user_id": uid, "card_id": chosen["id"], "card_name": chosen["name"], "rarity": chosen["rarity"], "obtained_at": now_iso}).execute()
    
    new_balance = u_data.get("jobs_balance", 0) + award
    update_dict = {"jobs_balance": new_balance, "last_roll_time": now_iso}
    if chosen["rarity"] == "null":
        update_dict["null_cards_count"] = u_data.get("null_cards_count", 0) + 1
    
    supabase.table("users").update(update_dict).eq("user_id", uid).execute()

    caption = (
        f"🃏 <b>Джоб достаёт карту «{html.escape(chosen['name'])} ({html.escape(chosen['series'])})»</b> 🃏\n"
        f"✨ Редкость: {RARITY_RU[chosen['rarity']]} {RARITY_EMOJI[chosen['rarity']]} ✨\n"
        f"💰 Джобсы: +{award} 💰\n"
        f"<i>«{html.escape(chosen['quote'])}»</i>"
    )
    try:
        await message.answer_photo(photo=chosen["image_url"], caption=caption, parse_mode=ParseMode.HTML)
    except Exception:
        await message.answer(caption, parse_mode=ParseMode.HTML)
# ================= ПОРОШОК (/powder) =================

@dp.message(Command("powder"))
async def cmd_powder(message: Message):
    if await check_antispam(message, bot): return
    uid = message.from_user.id
    register_user(uid, message.from_user.username, message.from_user.first_name)
    await render_powder_menu(uid, message)

async def render_powder_menu(uid, msg_or_cb):
    u_res = supabase.table("users").select("powder_balance, jobs_balance").eq("user_id", uid).execute()
    powder = u_res.data[0].get("powder_balance", 0)
    
    cards_res = supabase.table("user_cards").select("card_id, rarity").eq("user_id", uid).execute()
    
    counts = defaultdict(int)
    rarity_dups = defaultdict(int)
    total_dups = 0

    for r in cards_res.data:
        counts[(r["card_id"], r["rarity"])] += 1

    for (cid, rarity), cnt in counts.items():
        if cnt > 1:
            dups = cnt - 1
            rarity_dups[rarity] += dups
            total_dups += dups

    text = (
        "🧪 <b>Станция переработки карт</b>\n"
        "Превратите лишние дубликаты в карточный порошок.\n\n"
        f"📊 Ваши запасы: <b>{powder} ✨</b> порошка\n"
        f"⚠️ <i>Пошлина за переработку: 50 🪙 за карту.</i>"
    )

    buttons = []
    for r in RARITY_ORDER:
        if rarity_dups[r] > 0:
            buttons.append([InlineKeyboardButton(text=f"{RARITY_EMOJI[r]} Сжечь все {RARITY_RU[r]} дубликаты ({rarity_dups[r]} шт)", callback_data=f"burn:{uid}:{r}")])

    if total_dups > 0:
        buttons.append([InlineKeyboardButton(text="🔥 ПЕРЕПРАВИТЬ ВСЕ ДУБЛИКАТЫ РАЗОМ", callback_data=f"burn:{uid}:all")])
    buttons.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(msg_or_cb, Message):
        await msg_or_cb.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await msg_or_cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("burn:"))
async def cb_burn(cb: CallbackQuery):
    _, uid_s, mode = cb.data.split(":")
    uid = int(uid_s)
    if not await verify_cb_owner(cb, uid): return

    u_res = supabase.table("users").select("jobs_balance, powder_balance").eq("user_id", uid).execute()
    jobs = u_res.data[0].get("jobs_balance", 0)
    powder = u_res.data[0].get("powder_balance", 0)

    cards_res = supabase.table("user_cards").select("id, card_id, rarity").eq("user_id", uid).execute()
    
    card_groups = defaultdict(list)
    for row in cards_res.data:
        card_groups[row["card_id"]].append(row)

    to_burn = []
    for cid, items in card_groups.items():
        if len(items) > 1:
            for it in items[1:]:
                if mode == "all" or it["rarity"] == mode:
                    to_burn.append(it)

    if not to_burn:
        await cb.answer("Нет дубликатов для сжигания!", show_alert=True)
        return

    fee = len(to_burn) * 50
    if jobs < fee:
        await cb.answer(f"❌ Недостаточно средств! Требуется {fee} 🪙.", show_alert=True)
        return

    gained_powder = sum(RARITY_POWDER[it["rarity"]] for it in to_burn)
    
    for b_item in to_burn:
        supabase.table("user_cards").delete().eq("id", b_item["id"]).execute()

    supabase.table("users").update({
        "jobs_balance": jobs - fee,
        "powder_balance": powder + gained_powder
    }).eq("user_id", uid).execute()

    await cb.answer(f"🔥 Сожжено {len(to_burn)} карт! Получено +{gained_powder} ✨ порошка.", show_alert=True)
    await render_powder_menu(uid, cb)

# ================= ЧЕРНЫЙ РЫНОК (/blackmarket) =================

@dp.message(Command("blackmarket"))
async def cmd_bm(message: Message):
    if await check_antispam(message, bot): return
    uid = message.from_user.id
    register_user(uid, message.from_user.username, message.from_user.first_name)
    await render_bm(uid, message)

async def render_bm(uid, msg_or_cb):
    u_res = supabase.table("users").select("*").eq("user_id", uid).execute()
    u_data = u_res.data[0]
    powder = u_data.get("powder_balance", 0)

    boost_active = False
    if u_data.get("boost_until"):
        boost_active = datetime.fromisoformat(u_data["boost_until"].replace('Z', '+00:00')) > datetime.now(timezone.utc)

    text = (
        "🏴‍☠️ <b>Черный рынок Джоба</b>\n\n"
        f"📊 Ваш баланс: <b>{powder} ✨</b> порошка\n"
        "──────────────────────────────\n"
        "⚡ <b>Продюсерский буст (х1.5 на 24 часа)</b> — 300 ✨\n"
        "🍀 <b>Ролл 2х удачи</b> — 200 ✨ (Лимит: 3/сут)\n"
        "🔥 <b>Ролл 5х удачи</b> — 700 ✨ (Лимит: 1/сут)"
    )

    btn_boost = InlineKeyboardButton(text="⚡ Буст активен" if boost_active else "🛒 Купить буст (300 ✨)", callback_data=f"buy_bm:{uid}:boost")
    btn_2x = InlineKeyboardButton(text=f"🛒 Купить 2х-ролл (Осталось {u_data.get('luck_rolls_2x', 0)}/3)", callback_data=f"buy_bm:{uid}:2x")
    btn_5x = InlineKeyboardButton(text=f"🛒 Купить 5х-ролл (Осталось {u_data.get('luck_rolls_5x', 0)}/1)", callback_data=f"buy_bm:{uid}:5x")

    kb = InlineKeyboardMarkup(inline_keyboard=[[btn_boost], [btn_2x], [btn_5x], [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")]])
    
    if isinstance(msg_or_cb, Message):
        await msg_or_cb.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await msg_or_cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_bm:"))
async def cb_buy_bm(cb: CallbackQuery):
    _, uid_s, item = cb.data.split(":")
    uid = int(uid_s)
    if not await verify_cb_owner(cb, uid): return

    u_res = supabase.table("users").select("*").eq("user_id", uid).execute()
    u_data = u_res.data[0]
    powder = u_data.get("powder_balance", 0)

    if item == "boost":
        if u_data.get("boost_until") and datetime.fromisoformat(u_data["boost_until"].replace('Z', '+00:00')) > datetime.now(timezone.utc):
            await cb.answer("❌ У вас уже активен буст!", show_alert=True); return
        if powder < 300:
            await cb.answer("❌ Недостаточно порошка!", show_alert=True); return
        new_until = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        supabase.table("users").update({"powder_balance": powder - 300, "boost_until": new_until}).eq("user_id", uid).execute()
        await cb.answer("✅ Буст активирован на 24 часа!", show_alert=True)

    elif item == "2x":
        if u_data.get("luck_rolls_2x", 0) >= 3:
            await cb.answer("❌ Достигнут лимит на сегодня!", show_alert=True); return
        if powder < 200:
            await cb.answer("❌ Недостаточно порошка!", show_alert=True); return
        supabase.table("users").update({"powder_balance": powder - 200, "luck_rolls_2x": u_data.get("luck_rolls_2x", 0) + 1}).eq("user_id", uid).execute()
        await cb.answer("✅ Куплен 2х-ролл!", show_alert=True)

    elif item == "5x":
        if u_data.get("luck_rolls_5x", 0) >= 1:
            await cb.answer("❌ Достигнут лимит на сегодня!", show_alert=True); return
        if powder < 700:
            await cb.answer("❌ Недостаточно порошка!", show_alert=True); return
        supabase.table("users").update({"powder_balance": powder - 700, "luck_rolls_5x": 1}).eq("user_id", uid).execute()
        await cb.answer("✅ Куплен 5х-ролл!", show_alert=True)

    await render_bm(uid, cb)

# ================= МАГАЗИН (/shop) =================

@dp.message(Command("shop"))
async def cmd_shop(message: Message):
    if await check_antispam(message, bot): return
    uid = message.from_user.id
    register_user(uid, message.from_user.username, message.from_user.first_name)
    await render_shop_main(uid, message)

async def render_shop_main(uid, msg_or_cb):
    text = "🛒 <b>Магазин Джоба</b>\nВыберите категорию товаров:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷️ Титулы за Джобсы", callback_data=f"shop_cat:{uid}:titles")],
        [InlineKeyboardButton(text="🖼️ Эмодзи-рамки", callback_data=f"shop_cat:{uid}:frames")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")]
    ])
    if isinstance(msg_or_cb, Message):
        await msg_or_cb.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await msg_or_cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("shop_cat:"))
async def cb_shop_cat(cb: CallbackQuery):
    _, uid_s, cat = cb.data.split(":")
    uid = int(uid_s)
    if not await verify_cb_owner(cb, uid): return

    u_res = supabase.table("users").select("jobs_balance, unlocked_titles, active_frame").eq("user_id", uid).execute()
    jobs = u_res.data[0].get("jobs_balance", 0)
    unlocked = u_res.data[0].get("unlocked_titles") or []

    if cat == "titles":
        text = f"🏷️ <b>Титулы за Джобсы</b>\nВаш баланс: {jobs} 🪙\nПокупаются навсегда!"
        buttons = []
        for key, info in TITLES_SHOP.items():
            btn_text = f"{info['name']} (✅ Куплено)" if key in unlocked else f"{info['name']} — {info['price']} 🪙"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"buy_title:{uid}:{key}")])
        buttons.append([InlineKeyboardButton(text="◀️ Назад в магазин", callback_data=f"shop_back:{uid}")])
        buttons.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")])
        await cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    
    elif cat == "frames":
        text = f"🖼️ <b>Эмодзи-рамки профиля</b>\nВаш баланс: {jobs} 🪙\n⚠️ <i>Механика: при смене или возврате старой рамки оплата списывается заново!</i>"
        buttons = [
            [InlineKeyboardButton(text="🛡️ Обычные (500 🪙)", callback_data=f"frame_sub:{uid}:normal")],
            [InlineKeyboardButton(text="🌚 Парные (750 🪙)", callback_data=f"frame_sub:{uid}:pair")],
            [InlineKeyboardButton(text="🤡 Токсичные / Мемные (1 000 🪙)", callback_data=f"frame_sub:{uid}:toxic")],
            [InlineKeyboardButton(text="🐲 Элитные (3 000 🪙)", callback_data=f"frame_sub:{uid}:elite")],
            [InlineKeyboardButton(text="◀️ Назад в магазин", callback_data=f"shop_back:{uid}")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")]
        ]
        await cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("shop_back:"))
async def cb_shop_back(cb: CallbackQuery):
    uid = int(cb.data.split(":")[1])
    if not await verify_cb_owner(cb, uid): return
    await render_shop_main(uid, cb)

@dp.callback_query(F.data.startswith("frame_sub:"))
async def cb_frame_sub(cb: CallbackQuery):
    _, uid_s, sub_cat = cb.data.split(":")
    uid = int(uid_s)
    if not await verify_cb_owner(cb, uid): return

    u_res = supabase.table("users").select("jobs_balance").eq("user_id", uid).execute()
    jobs = u_res.data[0].get("jobs_balance", 0)

    cat_titles = {"normal": "Обычные (500 🪙)", "pair": "Парные (750 🪙)", "toxic": "Токсичные / Мемные (1 000 🪙)", "elite": "Элитные (3 000 🪙)"}
    text = f"🖼️ <b>Рамки: {cat_titles.get(sub_cat, '')}</b>\nВаш баланс: {jobs} 🪙\nНажмите для покупки и применения:"

    buttons = []
    for key, info in FRAMES_SHOP.items():
        if info["cat"] == sub_cat:
            if info["type"] == "single":
                label = f"{info['emoji']} — {info['price']} 🪙 [🛒 Купить]"
            else:
                label = f"{info['emoji_left']}...{info['emoji_right']} — {info['price']} 🪙 [🛒 Купить]"
            buttons.append([InlineKeyboardButton(text=label, callback_data=f"buy_frame:{uid}:{key}")])

    buttons.append([InlineKeyboardButton(text="◀️ К выбору категорий", callback_data=f"shop_cat:{uid}:frames")])
    buttons.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")])
    await cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("buy_title:"))
async def cb_buy_title(cb: CallbackQuery):
    _, uid_s, key = cb.data.split(":")
    uid = int(uid_s)
    if not await verify_cb_owner(cb, uid): return

    info = TITLES_SHOP[key]
    u_res = supabase.table("users").select("jobs_balance, unlocked_titles").eq("user_id", uid).execute()
    jobs = u_res.data[0].get("jobs_balance", 0)
    unlocked = u_res.data[0].get("unlocked_titles") or []

    if key in unlocked:
        await cb.answer("У вас уже куплен этот титул!", show_alert=True); return
    if jobs < info["price"]:
        await cb.answer("❌ Недостаточно джобсов!", show_alert=True); return

    unlocked.append(key)
    supabase.table("users").update({"jobs_balance": jobs - info["price"], "unlocked_titles": unlocked, "active_title": info["name"]}).eq("user_id", uid).execute()
    await cb.answer(f"✅ Вы успешно купили титул: {info['name']}!", show_alert=True)

@dp.callback_query(F.data.startswith("buy_frame:"))
async def cb_buy_frame(cb: CallbackQuery):
    _, uid_s, key = cb.data.split(":")
    uid = int(uid_s)
    if not await verify_cb_owner(cb, uid): return

    info = FRAMES_SHOP[key]
    u_res = supabase.table("users").select("jobs_balance").eq("user_id", uid).execute()
    jobs = u_res.data[0].get("jobs_balance", 0)

    if jobs < info["price"]:
        await cb.answer(f"❌ Недостаточно джобсов! Требуется {info['price']} 🪙.", show_alert=True); return

    # Списываем стоимость (платят каждый раз при смене/покупке согласно ТЗ)
    supabase.table("users").update({
        "jobs_balance": jobs - info["price"],
        "active_frame": key
    }).eq("user_id", uid).execute()

    await cb.answer(f"✅ Рамка успешно приобретена и установлена (-{info['price']} 🪙)!", show_alert=True)
# ================= КАЗИНО (/casino) =================

@dp.message(Command("casino"))
async def cmd_casino(message: Message):
    if await check_antispam(message, bot): return
    uid = message.from_user.id
    register_user(uid, message.from_user.username, message.from_user.first_name)
    await render_casino(uid, message)

async def render_casino(uid, msg_or_cb):
    c_res = supabase.table("casino_bank").select("total_bank").eq("id", 1).execute()
    bank = c_res.data[0].get("total_bank", 0) if c_res.data else 0

    u_res = supabase.table("users").select("casino_balance").eq("user_id", uid).execute()
    c_bal = u_res.data[0].get("casino_balance", 0)

    text = (
        "🎰 <b>Казино Джоба</b>\n"
        f"🏦 <b>Казна Джоба:</b> {bank} 🪙\n"
        f"💳 <b>Ваш баланс в казино:</b> {c_bal} 🪙\n"
        "──────────────────────────────\n"
        "• /deposit [сумма] — пополнить счет\n"
        "• /withdraw [сумма] — вывод (Комиссия 15%)\n"
        "• /check_casino — проверка казны (для админов)\n"
        "• Ставки: от 100 до 1 000 🪙 (Лимит 10/день)"
    )

    buttons = [
        [InlineKeyboardButton(text="100 🪙", callback_data=f"bet:{uid}:100"), InlineKeyboardButton(text="250 🪙", callback_data=f"bet:{uid}:250")],
        [InlineKeyboardButton(text="500 🪙", callback_data=f"bet:{uid}:500"), InlineKeyboardButton(text="1000 🪙", callback_data=f"bet:{uid}:1000")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")]
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(msg_or_cb, Message):
        await msg_or_cb.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await msg_or_cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.message(Command("check_casino"))
async def cmd_check_casino(message: Message):
    if not is_admin(message.from_user.id): return
    c_res = supabase.table("casino_bank").select("total_bank").eq("id", 1).execute()
    bank = c_res.data[0].get("total_bank", 0) if c_res.data else 0
    await message.answer(f"🏦 <b>Состояние казны казино:</b> {bank} 🪙", parse_mode=ParseMode.HTML)

@dp.message(Command("deposit"))
async def cmd_deposit(message: Message):
    if await check_antispam(message, bot): return
    uid = message.from_user.id
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("❌ Используй: /deposit [сумма]"); return
    
    amount = int(args[1])
    u_res = supabase.table("users").select("jobs_balance, casino_balance").eq("user_id", uid).execute()
    jobs = u_res.data[0].get("jobs_balance", 0)
    
    if jobs < amount:
        await message.answer("❌ Недостаточно джобсов!"); return

    supabase.table("users").update({
        "jobs_balance": jobs - amount,
        "casino_balance": u_res.data[0].get("casino_balance", 0) + amount
    }).eq("user_id", uid).execute()
    await message.answer(f"✅ Баланс казино пополнен на {amount} 🪙!")

@dp.message(Command("withdraw"))
async def cmd_withdraw(message: Message):
    if await check_antispam(message, bot): return
    uid = message.from_user.id
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("❌ Используй: /withdraw [сумма]"); return

    amount = int(args[1])
    u_res = supabase.table("users").select("jobs_balance, casino_balance").eq("user_id", uid).execute()
    c_bal = u_res.data[0].get("casino_balance", 0)

    if c_bal < amount:
        await message.answer("❌ Недостаточно средств на балансе казино!"); return

    # Проверка: на главного админа (ADMIN_ID) комиссия с игрового счета казны не действует
    if uid == ADMIN_ID:
        fee = 0
        to_user = amount
    else:
        fee = int(amount * 0.15)
        to_user = amount - fee
        c_bank = supabase.table("casino_bank").select("total_bank").eq("id", 1).execute()
        curr_bank = c_bank.data[0]["total_bank"] if c_bank.data else 0
        supabase.table("casino_bank").update({"total_bank": curr_bank + fee}).eq("id", 1).execute()

    supabase.table("users").update({
        "casino_balance": c_bal - amount,
        "jobs_balance": u_res.data[0].get("jobs_balance", 0) + to_user
    }).eq("user_id", uid).execute()

    await message.answer(f"✅ Выведено {to_user} 🪙 (Комиссия: {fee} 🪙).")

@dp.callback_query(F.data.startswith("bet:"))
async def cb_bet(cb: CallbackQuery):
    _, uid_s, bet_s = cb.data.split(":")
    uid, bet = int(uid_s), int(bet_s)
    if not await verify_cb_owner(cb, uid): return

    u_res = supabase.table("users").select("casino_balance, casino_bets_today").eq("user_id", uid).execute()
    c_bal = u_res.data[0].get("casino_balance", 0)
    bets_today = u_res.data[0].get("casino_bets_today", 0)

    if bets_today >= 10:
        await cb.answer("❌ Лимит 10 ставок в день исчерпан!", show_alert=True); return
    if c_bal < bet:
        await cb.answer("❌ Недостаточно средств в казино! Пополните счет: /deposit", show_alert=True); return

    r = random.random()
    c_bank = supabase.table("casino_bank").select("total_bank").eq("id", 1).execute()
    curr_bank = c_bank.data[0]["total_bank"] if c_bank.data else 0

    if r <= 0.62:
        new_c_bal = c_bal - bet
        supabase.table("casino_bank").update({"total_bank": curr_bank + bet}).eq("id", 1).execute()
        res_text = "❌ Проигрыш! Средства ушли в казну."
        slots = "[ 🍒 | 🍋 | 🔔 ]"
    elif r <= 0.87:
        new_c_bal = c_bal
        res_text = "⚖️ Возврат ставки."
        slots = "[ 🍒 | 🍒 | 🍋 ]"
    elif r <= 0.97:
        new_c_bal = c_bal + bet
        res_text = f"✅ Выигрыш x2: +{bet*2} 🪙!"
        slots = "[ 🍋 | 🍋 | 🍋 ]"
    elif r <= 0.99:
        new_c_bal = c_bal + (bet * 2)
        res_text = f"🎬 КАССОВЫЙ ХИТ x3: +{bet*3} 🪙!"
        slots = "[ 7️⃣ | 7️⃣ | 7️⃣ ]"
    else:
        new_c_bal = c_bal + (bet * 4)
        res_text = f"🔥 ДЖЕКПОТ x5: +{bet*5} 🪙!"
        slots = "[ 🃏 | 🃏 | 🃏 ]"

    supabase.table("users").update({"casino_balance": new_c_bal, "casino_bets_today": bets_today + 1}).eq("user_id", uid).execute()

    msg_text = (
        f"🎲 Ставка: {bet} 🪙\n"
        f"{slots}\n"
        f"{res_text}\n"
        f"• Ваш баланс в казино: {new_c_bal} 🪙"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")]])
    await cb.message.edit_text(msg_text, parse_mode=ParseMode.HTML, reply_markup=kb)

# ================= ПРОФИЛЬ (/profile) =================

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    if await check_antispam(message, bot): return
    uid = message.from_user.id
    register_user(uid, message.from_user.username, message.from_user.first_name)
    await render_profile(uid, message)

async def render_profile(uid, msg_or_cb):
    u_res = supabase.table("users").select("*").eq("user_id", uid).execute()
    u_data = u_res.data[0]

    cards_res = supabase.table("user_cards").select("rarity").eq("user_id", uid).execute()
    total_cards = len(cards_res.data)
    
    rarity_counts = defaultdict(int)
    for row in cards_res.data:
        rarity_counts[row["rarity"]] += 1

    rarity_str = " | ".join([f"{RARITY_EMOJI[r]} {RARITY_RU[r]}: {rarity_counts[r]}" for r in RARITY_ORDER if rarity_counts[r] > 0])

    boost_text = "Отсутствует"
    if u_data.get("boost_until"):
        b_time = datetime.fromisoformat(u_data["boost_until"].replace('Z', '+00:00'))
        if b_time > datetime.now(timezone.utc):
            rem = b_time - datetime.now(timezone.utc)
            boost_text = f"Активен еще {rem.seconds // 3600} ч. {(rem.seconds % 3600) // 60} мин."

    name_disp = format_user_display(u_data)
    title_disp = u_data.get("active_title") or "Отсутствует"

    text = (
        f"👤 <b>Профиль игрока:</b> [ {name_disp} ]\n"
        f"🏷️ <b>Титул:</b> [ {html.escape(title_disp)} ]\n"
        f"⏳ <b>Активные эффекты:</b>\n• ⚡ Продюсерский буст (х1.5): {boost_text}\n\n"
        f"📊 <b>Статистика коллекции:</b>\n"
        f"• Всего карт: {total_cards}\n"
        f"Детализация по редкости (динамически):\n• {rarity_str if rarity_str else 'Нет карт'}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Достижения", callback_data=f"achievements:{uid}")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")]
    ])

    if isinstance(msg_or_cb, Message):
        await msg_or_cb.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await msg_or_cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("achievements:"))
async def cb_achievements(cb: CallbackQuery):
    uid = int(cb.data.split(":")[1])
    if not await verify_cb_owner(cb, uid): return

    cards_res = supabase.table("user_cards").select("id", count="exact").eq("user_id", uid).execute()
    total_cards = cards_res.count or 0

    u_res = supabase.table("users").select("null_cards_count, username, first_name").eq("user_id", uid).execute()
    u_data = u_res.data[0] if u_res.data else {}
    null_count = u_data.get("null_cards_count", 0)

    achievements = []
    if total_cards >= 500:
        achievements.append("🃏 <b>The Emperor of Cards</b>\n└ Условие получения: Собрать в общей сумме 500 карт за всё время.")
    if null_count >= 3:
        achievements.append("🎰 <b>Devil's Luck</b>\n└ Условие получения: Выбить 3 Null-карты за всё время.")

    boss_name = u_data.get("username") if u_data.get("username") and u_data.get("username") != "no_name" else (u_data.get("first_name") or "boss")

    if achievements:
        msg_text = f"🏆 <b>Достижения игрока: {html.escape(boss_name)}</b>\n\n• " + ("\n• ".join(achievements))
    else:
        msg_text = f"🏆 <b>Достижения игрока: {html.escape(boss_name)}</b>\n\n❌ У вас пока нет разблокированных достижений. Крутите карты и испытывайте удачу!"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в профиль", callback_data=f"back_profile:{uid}")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")]
    ])
    await cb.message.edit_text(msg_text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("back_profile:"))
async def cb_back_profile(cb: CallbackQuery):
    uid = int(cb.data.split(":")[1])
    if not await verify_cb_owner(cb, uid): return
    await render_profile(uid, cb)

# ================= ТОП =================

@dp.message(Command("topjobs"))
async def top_jobs(message: Message):
    if await check_antispam(message, bot): return
    res = supabase.table("users").select("*").eq("is_banned", False).gt("jobs_balance", 0).order("jobs_balance", desc=True).limit(30).execute()
    if not res.data:
        await message.answer("💰 Пока никто не заработал джобсы. Будь первым!")
        return

    text = "🏆 <b>Топ 30 по джобсам:</b>\n\n"
    medals = {1:"🥇", 2:"🥈", 3:"🥉"}
    for i, row in enumerate(res.data, 1):
        name_display = format_user_display(row)
        title = f" [{row['active_title']}]" if row.get("active_title") else ""
        text += f"{medals.get(i, f'{i}.')} <b>{name_display}</b>{html.escape(title)} — {row.get('jobs_balance', 0)} 🪙\n"

    await message.answer(text, parse_mode=ParseMode.HTML)
# ========== АДМИН-КОМАНДЫ ==========

def get_target_user(query_str):
    query_clean = query_str.lstrip('@').strip()
    if query_clean.isdigit():
        res = supabase.table("users").select("*").eq("user_id", int(query_clean)).execute()
    else:
        res = supabase.table("users").select("*").ilike("username", query_clean).execute()
    return res.data[0] if res.data else None

@dp.message(Command("check_user"))
async def check_user(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /check_user <id_или_username>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    uid = user["user_id"]
    status = "⛔️ ЗАБАНЕН" if user.get("is_banned") else ("🧊 ЗАМОРОЖЕН" if user.get("is_frozen") else "🟢 Активен")
    
    spam_res = supabase.table("spam_logs").select("id", count="exact").eq("user_id", uid).execute()
    spam_cnt = spam_res.count or 0
    
    cards_res = supabase.table("user_cards").select("id", count="exact").eq("user_id", uid).execute()
    cards_cnt = cards_res.count or 0
    
    top_res = supabase.table("users").select("user_id", count="exact").gt("jobs_balance", user.get("jobs_balance", 0)).execute()
    top_pos = (top_res.count or 0) + 1

    ok_roll, rem_time = can_roll(uid)
    roll_status_display = "🟢 Готов к роллу" if ok_roll else f"🔴 Не готов (осталось {rem_time})"

    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
    msg = (
        f"📋 <b>ИНСПЕКЦИЯ ПОЛЬЗОВАТЕЛЯ</b>\n──────────────────────\n"
        f"👤 Игрок: {html.escape(uname_display)} (ID: <code>{uid}</code>)\n"
        f"💰 Баланс: <b>{user.get('jobs_balance', 0)}</b> джобсов | 🏆 Топ: #{top_pos} | 🎴 Карт: {cards_cnt}\n"
        f"🎲 Общее кол-во роллов: <b>{cards_cnt}</b>\n"
        f"⏳ Статус ролла: <b>{roll_status_display}</b>\n"
        f"🧊 Статус: <b>{status}</b>\n"
        f"🚨 Нарушения: <b>{spam_cnt}</b> спам-триггеров (Подробно: /logs_user {uid})"
    )
    await message.answer(msg, parse_mode=ParseMode.HTML)

@dp.message(Command("logs_user"))
async def logs_user(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /logs_user <id_или_username>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    uid = user["user_id"]
    spams = supabase.table("spam_logs").select("created_at, action_taken").eq("user_id", uid).order("id", desc=True).limit(5).execute()
    two_days_ago = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    recent_rolls = supabase.table("user_cards").select("card_name, rarity, obtained_at").eq("user_id", uid).gte("obtained_at", two_days_ago).order("id", desc=True).limit(10).execute()

    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
    msg = f"📊 <b>ПОЛНЫЕ ЛОГИ:</b> {html.escape(uname_display)} (ID: <code>{uid}</code>)\n──────────────────────\n\n🚨 <b>ИСТОРИЯ СПАМА:</b>\n"
    if not spams.data:
        msg += "• Нарушений не зафиксировано.\n"
    else:
        for s in spams.data:
            msg += f"• {s.get('created_at')[:16]} | {html.escape(str(s.get('action_taken')))}\n"
            
    msg += "\n🎲 <b>РОЛЛЫ ЗА 48 ЧАСОВ:</b>\n"
    if not recent_rolls.data:
        msg += "• Нет роллов за последние 48 часов.\n"
    else:
        for r in recent_rolls.data:
            emoji = RARITY_EMOJI.get(r.get('rarity'), "🃏")
            ru_rar = RARITY_RU.get(r.get('rarity'), r.get('rarity'))
            msg += f"• {r.get('obtained_at')[:16]} — {emoji} [{ru_rar}] {html.escape(r.get('card_name'))}\n"

    await message.answer(msg, parse_mode=ParseMode.HTML)

@dp.message(Command("freeze"))
async def cmd_freeze(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_frozen": True, "freeze_reason": "Ручная заморозка"}).eq("user_id", user["user_id"]).execute()
        await message.answer("🧊 Пользователь заморожен.")

@dp.message(Command("unfreeze"))
async def cmd_unfreeze(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_frozen": False, "freeze_reason": None}).eq("user_id", user["user_id"]).execute()
        await message.answer("🔓 Пользователь разморожен.")

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_banned": True}).eq("user_id", user["user_id"]).execute()
        await message.answer("⛔️ Пользователь забанен.")

@dp.message(Command("unban"))
async def cmd_unban(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_banned": False}).eq("user_id", user["user_id"]).execute()
        await message.answer("✅ Пользователь разбанен.")

@dp.message(Command("rc"))
async def cmd_rc(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"last_roll_time": None}).eq("user_id", user["user_id"]).execute()
        await message.answer("⏳ Таймер ролла сброшен.")

@dp.message(Command("reset_user"))
async def reset_user(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if not user: return
    if user["user_id"] == ADMIN_ID and message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Нельзя сбрасывать прогресс главного разработчика!"); return
    supabase.table("user_cards").delete().eq("user_id", user["user_id"]).execute()
    supabase.table("users").update({"jobs_balance": 0, "last_roll_time": None}).eq("user_id", user["user_id"]).execute()
    await message.answer("✅ Прогресс пользователя сброшен.")

@dp.message(Command("give_jobs"))
async def give_jobs(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 3: return
    user = get_target_user(args[1])
    if not user: return
    try: amount = int(args[2])
    except: return
    new_jobs = user.get("jobs_balance", 0) + amount
    supabase.table("users").update({"jobs_balance": new_jobs}).eq("user_id", user["user_id"]).execute()
    await message.answer(f"✅ Выдано {amount} джобсов.")

@dp.message(Command("take_jobs"))
async def take_jobs(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 3: return
    user = get_target_user(args[1])
    if not user: return
    if user["user_id"] == ADMIN_ID and message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Нельзя отнимать джобсы у главного разработчика!"); return
    try: amount = int(args[2])
    except: return
    new_jobs = max(0, user.get("jobs_balance", 0) - amount)
    supabase.table("users").update({"jobs_balance": new_jobs}).eq("user_id", user["user_id"]).execute()
    await message.answer(f"✅ Отнято джобсов. Баланс: {new_jobs}.")

@dp.message(Command("rig_roll"))
async def rig_roll(message: Message):
    if message.from_user.id != ADMIN_ID: return
    text_payload = message.text.replace("/rig_roll", "").strip()
    parts = text_payload.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Используй: /rig_roll <id_или_username> <ID_карт_через_запятую>"); return
    user = get_target_user(parts[0])
    if not user:
        await message.answer("❌ Пользователь не найден."); return
    try:
        card_ids = [int(cid.strip()) for cid in parts[1].replace(',', ' ').split() if cid.strip().isdigit()]
    except:
        await message.answer("❌ Неверный формат ID карт."); return
    
    target_uid = user["user_id"]
    if target_uid not in forced_next_cards:
        forced_next_cards[target_uid] = []
    forced_next_cards[target_uid].extend(card_ids)
    await message.answer(f"⚙️ Подкручено! Игроку выпадут карты с ID: {card_ids}")

@dp.message(Command("give_card"))
async def give_card(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 3: return
    user = get_target_user(args[1])
    if not user: return
    query = ' '.join(args[2:]).strip()
    card = CARDS_DICT.get(int(query)) if query.isdigit() else None
    if not card:
        for c in CARDS_DATA:
            if query.lower() in c[1].lower():
                card = CARDS_DICT[c[0]]; break
    if not card:
        await message.answer("❌ Карта не найдена."); return
    
    now_iso = datetime.now(timezone.utc).isoformat()
    supabase.table("user_cards").insert({"user_id": user["user_id"], "card_id": card["id"], "card_name": card["name"], "rarity": card["rarity"], "obtained_at": now_iso}).execute()
    await message.answer(f"✅ Карта «{card['name']}» успешно выдана игроку!")

# НОВАЯ КОМАНДА: Выдача донатных титулов и эксклюзива разработчика (/give_title @user [уровень_или_dev])
@dp.message(Command("give_title"))
async def give_title(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Используй: /give_title <id_или_username> <уровень_1-3 или dev>")
        return
    
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    param = args[2].lower()
    target_uid = user["user_id"]
    
    if param == "dev":
        # Эксклюзив Создателя: Личный несгораемый титул разработчика
        new_title = CREATOR_TITLE
    elif param.isdigit():
        lvl = int(param)
        if lvl in DONATE_TITLES:
            new_title = DONATE_TITLES[lvl]["name"]
        else:
            await message.answer("❌ Неверный уровень донатного титула (доступны 1, 2, 3)."); return
    else:
        await message.answer("❌ Неверный параметр. Используйте цифру от 1 до 3 или 'dev'."); return

    supabase.table("users").update({"active_title": new_title}).eq("user_id", target_uid).execute()
    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'Игрок')
    await message.answer(f"👑 Пользователю {html.escape(uname_display)} успешно выдан титул: <b>{new_title}</b>", parse_mode=ParseMode.HTML)

@dp.message(Command("add_admin"))
async def cmd_add_admin(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_admin": True}).eq("user_id", user["user_id"]).execute()
        await message.answer("👑 Пользователь назначен администратором.")

@dp.message(Command("remove_admin"))
async def cmd_remove_admin(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_admin": False}).eq("user_id", user["user_id"]).execute()
        await message.answer("🚫 Права администратора забраны.")

async def main():
    print("✅ Джоб v2.3 полностью готов и запущен!")
    await dp.start_polling(bot)

keep_alive()

if __name__ == "__main__":
    asyncio.run(main())