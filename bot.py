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
    return "Бот Джоб работает"

def run_web():
    port = int(os.environ.get('PORT', 5000))
    app_web.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()
# =========================================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6990974323  # Твой Telegram ID
LOG_CHAT_ID = -5336201694  # ID твоей приватной группы с логами

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# База карт
CARDS_DATA = [
    {"card_id": "1", "name": "Хоумлендер", "series": "The Boys", "rarity": "null", "image_url": "https://i.postimg.cc/R08Z0qmj/IMG-20260612-221053-063.jpg", "quote": "Я здесь бог.", "jobs_award": 3333},
    {"card_id": "2", "name": "Мясник", "series": "The Boys", "rarity": "mythic", "image_url": "https://i.postimg.cc/pdb7CH2M/IMG-20260612-221039-579.jpg", "quote": "Мы спасём эту чёртову страну!", "jobs_award": 2332},
    {"card_id": "3", "name": "Декстер Морган", "series": "Dexter", "rarity": "mythic", "image_url": "https://i.postimg.cc/tgczkddt/IMG-20260612-221039-343.jpg", "quote": "Сегодня ночью — охота.", "jobs_award": 1777},
    {"card_id": "4", "name": "Тони Сопрано", "series": "The Sopranos", "rarity": "mythic", "image_url": "https://i.postimg.cc/NM7kthqK/IMG-20260612-221045-473.jpg", "quote": "Я пришёл за утками.", "jobs_award": 1919},
    {"card_id": "5", "name": "Ганнибал Лектер", "series": "Hannibal", "rarity": "mythic", "image_url": "https://i.postimg.cc/Dzn6myv5/IMG-20260612-221039-738.jpg", "quote": "Печень — с бобами.", "jobs_award": 2700},
    {"card_id": "6", "name": "Хайзенберг", "series": "Breaking Bad", "rarity": "mythic", "image_url": "https://i.postimg.cc/gJknx1L6/IMG-20260612-221052-546.jpg", "quote": "Я — тот, кто стучит.", "jobs_award": 2500},
    {"card_id": "7", "name": "Королева Мэйв", "series": "The Boys", "rarity": "legendary", "image_url": "https://i.postimg.cc/zBP4nRvP/IMG-20260612-221045-477.jpg", "quote": "Хватит притворяться, Хоумлендер.", "jobs_award": 1636},
    {"card_id": "8", "name": "Джесси Пинкман", "series": "Breaking Bad", "rarity": "legendary", "image_url": "https://i.postimg.cc/CLvnbhs1/IMG-20260612-221039-831.jpg", "quote": "Наука, bitch!", "jobs_award": 1455},
    {"card_id": "9", "name": "Тринити-киллер", "series": "Dexter", "rarity": "legendary", "image_url": "https://i.postimg.cc/vHmLJSPf/IMG-20260612-221053-114.jpg", "quote": "Всё кончено, Декстер.", "jobs_award": 800},
    {"card_id": "10", "name": "Сол Гудман", "series": "Better Call Saul", "rarity": "legendary", "image_url": "https://i.postimg.cc/KzswbyDB/IMG-20260612-221045-610.jpg", "quote": "Позвоните Солу!", "jobs_award": 1321},
    {"card_id": "11", "name": "Уилл Грэм", "series": "Hannibal", "rarity": "legendary", "image_url": "https://i.postimg.cc/rmc5Qh0W/IMG-20260612-221053-281.jpg", "quote": "Это красиво.", "jobs_award": 1111},
    {"card_id": "12", "name": "Энни (Старлайт)", "series": "The Boys", "rarity": "epic", "image_url": "https://i.postimg.cc/SRV0Jt8d/IMG-20260612-221052-889.jpg", "quote": "Я верю в добро, даже если его почти не осталось.", "jobs_award": 609},
    {"card_id": "13", "name": "Дебра Морган", "series": "Dexter", "rarity": "epic", "image_url": "https://i.postimg.cc/TYvCBczN/IMG-20260612-221039-420.jpg", "quote": "Ты мне отвратителен, но я люблю тебя, брат.", "jobs_award": 512},
    {"card_id": "14", "name": "Кристофер Молтисанти", "series": "The Sopranos", "rarity": "epic", "image_url": "https://i.postimg.cc/ZRCJtmdz/IMG-20260612-221045-723.jpg", "quote": "Моя судьба — кино, а не это дерьмо.", "jobs_award": 464},
    {"card_id": "15", "name": "Ким Уэкслер", "series": "Better Call Saul", "rarity": "epic", "image_url": "https://i.postimg.cc/NFS36wKZ/IMG-20260612-221045-353.jpg", "quote": "Ты в деле, Сол.", "jobs_award": 400},
    {"card_id": "16", "name": "Гус Фринг", "series": "Breaking Bad", "rarity": "epic", "image_url": "https://i.postimg.cc/7LKRkT3D/IMG-20260612-221039-593.jpg", "quote": "Всё, что я делаю, я делаю для бизнеса.", "jobs_award": 444},
    {"card_id": "17", "name": "Депп", "series": "The Boys", "rarity": "rare", "image_url": "https://i.postimg.cc/52RvW4X7/IMG-20260612-221039-607.jpg", "quote": "Меня никто не уважает… даже осьминог.", "jobs_award": 277},
    {"card_id": "18", "name": "Сержант Докс", "series": "Dexter", "rarity": "rare", "image_url": "https://i.postimg.cc/dtJSLB5Q/IMG-20260612-221045-533.jpg", "quote": "Я узнаю убийцу, когда вижу его.", "jobs_award": 400},
    {"card_id": "19", "name": "Поли Уолнатс", "series": "The Sopranos", "rarity": "rare", "image_url": "https://i.postimg.cc/hvLwNZMb/IMG-20260612-221045-287.jpg", "quote": "Что ты там говоришь?", "jobs_award": 217},
    {"card_id": "20", "name": "Лало Саламанка", "series": "Better Call Saul", "rarity": "rare", "image_url": "https://i.postimg.cc/7hRkK2Wt/IMG-20260612-221044-998.jpg", "quote": "Расскажи это снова.", "jobs_award": 389},
    {"card_id": "21", "name": "Хэнк Шрейдер", "series": "Breaking Bad", "rarity": "rare", "image_url": "https://i.postimg.cc/bNTYtm8M/IMG-20260612-221052-912.jpg", "quote": "Я найду тебя, Хайзенберг.", "jobs_award": 323},
    {"card_id": "22", "name": "Эбигейл Хоббс", "series": "Hannibal", "rarity": "rare", "image_url": "https://i.postimg.cc/02cxQrdt/IMG-20260612-221053-261.jpg", "quote": "Я не хотела этого.", "jobs_award": 247},
    {"card_id": "23", "name": "Ханна Маккей", "series": "Dexter", "rarity": "uncommon", "image_url": "https://i.postimg.cc/bwxJ3qQ0/IMG-20260612-221052-516.jpg", "quote": "Мы созданы друг для друга, Декстер.", "jobs_award": 167},
    {"card_id": "24", "name": "Кармела Сопрано", "series": "The Sopranos", "rarity": "uncommon", "image_url": "https://i.postimg.cc/63YtF333/IMG-20260612-221039-861.jpg", "quote": "Я знаю, кто ты, Тони.", "jobs_award": 111},
    {"card_id": "25", "name": "Майк Эрмантраут", "series": "Better Call Saul", "rarity": "uncommon", "image_url": "https://i.postimg.cc/Dwvk3h96/IMG-20260612-221045-690.jpg", "quote": "Я просчитываю каждый шаг.", "jobs_award": 129},
    {"card_id": "26", "name": "Тодд Алкист", "series": "Breaking Bad", "rarity": "uncommon", "image_url": "https://i.postimg.cc/MKstX8cF/IMG-20260612-221045-373.jpg", "quote": "Ничего личного.", "jobs_award": 100},
    {"card_id": "27", "name": "Французик", "series": "The Boys", "rarity": "common", "image_url": "https://i.postimg.cc/tTXVhYwd/IMG-20260612-221052-794.jpg", "quote": "Я люблю этот мир, но он не любит меня.", "jobs_award": 100},
    {"card_id": "28", "name": "Винс Масука", "series": "Dexter", "rarity": "common", "image_url": "https://i.postimg.cc/nLJR7GkM/IMG-20260612-221039-163.jpg", "quote": "Это отличный день, чтобы быть живым!", "jobs_award": 69},
    {"card_id": "29", "name": "Дядя Джуниор", "series": "The Sopranos", "rarity": "common", "image_url": "https://i.postimg.cc/R0w0p4Kf/IMG-20260612-221039-310.jpg", "quote": "У тебя никогда не было яиц.", "jobs_award": 55},
    {"card_id": "30", "name": "Чак Макгилл", "series": "Better Call Saul", "rarity": "common", "image_url": "https://i.postimg.cc/B6H4QgMK/IMG-20260612-221052-846.jpg", "quote": "Люди не меняются.", "jobs_award": 50}
]

RARITY_CHANCES = {"common":0.44, "uncommon":0.22, "rare":0.15, "epic":0.10, "legendary":0.05, "mythic":0.03, "null":0.01}
RARITY_EMOJI = {"common":"⚪", "uncommon":"🟢", "rare":"🔵", "epic":"🟣", "legendary":"🟠", "mythic":"🔴", "null":"⚫"}
RARITY_RU = {"common":"Простая", "uncommon":"Необычная", "rare":"Редкая", "epic":"Эпическая", "legendary":"Легендарная", "mythic":"Мифическая", "null":"Null"}
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic", "null"]

# ========== СИСТЕМА АНТИСПАМА ==========
user_request_timestamps = defaultdict(list)
user_command_history = defaultdict(list)

def register_user(user_id, username):
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not res.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "username": username,
            "is_frozen": False,
            "jobs_balance": 0
        }).execute()
    else:
        supabase.table("users").update({"username": username}).eq("user_id", user_id).execute()

def is_user_blocked(user_id):
    res = supabase.table("users").select("is_frozen").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0].get("is_frozen", False)
    return False

def freeze_user(user_id, reason):
    supabase.table("users").update({"is_frozen": True}).eq("user_id", user_id).execute()
    supabase.table("spam_logs").insert({
        "user_id": user_id,
        "action_taken": f"Auto-Frozen ({reason})",
        "triggers_count": 1
    }).execute()

async def check_antispam(message: Message, bot: Bot) -> bool:
    user_id = message.from_user.id
    if user_id == ADMIN_ID or is_user_blocked(user_id):
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

    if len(timestamps) >= 7:
        freeze_user(user_id, "Tier 2: >7 запросов за 5 сек")
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔓 Разморозить", callback_data=f"unfreeze:{user_id}"),
            InlineKeyboardButton(text="⛔ Забанить", callback_data=f"ban:{user_id}")
        ]])
        await bot.send_message(
            LOG_CHAT_ID, 
            f"🚨 <b>АНТИСПАМ (Tier 2):</b> Игрок @{html.escape(message.from_user.username or 'без ника')} (ID: <code>{user_id}</code>) заморожен!\n"
            f"Причина: 7+ запросов за 5 секунд.",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )
        return True

    elif same_cmd_count >= 10:
        freeze_user(user_id, f"Tier 3: 10x '{cmd_text}' за 10 мин")
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔓 Разморозить", callback_data=f"unfreeze:{user_id}"),
            InlineKeyboardButton(text="⛔ Забанить", callback_data=f"ban:{user_id}")
        ]])
        await bot.send_message(
            LOG_CHAT_ID, 
            f"🚨 <b>АНТИСПАМ (Tier 3):</b> Игрок @{html.escape(message.from_user.username or 'без ника')} (ID: <code>{user_id}</code>) заморожен!\n"
            f"Причина: Повтор команды <i>'{html.escape(cmd_text)}'</i> 10 раз за 10 минут.",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )
        return True

    elif len(timestamps) > 1:
        return True

    return False

# =========================================

def get_random_card(roll_count):
    r = random.random()
    cum = 0
    chosen = "common"
    for rarity, chance in RARITY_CHANCES.items():
        cum += chance
        if r <= cum:
            chosen = rarity
            break

    if roll_count < 3 and chosen in ["legendary", "mythic", "null"]:
        allowed = {k: v for k, v in RARITY_CHANCES.items() if k not in ["legendary", "mythic", "null"]}
        total = sum(allowed.values())
        r2 = random.random()
        cum2 = 0
        for rarity, chance in allowed.items():
            cum2 += chance / total
            if r2 <= cum2:
                chosen = rarity
                break

    matching_cards = [c for c in CARDS_DATA if c["rarity"] == chosen]
    return random.choice(matching_cards if matching_cards else CARDS_DATA)

def can_roll(user_id):
    res = supabase.table("users").select("last_roll_time").eq("user_id", user_id).execute()
    if not res.data or not res.data[0]["last_roll_time"]:
        return True, None
    last = datetime.fromisoformat(res.data[0]["last_roll_time"])
    now = datetime.now(timezone.utc)
    if now - last >= timedelta(hours=2):
        return True, None
    remaining = timedelta(hours=2) - (now - last)
    return False, f"{remaining.seconds // 3600} ч {(remaining.seconds % 3600) // 60} мин"

def give_card_to_user(user_id, card, now):
    supabase.table("user_cards").insert({
        "user_id": user_id, 
        "card_id": str(card["card_id"]), 
        "card_name": card["name"],
        "rarity": card["rarity"]
    }).execute()

    user_res = supabase.table("users").select("jobs_balance").eq("user_id", user_id).execute()
    curr_jobs = user_res.data[0].get("jobs_balance", 0) or 0 if user_res.data else 0

    supabase.table("users").update({
        "last_roll_time": now.isoformat(),
        "jobs_balance": curr_jobs + card.get("jobs_award", 0)
    }).eq("user_id", user_id).execute()

def get_mycards_keyboard(user_id, page_idx):
    prev_idx = (page_idx - 1) % len(RARITY_ORDER)
    next_idx = (page_idx + 1) % len(RARITY_ORDER)
    current_rarity = RARITY_ORDER[page_idx]
    emoji = RARITY_EMOJI[current_rarity]

    buttons = [
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"mycards:{user_id}:{prev_idx}"),
        InlineKeyboardButton(text=f"Стр. {page_idx+1}/7 ({emoji})", callback_data="noop"),
        InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"mycards:{user_id}:{next_idx}")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

bot = Bot(token=TOKEN)
dp = Dispatcher()
# ========== ЮЗЕРСКИЕ КОМАНДЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if await check_antispam(message, bot): return
    register_user(message.from_user.id, message.from_user.username or "no_name")
    await message.answer(
        "📺 <b>Добро пожаловать в сериальную коллекцию, боец!</b>\n"
        "Меня зовут <b>Джоб</b>, и я помогаю собирать карты легендарных персонажей.\n\n"
        "🎴 <b>Как играть:</b>\n"
        "• Каждые 2 часа проси у меня карту: «<b>Джоб дай карту</b>»\n"
        "• Смотри свою коллекцию: «<b>Джоб мои карты</b>»\n\n"
        "Да начнётся коллекция!",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    if await check_antispam(message, bot): return
    text = (
        "📋 <b>Команды Джоба:</b>\n\n"
        "/start - запустить бота\n"
        "/help - это сообщение\n"
        "/roll или Джоб дай карту - получить случайную карту (раз в 2 часа)\n"
        "/mycards или Джоб мои карты - показать коллекцию"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("roll"))
async def roll_card(message: Message):
    if await check_antispam(message, bot): return
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username or "no_name")
    ok, rem = can_roll(user_id)
    if not ok:
        await message.answer(f"⏳ У Джоба больше нет карт сейчас для вас, отдыхайте, но приходите через ({rem})")
        return
    
    card = get_random_card(0)
    give_card_to_user(user_id, card, datetime.now(timezone.utc))
    
    caption = (
        f"🃏 <b>Джоб достаёт карту «{html.escape(card['name'])} ({html.escape(card['series'])})»</b> 🃏\n"
        f"✨ Редкость: {RARITY_RU[card['rarity']]} {RARITY_EMOJI[card['rarity']]} ✨\n"
        f"💰 Джобсы: +{card['jobs_award']} 💰\n"
        f"<i>«{html.escape(card['quote'])}»</i>"
    )
    try:
        await message.answer_photo(photo=card["image_url"], caption=caption, parse_mode=ParseMode.HTML)
    except Exception:
        await message.answer(caption, parse_mode=ParseMode.HTML)

@dp.message(Command("mycards"))
async def my_cards(message: Message):
    if await check_antispam(message, bot): return
    await render_mycards_page(message.from_user.id, message, page_idx=0)

async def render_mycards_page(user_id, message_or_cb, page_idx=0):
    rarity = RARITY_ORDER[page_idx]
    cards_res = supabase.table("user_cards").select("*").eq("user_id", user_id).execute()
    
    filtered_cards = defaultdict(int)
    total_cards = 0
    if cards_res.data:
        for row in cards_res.data:
            total_cards += 1
            if row.get("rarity") == rarity:
                filtered_cards[row.get("card_name")] += 1

    emoji = RARITY_EMOJI[rarity]
    ru_rarity = RARITY_RU[rarity]
    
    msg_text = f"🃏 <b>Твоя коллекция</b> (Всего карт: {total_cards})\n"
    msg_text += f"Страница {page_idx+1}/7 — {emoji} <b>{ru_rarity}</b>:\n──────────────────────\n"

    if not filtered_cards:
        msg_text += "<i>В этой категории у тебя пока нет карт.</i>"
    else:
        for name, count in sorted(filtered_cards.items()):
            msg_text += f"• <b>{html.escape(name)}</b> — <b>{count} шт.</b>\n"

    kb = get_mycards_keyboard(user_id, page_idx)

    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(msg_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await message_or_cb.message.edit_text(msg_text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.callback_query(F.data.startswith("mycards:"))
async def mycards_callback(cb: CallbackQuery):
    _, uid, p_idx = cb.data.split(":")
    if cb.from_user.id != int(uid):
        await cb.answer("Это не твоя коллекция!", show_alert=True)
        return
    await render_mycards_page(int(uid), cb, int(p_idx))
    await cb.answer()

@dp.callback_query(F.data == "noop")
async def noop_callback(cb: CallbackQuery):
    await cb.answer()

@dp.message(F.text & ~F.text.startswith("/"))
async def text_commands(message: Message):
    text = message.text.strip().lower().rstrip('!.,;')
    if text in ["джоб дай карту", "джоб, дай карту"] or text.startswith("джоб дай карту"):
        await roll_card(message)
    elif text in ["джоб мои карты", "джоб, мои карты"]:
        await my_cards(message)

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
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /check_user <id_или_username>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    uid = user["user_id"]
    status = "🧊 ЗАМОРОЖЕН" if user.get("is_frozen") else "🟢 Активен"
    jobs = user.get("jobs_balance", 0) or 0
    
    cards_cnt = supabase.table("user_cards").select("id", count="exact").eq("user_id", uid).execute().count or 0
    spam_cnt = supabase.table("spam_logs").select("id", count="exact").eq("user_id", uid).execute().count or 0

    msg = (
        f"📋 <b>ИНСПЕКЦИЯ ПОЛЬЗОВАТЕЛЯ</b>\n──────────────────────\n"
        f"👤 Игрок: @{html.escape(user['username'] or 'no_name')} (ID: <code>{uid}</code>)\n"
        f"💰 Баланс: <b>{jobs}</b> джобсов\n"
        f"🃏 Всего карт в коллекции: <b>{cards_cnt}</b> шт.\n"
        f"🧊 Статус: <b>{status}</b>\n"
        f"🚨 Нарушения: <b>{spam_cnt}</b> спам-триггеров (Подробно: /logs_user {uid})"
    )
    await message.answer(msg, parse_mode=ParseMode.HTML)

@dp.message(Command("logs_user"))
async def logs_user(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /logs_user <id_или_username>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    uid = user["user_id"]
    spams = supabase.table("spam_logs").select("*").eq("user_id", uid).order("id", desc=True).limit(5).execute()
    
    msg = f"📊 <b>ПОЛНЫЕ ЛОГИ:</b> @{html.escape(user['username'] or 'no_name')} (ID: <code>{uid}</code>)\n──────────────────────\n\n🚨 <b>ИСТОРИЯ СПАМА:</b>\n"
    if not spams.data:
        msg += "• Нарушений не зафиксировано.\n"
    else:
        for s in spams.data:
            msg += f"• {s.get('created_at', 'Н/Д')} | {html.escape(s.get('action_taken', 'Спам'))}\n"
            
    await message.answer(msg, parse_mode=ParseMode.HTML)

@dp.message(Command("give_jobs"))
async def give_jobs(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Используй: /give_jobs <id_или_username> <количество>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    try:
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ Количество должно быть числом.")
        return

    uid = user["user_id"]
    current_jobs = user.get("jobs_balance", 0) or 0
    new_balance = current_jobs + amount

    supabase.table("users").update({"jobs_balance": new_balance}).eq("user_id", uid).execute()
    await message.answer(
        f"💰 Пользователю @{html.escape(user['username'] or 'no_name')} начислено <b>{amount}</b> джобсов!\n"
        f"Текущий баланс: <b>{new_balance}</b> 💰",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("freeze"))
async def cmd_freeze(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_frozen": True}).eq("user_id", user["user_id"]).execute()
        await message.answer(f"🧊 Пользователь @{html.escape(user['username'] or 'no_name')} заморожен.", parse_mode=ParseMode.HTML)

@dp.message(Command("unfreeze"))
async def cmd_unfreeze(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_frozen": False}).eq("user_id", user["user_id"]).execute()
        await message.answer(f"🔓 Пользователь @{html.escape(user['username'] or 'no_name')} разморожен.", parse_mode=ParseMode.HTML)

@dp.message(Command("rc"))
async def cmd_rc(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"last_roll_time": None}).eq("user_id", user["user_id"]).execute()
        await message.answer(f"⏳ Таймер ролла для @{html.escape(user['username'] or 'no_name')} сброшен.", parse_mode=ParseMode.HTML)

@dp.message(Command("reset_user"))
async def reset_user(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /reset_user <id_или_username>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    target_id = user["user_id"]
    supabase.table("user_cards").delete().eq("user_id", target_id).execute()
    supabase.table("users").update({"last_roll_time": None, "jobs_balance": 0}).eq("user_id", target_id).execute()
    await message.answer(f"✅ Прогресс карт и джобсов пользователя @{html.escape(user['username'] or 'no_name')} сброшен.", parse_mode=ParseMode.HTML)

@dp.message(Command("give_card"))
async def give_card(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Используй: /give_card <id_или_username> <ID_карты_или_название>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    query = ' '.join(args[2:]).strip().lower()
    card = None
    for c in CARDS_DATA:
        if c["card_id"] == query or query in c["name"].lower():
            card = c
            break
    
    if not card:
        await message.answer("❌ Карта не найдена.")
        return
    
    give_card_to_user(user["user_id"], card, datetime.now(timezone.utc))
    
    caption = (
        f"🃏 <b>Админ лично выдал карту</b> «{html.escape(card['name'])} ({html.escape(card['series'])})» пользователю @{html.escape(user['username'] or 'no_name')} 🃏\n"
        f"✨ Редкость: {RARITY_RU[card['rarity']]} {RARITY_EMOJI[card['rarity']]} ✨\n"
        f"<i>«{html.escape(card['quote'])}»</i>"
    )
    try:
        await message.answer_photo(photo=card["image_url"], caption=caption, parse_mode=ParseMode.HTML)
    except Exception:
        await message.answer(caption, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("unfreeze:"))
async def cb_unfreeze(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID: return
    uid = int(cb.data.split(":")[1])
    supabase.table("users").update({"is_frozen": False}).eq("user_id", uid).execute()
    await cb.message.edit_text(cb.message.text + "\n\n✅ <b>ПОЛЬЗОВАТЕЛЬ РАЗМОРОЖЕН</b>", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("ban:"))
async def cb_ban(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID: return
    uid = int(cb.data.split(":")[1])
    supabase.table("users").update({"is_frozen": True}).eq("user_id", uid).execute()
    await cb.message.edit_text(cb.message.text + "\n\n⛔ <b>ПОЛЬЗОВАТЕЛЬ ЗАБАНЕН</b>", parse_mode=ParseMode.HTML)

# =========================================

async def main():
    print("✅ Джоб v2.0 (FULL ADMIN & SUPABASE) запущен!")
    await dp.start_polling(bot)

keep_alive()

if __name__ == "__main__":
    asyncio.run(main())

