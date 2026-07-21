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

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Автоматический дефолтный список карт для заполнения базы Supabase
CARDS_DATA = [
    ("Хоумлендер", "The Boys", "null", "https://i.postimg.cc/R08Z0qmj/IMG-20260612-221053-063.jpg", "Я здесь бог.", 3333),
    ("Мясник", "The Boys", "mythic", "https://i.postimg.cc/pdb7CH2M/IMG-20260612-221039-579.jpg", "Мы спасём эту чёртову страну!", 2332),
    ("Декстер Морган", "Dexter", "mythic", "https://i.postimg.cc/tgczkddt/IMG-20260612-221039-343.jpg", "Сегодня ночью — охота.", 1777),
    ("Тони Сопрано", "The Sopranos", "mythic", "https://i.postimg.cc/NM7kthqK/IMG-20260612-221045-473.jpg", "Я пришёл за утками.", 1919),
    ("Ганнибал Лектер", "Hannibal", "mythic", "https://i.postimg.cc/Dzn6myv5/IMG-20260612-221039-738.jpg", "Печень — с бобами.", 2700),
    ("Хайзенберг", "Breaking Bad", "mythic", "https://i.postimg.cc/gJknx1L6/IMG-20260612-221052-546.jpg", "Я — тот, кто стучит.", 2500),
    ("Королева Мэйв", "The Boys", "legendary", "https://i.postimg.cc/zBP4nRvP/IMG-20260612-221045-477.jpg", "Хватит притворяться, Хоумлендер.", 1636),
    ("Джесси Пинкман", "Breaking Bad", "legendary", "https://i.postimg.cc/CLvnbhs1/IMG-20260612-221039-831.jpg", "Наука, bitch!", 1455),
    ("Тринити-киллер", "Dexter", "legendary", "https://i.postimg.cc/vHmLJSPf/IMG-20260612-221053-114.jpg", "Всё кончено, Декстер.", 800),
    ("Сол Гудман", "Better Call Saul", "legendary", "https://i.postimg.cc/KzswbyDB/IMG-20260612-221045-610.jpg", "Позвоните Солу!", 1321),
    ("Уилл Грэм", "Hannibal", "legendary", "https://i.postimg.cc/rmc5Qh0W/IMG-20260612-221053-281.jpg", "Это красиво.", 1111),
    ("Энни (Старлайт)", "The Boys", "epic", "https://i.postimg.cc/SRV0Jt8d/IMG-20260612-221052-889.jpg", "Я верю в добро, даже если его почти не осталось.", 609),
    ("Дебра Морган", "Dexter", "epic", "https://i.postimg.cc/TYvCBczN/IMG-20260612-221039-420.jpg", "Ты мне отвратителен, но я люблю тебя, брат.", 512),
    ("Кристофер Молтисанти", "The Sopranos", "epic", "https://i.postimg.cc/ZRCJtmdz/IMG-20260612-221045-723.jpg", "Моя судьба — кино, а не это дерьмо.", 464),
    ("Ким Уэкслер", "Better Call Saul", "epic", "https://i.postimg.cc/NFS36wKZ/IMG-20260612-221045-353.jpg", "Ты в деле, Сол.", 400),
    ("Гус Фринг", "Breaking Bad", "epic", "https://i.postimg.cc/7LKRkT3D/IMG-20260612-221039-593.jpg", "Всё, что я делаю, я делаю для бизнеса.", 444),
    ("Депп", "The Boys", "rare", "https://i.postimg.cc/52RvW4X7/IMG-20260612-221039-607.jpg", "Меня никто не уважает… даже осьминог.", 277),
    ("Сержант Докс", "Dexter", "rare", "https://i.postimg.cc/dtJSLB5Q/IMG-20260612-221045-533.jpg", "Я узнаю убийцу, когда вижу его.", 400),
    ("Поли Уолнатс", "The Sopranos", "rare", "https://i.postimg.cc/hvLwNZMb/IMG-20260612-221045-287.jpg", "Что ты там говоришь?", 217),
    ("Лало Саламанка", "Better Call Saul", "rare", "https://i.postimg.cc/7hRkK2Wt/IMG-20260612-221044-998.jpg", "Расскажи это снова.", 389),
    ("Хэнк Шрейдер", "Breaking Bad", "rare", "https://i.postimg.cc/bNTYtm8M/IMG-20260612-221052-912.jpg", "Я найду тебя, Хайзенберг.", 323),
    ("Эбигейл Хоббс", "Hannibal", "rare", "https://i.postimg.cc/02cxQrdt/IMG-20260612-221053-261.jpg", "Я не хотела этого.", 247),
    ("Ханна Маккей", "Dexter", "uncommon", "https://i.postimg.cc/bwxJ3qQ0/IMG-20260612-221052-516.jpg", "Мы созданы друг для друга, Декстер.", 167),
    ("Кармела Сопрано", "The Sopranos", "uncommon", "https://i.postimg.cc/63YtF333/IMG-20260612-221039-861.jpg", "Я знаю, кто ты, Тони.", 111),
    ("Майк Эрмантраут", "Better Call Saul", "uncommon", "https://i.postimg.cc/Dwvk3h96/IMG-20260612-221045-690.jpg", "Я просчитываю каждый шаг.", 129),
    ("Тодд Алкист", "Breaking Bad", "uncommon", "https://i.postimg.cc/MKstX8cF/IMG-20260612-221045-373.jpg", "Ничего личного.", 100),
    ("Французик", "The Boys", "common", "https://i.postimg.cc/tTXVhYwd/IMG-20260612-221052-794.jpg", "Я люблю этот мир, но он не любит меня.", 100),
    ("Винс Масука", "Dexter", "common", "https://i.postimg.cc/nLJR7GkM/IMG-20260612-221039-163.jpg", "Это отличный день, чтобы быть живым!", 69),
    ("Дядя Джуниор", "The Sopranos", "common", "https://i.postimg.cc/R0w0p4Kf/IMG-20260612-221039-310.jpg", "У тебя никогда не было яиц.", 55),
    ("Чак Макгилл", "Better Call Saul", "common", "https://i.postimg.cc/B6H4QgMK/IMG-20260612-221052-846.jpg", "Люди не меняются.", 50),
]

def init_supabase():
    try:
        res = supabase.table("cards").select("id", count="exact").execute()
        if res.count == 0 or res.count is None:
            rows = []
            for name, series, rarity, img, quote, award in CARDS_DATA:
                rows.append({
                    "card_name": name,
                    "series": series,
                    "rarity": rarity,
                    "image_url": img,
                    "quote": quote,
                    "jobs_award": award
                })
            supabase.table("cards").insert(rows).execute()
    except Exception as e:
        print(f"Ошибка инициализации карт: {e}")

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
            "jobs_balance": 0,
            "is_frozen": False,
            "is_banned": False
        }).execute()
    else:
        supabase.table("users").update({"username": username}).eq("user_id", user_id).execute()

def is_user_blocked(user_id):
    res = supabase.table("users").select("is_frozen, is_banned").eq("user_id", user_id).execute()
    if res.data:
        row = res.data[0]
        if row.get("is_frozen") or row.get("is_banned"):
            return True
    return False

def freeze_user(user_id, reason):
    now = datetime.now(timezone.utc).isoformat()
    supabase.table("users").update({"is_frozen": True, "freeze_reason": reason}).eq("user_id", user_id).execute()
    supabase.table("spam_logs").insert({
        "user_id": user_id,
        "created_at": now,
        "action_taken": "Auto-Frozen",
        "reason": reason
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
            ADMIN_ID, 
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
            ADMIN_ID, 
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

    res = supabase.table("cards").select("*").eq("rarity", chosen).execute()
    if res.data:
        return random.choice(res.data)
    else:
        res = supabase.table("cards").select("*").execute()
        return random.choice(res.data)

def can_roll(user_id):
    res = supabase.table("users").select("last_roll_time").eq("user_id", user_id).execute()
    if not res.data or not res.data[0].get("last_roll_time"):
        return True, None
    last = datetime.fromisoformat(res.data[0]["last_roll_time"])
    now = datetime.now(timezone.utc)
    if now - last >= timedelta(hours=2):
        return True, None
    remaining = timedelta(hours=2) - (now - last)
    return False, f"{remaining.seconds // 3600} ч {(remaining.seconds % 3600) // 60} мин"

def give_card_to_user(user_id, card, now):
    user_res = supabase.table("users").select("jobs_balance").eq("user_id", user_id).execute()
    current_balance = user_res.data[0].get("jobs_balance") or 0 if user_res.data else 0
    
    # Регистрируем карту
    card_id_val = str(card.get("id") or card.get("card_id") or card.get("card_name"))
    card_name_val = card.get("card_name") or card.get("name")
    
    supabase.table("user_cards").insert({
        "user_id": user_id, 
        "card_id": card_id_val, 
        "card_name": card_name_val,
        "rarity": card.get("rarity"),
        "obtained_at": now.isoformat()
    }).execute()

    supabase.table("users").update({
        "jobs_balance": current_balance + card.get("jobs_award", 100),
        "last_roll_time": now.isoformat()
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
        "• Смотри свою коллекцию: «<b>Джоб мои карты</b>»\n"
        "• Узнавай баланс джобсов: «<b>Джоб мой баланс</b>»\n\n"
        "💰 Джобсы пригодятся в будущем магазине. А пока просто копи.\n\n"
        "🏆 Попади в глобальный <b>ТОП 30 по джобсам!</b>\n\n" 
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
        "/topjobs - глобальный топ 30 по джобсам!\n"
        "/roll или Джоб дай карту - получить случайную карту (раз в 2 часа)\n"
        "/mycards или Джоб мои карты - показать коллекцию\n"
        "/jobs или Джоб мой баланс - сколько джобсов накопилось"
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
    
    cards_cnt_res = supabase.table("user_cards").select("id", count="exact").eq("user_id", user_id).execute()
    roll_cnt = cards_cnt_res.count or 0
    
    card = get_random_card(roll_cnt)
    give_card_to_user(user_id, card, datetime.now(timezone.utc))
    
    c_name = card.get('card_name') or card.get('name')
    c_series = card.get('series', 'Сериал')
    
    caption = (
        f"🃏 <b>Джоб достаёт карту «{html.escape(c_name)} ({html.escape(c_series)})»</b> 🃏\n"
        f"✨ Редкость: {RARITY_RU[card['rarity']]} {RARITY_EMOJI[card['rarity']]} ✨\n"
        f"💰 Джобсы: +{card.get('jobs_award', 100)} 💰\n"
        f"<i>«{html.escape(card.get('quote', ''))}»</i>"
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
    
    cards_res = supabase.table("user_cards").select("card_name, rarity").eq("user_id", user_id).execute()
    
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
        for name, cnt in sorted(filtered_cards.items()):
            msg_text += f"• <b>{html.escape(name)}</b> — <b>{cnt} шт.</b>\n"

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

@dp.message(Command("jobs"))
async def show_balance(message: Message):
    if await check_antispam(message, bot): return
    res = supabase.table("users").select("jobs_balance").eq("user_id", message.from_user.id).execute()
    jobs = res.data[0].get("jobs_balance") or 0 if res.data else 0
    await message.answer(f"💰 Джоб пересчитал твои заначки: <b>{jobs}</b> джобсов. Потрать их с умом (В будущем).", parse_mode=ParseMode.HTML)

@dp.message(Command("topjobs"))
async def top_jobs(message: Message):
    if await check_antispam(message, bot): return
    try:
        res = supabase.table("users").select("username, jobs_balance").gt("jobs_balance", 0).eq("is_banned", False).order("jobs_balance", desc=True).limit(30).execute()
        if not res.data:
            await message.answer("💰 Пока никто не заработал ни одного джобса. Начни первым!")
            return
        text = "🏆 <b>Топ 30 по джобсам:</b>\n\n"
        medals = {1:"🥇",2:"🥈",3:"🥉"}
        for i, row in enumerate(res.data, 1):
            raw_username = row.get("username")
            username = "Аноним" if not raw_username or raw_username == "no_name" else html.escape(raw_username).replace("@", "")
            medal = medals.get(i, f"{i}.")
            text += f"{medal} <b>{username}</b> — {row.get('jobs_balance', 0)} 🪙\n"
        await message.answer(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.answer("⚠️ Ошибка при загрузке топа. Попробуй позже.")

@dp.message(F.text & ~F.text.startswith("/"))
async def text_commands(message: Message):
    text = message.text.strip().lower().rstrip('!.,;')
    if text in ["джоб дай карту", "джоб, дай карту"] or text.startswith("джоб дай карту"):
        await roll_card(message)
    elif text in ["джоб мои карты", "джоб, мои карты"]:
        await my_cards(message)
    elif text in ["джоб мой баланс", "джоб, мой баланс"]:
        await show_balance(message)

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
    status = "⛔ ЗАБАНЕН" if user.get("is_banned") else ("🧊 ЗАМОРОЖЕН" if user.get("is_frozen") else "🟢 Активен")
    
    spam_res = supabase.table("spam_logs").select("id", count="exact").eq("user_id", uid).execute()
    spam_cnt = spam_res.count if spam_res.count else 0
    
    top_res = supabase.table("users").select("user_id", count="exact").gt("jobs_balance", user.get("jobs_balance", 0)).eq("is_banned", False).execute()
    top_pos = (top_res.count or 0) + 1

    msg = (
        f"📋 <b>ИНСПЕКЦИЯ ПОЛЬЗОВАТЕЛЯ</b>\n──────────────────────\n"
        f"👤 Игрок: @{html.escape(user.get('username') or 'no_name')} (ID: <code>{uid}</code>)\n"
        f"💰 Баланс: <b>{user.get('jobs_balance', 0)}</b> джобсов | 🏆 Топ: #{top_pos}\n"
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
    spams = supabase.table("spam_logs").select("created_at, reason").eq("user_id", uid).order("id", desc=True).limit(5).execute()
    
    msg = f"📊 <b>ПОЛНЫЕ ЛОГИ:</b> @{html.escape(user.get('username') or 'no_name')} (ID: <code>{uid}</code>)\n──────────────────────\n\n🚨 <b>ИСТОРИЯ СПАМА:</b>\n"
    if not spams.data:
        msg += "• Нарушений не зафиксировано.\n"
    else:
        for s in spams.data:
            msg += f"• {s.get('created_at')} | {html.escape(str(s.get('reason')))}\n"
            
    await message.answer(msg, parse_mode=ParseMode.HTML)

@dp.message(Command("freeze"))
async def cmd_freeze(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_frozen": True, "freeze_reason": "Ручная заморозка админом"}).eq("user_id", user["user_id"]).execute()
        await message.answer(f"🧊 Пользователь @{html.escape(user.get('username') or 'no_name')} заморожен.", parse_mode=ParseMode.HTML)

@dp.message(Command("unfreeze"))
async def cmd_unfreeze(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_frozen": False}).eq("user_id", user["user_id"]).execute()
        await message.answer(f"🔓 Пользователь @{html.escape(user.get('username') or 'no_name')} разморожен.", parse_mode=ParseMode.HTML)

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_banned": True}).eq("user_id", user["user_id"]).execute()
        await message.answer(f"⛔ Пользователь @{html.escape(user.get('username') or 'no_name')} забанен и скрыт из ТОПа.", parse_mode=ParseMode.HTML)

@dp.message(Command("unban"))
async def cmd_unban(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_banned": False}).eq("user_id", user["user_id"]).execute()
        await message.answer(f"✅ Пользователь @{html.escape(user.get('username') or 'no_name')} разбанен.", parse_mode=ParseMode.HTML)

@dp.message(Command("rc"))
async def cmd_rc(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"last_roll_time": None}).eq("user_id", user["user_id"]).execute()
        await message.answer(f"⏳ Таймер ролла для @{html.escape(user.get('username') or 'no_name')} сброшен.", parse_mode=ParseMode.HTML)

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
    supabase.table("users").update({"jobs_balance": 0, "last_roll_time": None}).eq("user_id", target_id).execute()
    await message.answer(f"✅ Прогресс пользователя @{html.escape(user.get('username') or 'no_name')} (ID: {target_id}) полностью сброшен.", parse_mode=ParseMode.HTML)

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
    try: amount = int(args[2])
    except: return
    
    new_jobs = (user.get("jobs_balance") or 0) + amount
    supabase.table("users").update({"jobs_balance": new_jobs}).eq("user_id", user["user_id"]).execute()
    await message.answer(f"✅ Выдано {amount} джобсов пользователю @{html.escape(user.get('username') or 'no_name')}.", parse_mode=ParseMode.HTML)

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
    
    query = ' '.join(args[2:]).strip()
    card = None
    if query.isdigit():
        res = supabase.table("cards").select("*").eq("id", int(query)).execute()
        card = res.data[0] if res.data else None
    if not card:
        res = supabase.table("cards").select("*").ilike("card_name", f"%{query}%").execute()
        card = res.data[0] if res.data else None
    
    if not card:
        await message.answer("❌ Карта не найдена.")
        return
    
    give_card_to_user(user["user_id"], card, datetime.now(timezone.utc))
    
    c_name = card.get('card_name') or card.get('name')
    c_series = card.get('series', 'Сериал')

    caption = (
        f"🃏 <b>Админ-разработчик бота Джоб лично выдал карту</b> «{html.escape(c_name)} ({html.escape(c_series)})» пользователю @{html.escape(user.get('username') or 'no_name')} 🃏\n"
        f"✨ Редкость: {RARITY_RU[card['rarity']]} {RARITY_EMOJI[card['rarity']]} ✨\n"
        f"💰 Джобсы: +{card.get('jobs_award', 100)} 💰\n"
        f"<i>«{html.escape(card.get('quote', ''))}»</i>"
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
    supabase.table("users").update({"is_banned": True}).eq("user_id", uid).execute()
    await cb.message.edit_text(cb.message.text + "\n\n⛔ <b>ПОЛЬЗОВАТЕЛЬ ЗАБАНЕН И СКРЫТ ИЗ ТОПА</b>", parse_mode=ParseMode.HTML)

# =========================================

async def main():
    init_supabase()
    print("✅ Джоб v2.0 (Supabase Edition) успешно запущен!")
    await dp.start_polling(bot)

keep_alive()

if __name__ == "__main__":
    asyncio.run(main())
