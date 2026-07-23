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
    return "Бот Джоб v2.0 работает!"

def run_web():
    port = int(os.environ.get('PORT', 5000))
    app_web.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()
# =========================================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6990974323  # Твой Telegram ID
LOG_CHAT_ID = -1005336201694  # ID группы для логов (с -100)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Локальная база карт
CARDS_DATA = [
    (1, "Хоумлендер", "The Boys", "null", "https://i.postimg.cc/R08Z0qmj/IMG-20260612-221053-063.jpg", "Я здесь бог.", 3333),
    (2, "Мясник", "The Boys", "mythic", "https://i.postimg.cc/pdb7CH2M/IMG-20260612-221039-579.jpg", "Мы спасём эту чёртову страну!", 2332),
    (3, "Декстер Морган", "Dexter", "mythic", "https://i.postimg.cc/tgczkddt/IMG-20260612-221039-343.jpg", "Сегодня ночью — охота.", 1777),
    (4, "Тони Сопрано", "The Sopranos", "mythic", "https://i.postimg.cc/NM7kthqK/IMG-20260612-221045-473.jpg", "Я пришёл за утками.", 1919),
    (5, "Ганнибал Лектер", "Hannibal", "mythic", "https://i.postimg.cc/Dzn6myv5/IMG-20260612-221039-738.jpg", "Печень — с бобами.", 2700),
    (6, "Хайзенберг", "Breaking Bad", "mythic", "https://i.postimg.cc/gJknx1L6/IMG-20260612-221052-546.jpg", "Я — тот, кто стучит.", 2500),
    (7, "Королева Мэйв", "The Boys", "legendary", "https://i.postimg.cc/zBP4nRvP/IMG-20260612-221045-477.jpg", "Хватит притворяться, Хоумлендер.", 1636),
    (8, "Джесси Пинкман", "Breaking Bad", "legendary", "https://i.postimg.cc/CLvnbhs1/IMG-20260612-221039-831.jpg", "Наука, bitch!", 1455),
    (9, "Тринити-киллер", "Dexter", "legendary", "https://i.postimg.cc/vHmLJSPf/IMG-20260612-221053-114.jpg", "Всё кончено, Декстер.", 800),
    (10, "Сол Гудман", "Better Call Saul", "legendary", "https://i.postimg.cc/KzswbyDB/IMG-20260612-221045-610.jpg", "Позвоните Солу!", 1321),
    (11, "Уилл Грэм", "Hannibal", "legendary", "https://i.postimg.cc/rmc5Qh0W/IMG-20260612-221053-281.jpg", "Это красиво.", 1111),
    (12, "Энни (Старлайт)", "The Boys", "epic", "https://i.postimg.cc/SRV0Jt8d/IMG-20260612-221052-889.jpg", "Я верю в добро, даже если его почти не осталось.", 609),
    (13, "Дебра Морган", "Dexter", "epic", "https://i.postimg.cc/TYvCBczN/IMG-20260612-221039-420.jpg", "Ты мне отвратителен, но я люблю тебя, брат.", 512),
    (14, "Кристофер Молтисанти", "The Sopranos", "epic", "https://i.postimg.cc/ZRCJtmdz/IMG-20260612-221045-723.jpg", "Моя судьба — кино, а не это дерьмо.", 464),
    (15, "Ким Уэкслер", "Better Call Saul", "epic", "https://i.postimg.cc/NFS36wKZ/IMG-20260612-221045-353.jpg", "Ты в деле, Сол.", 400),
    (16, "Гус Фринг", "Breaking Bad", "epic", "https://i.postimg.cc/7LKRkT3D/IMG-20260612-221039-593.jpg", "Всё, что я делаю, я делаю для бизнеса.", 444),
    (17, "Депп", "The Boys", "rare", "https://i.postimg.cc/52RvW4X7/IMG-20260612-221039-607.jpg", "Меня никто не уважает… даже осьминог.", 277),
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
]

CARDS_DICT = {
    c[0]: {"id": c[0], "name": c[1], "series": c[2], "rarity": c[3], "image_url": c[4], "quote": c[5], "jobs_award": c[6]}
    for c in CARDS_DATA
}

RARITY_CHANCES = {"common":0.44, "uncommon":0.22, "rare":0.15, "epic":0.10, "legendary":0.05, "mythic":0.03, "null":0.01}
RARITY_EMOJI = {"common":"⚪", "uncommon":"🟢", "rare":"🔵", "epic":"🟣", "legendary":"🟠", "mythic":"🔴", "null":"⚫"}
RARITY_RU = {"common":"Простая", "uncommon":"Необычная", "rare":"Редкая", "epic":"Эпическая", "legendary":"Легендарная", "mythic":"Мифическая", "null":"Null"}
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic", "null"]

user_request_timestamps = defaultdict(list)
user_command_history = defaultdict(list)

def register_user(user_id, username, first_name=""):
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not res.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "username": username or "no_name",
            "first_name": first_name or "",
            "is_frozen": False,
            "is_banned": False,
            "is_admin": False,
            "jobs_balance": 0
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
    if user_id == ADMIN_ID:
        return True
    res = supabase.table("users").select("is_admin").eq("user_id", user_id).execute()
    if res.data:
        return bool(res.data[0].get("is_admin"))
    return False

def freeze_user(user_id, reason):
    now = datetime.now(timezone.utc).isoformat()
    supabase.table("users").update({"is_frozen": True, "freeze_reason": reason}).eq("user_id", user_id).execute()
    
    logs_res = supabase.table("spam_logs").select("id", count="exact").eq("user_id", user_id).execute()
    triggers = (logs_res.count or 0) + 1
    
    supabase.table("spam_logs").insert({
        "user_id": user_id,
        "action_taken": f"Auto-Frozen ({reason})",
        "triggers_count": triggers,
        "created_at": now
    }).execute()

async def check_antispam(message: Message, bot: Bot) -> bool:
    user_id = message.from_user.id
    if user_id == ADMIN_ID or is_admin(user_id) or is_user_blocked(user_id):
        return is_user_blocked(user_id)

    now = datetime.now()
    cmd_text = message.text.strip().lower() if message.text else ""

    # Очистка старых таймстемпов за 5 секунд
    timestamps = [t for t in user_request_timestamps[user_id] if now - t <= timedelta(seconds=5)]
    timestamps.append(now)
    user_request_timestamps[user_id] = timestamps

    # Очистка истории одинаковых команд за 10 минут
    cmd_history = [(t, c) for t, c in user_command_history[user_id] if now - t <= timedelta(minutes=10)]
    cmd_history.append((now, cmd_text))
    user_command_history[user_id] = cmd_history

    same_cmd_count = sum(1 for t, c in cmd_history if c == cmd_text)

    # Tier 2 & Tier 3
    if len(timestamps) >= 7 or same_cmd_count >= 10:
        tier_label = "Tier 2 (>7 за 5 сек)" if len(timestamps) >= 7 else f"Tier 3 (10x '{cmd_text}' за 10 мин)"
        freeze_user(user_id, tier_label)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔓 Разморозить", callback_data=f"unfreeze:{user_id}"),
            InlineKeyboardButton(text="⛔ Забанить", callback_data=f"ban:{user_id}")
        ]])
        try:
            uname_display = f"@{message.from_user.username}" if message.from_user.username else (message.from_user.first_name or "без ника")
            await bot.send_message(
                LOG_CHAT_ID, 
                f"🚨 <b>АНТИСПАМ ({tier_label}):</b> Обнаружена подозрительная активность!\n"
                f"Пользователь: {html.escape(uname_display)} (ID: <code>{user_id}</code>)\n"
                f"Действие: Автоматическая заморозка (is_frozen = True)",
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
        except Exception as e:
            print(f"Ошибка отправки в LOG_CHAT_ID: {e}")
        return True

    # Tier 1: Бесшумный игнор (2-6 запросов за 5 сек)
    elif len(timestamps) > 1:
        return True

    return False

def get_random_card():
    r = random.random()
    cum = 0
    chosen_rarity = "common"
    for rarity, chance in RARITY_CHANCES.items():
        cum += chance
        if r <= cum:
            chosen_rarity = rarity
            break

    matching_cards = [c for c in CARDS_DATA if c[3] == chosen_rarity]
    if not matching_cards:
        matching_cards = CARDS_DATA
    
    chosen = random.choice(matching_cards)
    return CARDS_DICT[chosen[0]]

def can_roll(user_id):
    res = supabase.table("users").select("last_roll_time").eq("user_id", user_id).execute()
    if not res.data or not res.data[0].get("last_roll_time"):
        return True, None
    
    last_str = res.data[0]["last_roll_time"]
    last = datetime.fromisoformat(last_str.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    if now - last >= timedelta(hours=2):
        return True, None
    remaining = timedelta(hours=2) - (now - last)
    return False, f"{remaining.seconds // 3600} ч {(remaining.seconds % 3600) // 60} мин"

async def give_card_to_user(user_id, card, now, username="no_name", first_name=""):
    user_res = supabase.table("users").select("jobs_balance").eq("user_id", user_id).execute()
    current_jobs = user_res.data[0].get("jobs_balance", 0) if user_res.data else 0

    supabase.table("user_cards").insert({
        "user_id": user_id,
        "card_id": card["id"],
        "card_name": card["name"],
        "rarity": card["rarity"],
        "obtained_at": now.isoformat()
    }).execute()

    supabase.table("users").update({
        "jobs_balance": current_jobs + card["jobs_award"],
        "last_roll_time": now.isoformat()
    }).eq("user_id", user_id).execute()

    try:
        uname_display = f"@{username}" if username and username != "no_name" else (first_name or "Игрок")
        log_msg = (
            f"🎲 <b>Игрок:</b> {html.escape(uname_display)} (ID: <code>{user_id}</code>)\n"
            f"🃏 <b>Выбил карту:</b> {html.escape(card['name'])} ({html.escape(card['series'])})\n"
            f"✨ <b>Редкость:</b> {RARITY_RU[card['rarity']]} {RARITY_EMOJI[card['rarity']]}\n"
            f"💰 <b>Награда:</b> +{card['jobs_award']} джобсов"
        )
        await bot.send_message(LOG_CHAT_ID, log_msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Ошибка логирования ролла: {e}")

bot = Bot(token=TOKEN)
dp = Dispatcher()
# ========== ЮЗЕРСКИЕ КОМАНДЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if await check_antispam(message, bot): return
    register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        "📺 <b>Добро пожаловать в сериальную коллекцию, боец!</b>\n"
        "Меня зовут <b>Джоб</b>, и я помогаю собирать карты легендарных персонажей.\n\n"
        "🎴 <b>Как играть:</b>\n"
        "• Каждые 2 часа проси у меня карту: «<b>Джоб дай карту</b>»\n"
        "• Смотри свою коллекцию: «<b>Джоб мои карты</b>»\n"
        "• Узнавай баланс джобсов: «<b>Джоб мой баланс</b>»\n\n"
        "🏆 Попади в глобальный <b>ТОП 30 по джобсам!</b>\n\nДа начнётся коллекция!",
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
    username = message.from_user.username or "no_name"
    first_name = message.from_user.first_name or ""
    register_user(user_id, username, first_name)
    
    ok, rem = can_roll(user_id)
    if not ok:
        await message.answer(f"⏳ У Джоба больше нет карт сейчас для вас, отдыхайте, но приходите через ({rem})")
        return
    
    card = get_random_card()
    await give_card_to_user(user_id, card, datetime.now(timezone.utc), username, first_name)
    
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

async def render_user_cards_page(target_user_id, message_or_cb, page_idx=0, viewer_id=None):
    rarity = RARITY_ORDER[page_idx]
    cards_res = supabase.table("user_cards").select("card_id, card_name, rarity").eq("user_id", target_user_id).execute()
    
    counts = defaultdict(int)
    total_cards = len(cards_res.data) if cards_res.data else 0
    
    if cards_res.data:
        for row in cards_res.data:
            if row.get("rarity") == rarity:
                counts[row.get("card_name")] += 1

    emoji = RARITY_EMOJI[rarity]
    ru_rarity = RARITY_RU[rarity]
    
    prefix = "🃏 <b>Коллекция игрока</b>" if viewer_id and viewer_id != target_user_id else "🃏 <b>Твоя коллекция</b>"
    
    msg_text = f"{prefix} (Всего карт: {total_cards})\n"
    msg_text += f"Страница {page_idx+1}/7 — {emoji} <b>{ru_rarity}</b>:\n──────────────────────\n"

    if not counts:
        msg_text += "<i>В этой категории пока нет карт.</i>"
    else:
        for card_name, cnt in sorted(counts.items()):
            msg_text += f"• <b>{html.escape(card_name)}</b> — <b>{cnt} шт.</b>\n"

    cb_prefix = "viewcards" if viewer_id and is_admin(viewer_id) and viewer_id != target_user_id else "mycards"
    
    buttons = [
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{cb_prefix}:{target_user_id}:{(page_idx - 1) % len(RARITY_ORDER)}"),
        InlineKeyboardButton(text=f"Стр. {page_idx+1}/7 ({emoji})", callback_data="noop"),
        InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{cb_prefix}:{target_user_id}:{(page_idx + 1) % len(RARITY_ORDER)}")
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=[buttons])

    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(msg_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await message_or_cb.message.edit_text(msg_text, parse_mode=ParseMode.HTML, reply_markup=kb)

@dp.message(Command("mycards"))
async def my_cards(message: Message):
    if await check_antispam(message, bot): return
    await render_user_cards_page(message.from_user.id, message, page_idx=0, viewer_id=message.from_user.id)

@dp.callback_query(F.data.startswith("mycards:"))
async def mycards_callback(cb: CallbackQuery):
    _, uid, p_idx = cb.data.split(":")
    if cb.from_user.id != int(uid):
        await cb.answer("Это не твоя коллекция!", show_alert=True)
        return
    await render_user_cards_page(int(uid), cb, int(p_idx), viewer_id=cb.from_user.id)
    await cb.answer()

@dp.callback_query(F.data.startswith("viewcards:"))
async def viewcards_callback(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("Только админ может просматривать чужие карты!", show_alert=True)
        return
    _, target_uid, p_idx = cb.data.split(":")
    await render_user_cards_page(int(target_uid), cb, int(p_idx), viewer_id=cb.from_user.id)
    await cb.answer()

@dp.callback_query(F.data == "noop")
async def noop_callback(cb: CallbackQuery):
    await cb.answer()

@dp.message(Command("jobs"))
async def show_balance(message: Message):
    if await check_antispam(message, bot): return
    register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    res = supabase.table("users").select("jobs_balance").eq("user_id", message.from_user.id).execute()
    jobs = res.data[0].get("jobs_balance", 0) if res.data else 0
    await message.answer(f"💰 Джоб пересчитал твои заначки: <b>{jobs}</b> джобсов.", parse_mode=ParseMode.HTML)

@dp.message(Command("topjobs"))
async def top_jobs(message: Message):
    if await check_antispam(message, bot): return
    try:
        # ИСКЛЮЧАЕМ ЗАБАНЕННЫХ ИЗ ТОПА (is_banned = False)!
        res = supabase.table("users").select("username, first_name, jobs_balance").eq("is_banned", False).gt("jobs_balance", 0).order("jobs_balance", desc=True).limit(30).execute()
        if not res.data:
            await message.answer("💰 Пока никто не заработал ни одного джобса. Начни первым!")
            return
        text = "🏆 <b>Топ 30 по джобсам:</b>\n\n"
        medals = {1:"🥇", 2:"🥈", 3:"🥉"}
        for i, row in enumerate(res.data, 1):
            raw_username = row.get("username")
            first_name = row.get("first_name") or "Аноним"
            if raw_username and raw_username != "no_name":
                name_display = raw_username
            else:
                name_display = first_name
            medal = medals.get(i, f"{i}.")
            text += f"{medal} <b>{html.escape(name_display)}</b> — {row.get('jobs_balance', 0)} 🪙\n"
        await message.answer(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Ошибка TopJobs: {e}")
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
    if user.get("is_banned"):
        status = "⛔ ЗАБАНЕН"
    elif user.get("is_frozen"):
        status = "🧊 ЗАМОРОЖЕН"
    else:
        status = "🟢 Активен"
    
    spam_res = supabase.table("spam_logs").select("id", count="exact").eq("user_id", uid).execute()
    spam_cnt = spam_res.count or 0
    
    cards_res = supabase.table("user_cards").select("id", count="exact").eq("user_id", uid).execute()
    cards_cnt = cards_res.count or 0
    
    top_res = supabase.table("users").select("user_id", count="exact").gt("jobs_balance", user.get("jobs_balance", 0)).execute()
    top_pos = (top_res.count or 0) + 1

    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
    msg = (
        f"📋 <b>ИНСПЕКЦИЯ ПОЛЬЗОВАТЕЛЯ</b>\n──────────────────────\n"
        f"👤 Игрок: {html.escape(uname_display)} (ID: <code>{uid}</code>)\n"
        f"💰 Баланс: <b>{user.get('jobs_balance', 0)}</b> джобсов | 🏆 Топ: #{top_pos} | 🎴 Карт: {cards_cnt}\n"
        f"🧊 Статус: <b>{status}</b>\n"
        f"🚨 Нарушения: <b>{spam_cnt}</b> спам-триггеров (Подробно: /logs_user {uid})"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎴 Посмотреть коллекцию", callback_data=f"viewcards:{uid}:0")
    ]])
    await message.answer(msg, parse_mode=ParseMode.HTML, reply_markup=kb)

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
    
    spams = supabase.table("spam_logs").select("created_at, action_taken, triggers_count").eq("user_id", uid).order("id", desc=True).limit(5).execute()
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
        uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
        await message.answer(f"🧊 Пользователь {html.escape(uname_display)} заморожен.", parse_mode=ParseMode.HTML)

@dp.message(Command("unfreeze"))
async def cmd_unfreeze(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_frozen": False, "freeze_reason": None}).eq("user_id", user["user_id"]).execute()
        uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
        await message.answer(f"🔓 Пользователь {html.escape(uname_display)} разморожен.", parse_mode=ParseMode.HTML)

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_banned": True}).eq("user_id", user["user_id"]).execute()
        uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
        await message.answer(f"⛔ Пользователь {html.escape(uname_display)} забанен (скрыт из топа).", parse_mode=ParseMode.HTML)

@dp.message(Command("unban"))
async def cmd_unban(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"is_banned": False}).eq("user_id", user["user_id"]).execute()
        uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
        await message.answer(f"✅ Пользователь {html.escape(uname_display)} разбанен.", parse_mode=ParseMode.HTML)

@dp.message(Command("rc"))
async def cmd_rc(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return
    user = get_target_user(args[1])
    if user:
        supabase.table("users").update({"last_roll_time": None}).eq("user_id", user["user_id"]).execute()
        uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
        await message.answer(f"⏳ Таймер ролла для {html.escape(uname_display)} сброшен.", parse_mode=ParseMode.HTML)

@dp.message(Command("reset_user"))
async def reset_user(message: Message):
    if not is_admin(message.from_user.id): return
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
    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
    await message.answer(f"✅ Прогресс пользователя {html.escape(uname_display)} (ID: {target_id}) полностью сброшен.", parse_mode=ParseMode.HTML)

@dp.message(Command("give_jobs"))
async def give_jobs(message: Message):
    if not is_admin(message.from_user.id): return
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
    
    new_jobs = user.get("jobs_balance", 0) + amount
    supabase.table("users").update({"jobs_balance": new_jobs}).eq("user_id", user["user_id"]).execute()
    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
    await message.answer(f"✅ Выдано {amount} джобсов пользователю {html.escape(uname_display)}.", parse_mode=ParseMode.HTML)

@dp.message(Command("give_card"))
async def give_card(message: Message):
    if not is_admin(message.from_user.id): return
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
        card = CARDS_DICT.get(int(query))
    if not card:
        for c in CARDS_DATA:
            if query.lower() in c[1].lower():
                card = CARDS_DICT[c[0]]
                break
    
    if not card:
        await message.answer("❌ Карта не найдена.")
        return
    
    await give_card_to_user(user["user_id"], card, datetime.now(timezone.utc), user.get("username", "no_name"), user.get("first_name", ""))
    
    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
    caption = (
        f"🃏 <b>Админ бота Джоб выдал карту</b> «{html.escape(card['name'])} ({html.escape(card['series'])})» пользователю {html.escape(uname_display)} 🃏\n"
        f"✨ Редкость: {RARITY_RU[card['rarity']]} {RARITY_EMOJI[card['rarity']]} ✨\n"
        f"💰 Джобсы: +{card['jobs_award']} 💰\n"
        f"<i>«{html.escape(card['quote'])}»</i>"
    )
    try:
        await message.answer_photo(photo=card["image_url"], caption=caption, parse_mode=ParseMode.HTML)
    except Exception:
        await message.answer(caption, parse_mode=ParseMode.HTML)

# Команды добавления и снятия админки (Строго только для главного создателя ADMIN_ID)
@dp.message(Command("add_admin"))
async def cmd_add_admin(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /add_admin <id_или_username>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    supabase.table("users").update({"is_admin": True}).eq("user_id", user["user_id"]).execute()
    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
    await message.answer(f"👑 Пользователь {html.escape(uname_display)} назначен администратором!", parse_mode=ParseMode.HTML)

@dp.message(Command("remove_admin"))
async def cmd_remove_admin(message: Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /remove_admin <id_или_username>")
        return
    user = get_target_user(args[1])
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    supabase.table("users").update({"is_admin": False}).eq("user_id", user["user_id"]).execute()
    uname_display = user.get('username') if user.get('username') and user.get('username') != "no_name" else (user.get('first_name') or 'no_name')
    await message.answer(f"🚫 У пользователя {html.escape(uname_display)} забраны права администратора.", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("unfreeze:"))
async def cb_unfreeze(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    uid = int(cb.data.split(":")[1])
    supabase.table("users").update({"is_frozen": False, "freeze_reason": None}).eq("user_id", uid).execute()
    await cb.message.edit_text(cb.message.text + "\n\n✅ <b>ПОЛЬЗОВАТЕЛЬ РАЗМОРОЖЕН</b>", parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("ban:"))
async def cb_ban(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID: return
    uid = int(cb.data.split(":")[1])
    supabase.table("users").update({"is_banned": True}).eq("user_id", uid).execute()
    await cb.message.edit_text(cb.message.text + "\n\n⛔ <b>ПОЛЬЗОВАТЕЛЬ ЗАБАНЕН</b>", parse_mode=ParseMode.HTML)

# =========================================

async def main():
    print("✅ Джоб v2.0 (Manifest Match) запущен!")
    await dp.start_polling(bot)

keep_alive()

if __name__ == "__main__":
    asyncio.run(main())