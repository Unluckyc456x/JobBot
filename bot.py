import asyncio
import random
import sqlite3
import os
TOKEN = os.environ["BOT_TOKEN"]
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# ========== КОСТЯ ТОКЕНННННН ==========

# ============================================

DB_PATH = "job_bot.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            total_cards INTEGER DEFAULT 0,
            total_jobs INTEGER DEFAULT 0,
            last_roll TEXT,
            roll_count INTEGER DEFAULT 0
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS user_cards (
            user_id INTEGER,
            card_id INTEGER,
            count INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, card_id)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS cards (
            card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            series TEXT,
            rarity TEXT,
            image_url TEXT,
            quote TEXT,
            jobs_award INTEGER
        )''')
        # КОСТЯ ЕБЛАН ЧТОБЫ ТЫ НЕ ЗАБЫЛ, УДАЛЯЕМ СТАРЫЕ КАРТЫ И ЗАПОЛНЯЕМ НОВЫМИ (30 штук)
        conn.execute("DELETE FROM cards")
        cards_data = [
            # Null (1)
            ("Хоумлендер", "The Boys", "null", "https://postimg.cc/B8mcpvtw", "Я здесь бог.", 3000),
            # Мифические (5)
            ("Мясник", "The Boys", "mythic", "https://postimg.cc/8J1v2gfH", "Мы спасём эту чёртову страну!", 1700),
            ("Декстер Морган", "Dexter", "mythic", "https://postimg.cc/V0JJwffZ", "Сегодня ночью — охота.", 1700),
            ("Тони Сопрано", "The Sopranos", "mythic", "https://postimg.cc/tZTTdqVf", "Я пришёл за утками.", 1700),
            ("Ганнибал Лектер", "Hannibal", "mythic", "https://postimg.cc/mcpCM65Z", "Печень — с бобами.", 1700),
            ("Уолтер Уайт", "Breaking Bad", "mythic", "https://postimg.cc/v18HMYXZ", "Я — тот, кто стучит.", 1700),
            # Легендарные (5)
            ("Королева Мэйв", "The Boys", "legendary", "https://postimg.cc/Mn9J7ybS", "Хватит притворяться, Хоумлендер.", 800),
            ("Джесси Пинкман", "Breaking Bad", "legendary", "https://postimg.cc/gLFCz4d5", "Наука, bitch!", 800),
            ("Тринити-киллер", "Dexter", "legendary", "https://postimg.cc/4YLj7Xst", "Всё кончено, Декстер.", 800),
            ("Сол Гудман", "Better Call Saul", "legendary", "https://postimg.cc/hfKY2XGb", "Позвоните Солу!", 800),
            ("Уилл Грэм", "Hannibal", "legendary", "https://postimg.cc/fSD8qPML", "Это красиво.", 800),
            # Эпические (5)
            ("Энни (Старлайт)", "The Boys", "epic", "https://postimg.cc/mt2stXCw", "Я верю в добро, даже если его почти не осталось.", 400),
            ("Дебра Морган", "Dexter", "epic", "https://postimg.cc/2bFs5h6Y", "Ты мне отвратителен, но я люблю тебя, брат.", 400),
            ("Кристофер Молтисанти", "The Sopranos", "epic", "https://postimg.cc/SJKByXpS", "Моя судьба — кино, а не это дерьмо.", 400),
            ("Ким Уэкслер", "Better Call Saul", "epic", "https://postimg.cc/fV9gLm2H", "Ты в деле, Сол.", 400),
            ("Гус Фринг", "Breaking Bad", "epic", "https://postimg.cc/LhQy3NrF", "Всё, что я делаю, я делаю для бизнеса.", 400),
            # Редкие (6)
            ("Депп", "The Boys", "rare", "https://postimg.cc/TL7cQ3Nr", "Меня никто не уважает… даже осьминог.", 200),
            ("Сержант Докс", "Dexter", "rare", "https://postimg.cc/ykSTXBmm", "Я узнаю убийцу, когда вижу его.", 200),
            ("Поли Уолнатс", "The Sopranos", "rare", "https://postimg.cc/gnRvLspZ", "Что ты там говоришь?", 200),
            ("Лало Саламанка", "Better Call Saul", "rare", "https://postimg.cc/XGmCpGz0", "Расскажи это снова.", 200),
            ("Хэнк Шрейдер", "Breaking Bad", "rare", "https://postimg.cc/Czy8088N", "Я найду тебя, Хайзенберг.", 200),
            ("Абигайл Хоббс", "Hannibal", "rare", "https://postimg.cc/cK5KbtZs", "Я не хотела этого.", 200),
            # Необычные (4)
            ("Ханна Маккей", "Dexter", "uncommon", "https://postimg.cc/9rtDjnVB", "Мы созданы друг для друга, Декстер.", 100),
            ("Кармела Сопрано", "The Sopranos", "uncommon", "https://postimg.cc/7JrZFgRG", "Я знаю, кто ты, Тони.", 100),
            ("Майк Эрмантраут", "Better Call Saul", "uncommon", "https://postimg.cc/Sn1NS0PL", "Я просчитываю каждый шаг.", 100),
            ("Тодд Алуист", "Breaking Bad", "uncommon", "https://postimg.cc/dZ9wggdy", "Ничего личного.", 100),
            # Простые (4)
            ("Французик", "The Boys", "common", "https://postimg.cc/5QpWsLd8", "Я люблю этот мир, но он не любит меня.", 50),
            ("Винс Масука", "Dexter", "common", "https://postimg.cc/svVW6hZS", "Это отличный день, чтобы быть живым!", 50),
            ("Дядя Джуниор", "The Sopranos", "common", "https://postimg.cc/nXrDZf2r", "У тебя никогда не было яиц.", 50),
            ("Чак Макгилл", "Better Call Saul", "common", "https://postimg.cc/HcDcQcg9", "Люди не меняются.", 50),
        ]
        for card in cards_data:
            conn.execute("INSERT INTO cards (name, series, rarity, image_url, quote, jobs_award) VALUES (?,?,?,?,?,?)", card)
        conn.commit()

RARITY_CHANCES = {"common":0.44,"uncommon":0.22,"rare":0.15,"epic":0.10,"legendary":0.05,"mythic":0.03,"null":0.01}
RARITY_EMOJI = {"common":"⚪","uncommon":"🟢","rare":"🔵","epic":"🟣","legendary":"🟠","mythic":"🔴","null":"⚫"}

def get_random_card(roll_count):
    r = random.random()
    cum = 0
    chosen = "common"
    for rarity, chance in RARITY_CHANCES.items():
        cum += chance
        if r <= cum:
            chosen = rarity
            break
    if roll_count < 5 and chosen in ["mythic","null"]:
        allowed = {k:v for k,v in RARITY_CHANCES.items() if k not in ["mythic","null"]}
        total = sum(allowed.values())
        r2 = random.random()
        cum2 = 0
        for rarity, chance in allowed.items():
            cum2 += chance/total
            if r2 <= cum2:
                chosen = rarity
                break
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM cards WHERE rarity = ? ORDER BY RANDOM() LIMIT 1", (chosen,))
        return dict(cur.fetchone())

def register_user(user_id, username):
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id, username, total_cards, total_jobs, last_roll, roll_count) VALUES (?,?,0,0,NULL,0)", (user_id, username))
        conn.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))

def can_roll(user_id):
    with get_db() as conn:
        row = conn.execute("SELECT last_roll FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not row or not row["last_roll"]:
        return True, None
    last = datetime.fromisoformat(row["last_roll"])
    now = datetime.now()
    if now - last >= timedelta(hours=2):
        return True, None
    remaining = timedelta(hours=2) - (now - last)
    return False, f"{remaining.seconds//3600} ч {(remaining.seconds%3600)//60} мин"

def give_card(user_id, card, now):
    with get_db() as conn:
        conn.execute("UPDATE users SET roll_count = roll_count + 1 WHERE user_id = ?", (user_id,))
        conn.execute("INSERT INTO user_cards (user_id, card_id, count) VALUES (?,?,1) ON CONFLICT(user_id, card_id) DO UPDATE SET count = count + 1", (user_id, card["card_id"]))
        conn.execute("UPDATE users SET total_cards = total_cards + 1, total_jobs = total_jobs + ?, last_roll = ? WHERE user_id = ?", (card["jobs_award"], now.isoformat(), user_id))

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    register_user(message.from_user.id, message.from_user.username or "no_name")
    await message.answer(
        "📺 *Добро пожаловать в сериальную коллекцию, боец!*\n"
        "Меня зовут *Джоб*, и я помогаю собирать карты легендарных персонажей.\n\n"
        "🎴 *Как играть:*\n"
        "• Каждые 2 часа проси у меня карту: «*Джоб дай карту!*» или /roll\n"
        "• Смотри свою коллекцию: «*Джоб мои карты*» или /mycards\n"
        "• Узнавай баланс джобсов: «*Джоб мой баланс*» или /jobs\n\n"
        "💰 Джобсы пригодятся в будущем магазине. А пока просто копи.\n\n"
        "Да начнётся коллекция!",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📋 *Команды Джоба:*\n\n"
        "/start — запустить бота\n"
        "/help — это сообщение\n"
        "/roll или «*Джоб дай карту!*» — получить карту (раз в 2 часа)\n"
        "/mycards или «*Джоб мои карты*» — показать коллекцию\n"
        "/jobs или «*Джоб мой баланс*» — сколько джобсов накопилось\n\n"
        "Редкости: ⚪ Простая, 🟢 Необычная, 🔵 Редкая, 🟣 Эпическая, 🟠 Легендарная, 🔴 Мифическая, ⚫ Null"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("roll"))
@dp.message(F.text.lower().strip() == "Джоб дай карту!")
async def roll_card(message: Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username or "no_name")
    ok, rem = can_roll(user_id)
    if not ok:
        await message.answer(f"⏳ У Джоба больше нет карт сейчас для вас, отдыхайте, но приходите через ({rem})")
        return
    with get_db() as conn:
        roll_cnt = conn.execute("SELECT roll_count FROM users WHERE user_id = ?", (user_id,)).fetchone()["roll_count"]
    card = get_random_card(roll_cnt)
    give_card(user_id, card, datetime.now())
    rarity_ru = {"common":"Простая","uncommon":"Необычная","rare":"Редкая","epic":"Эпическая","legendary":"Легендарная","mythic":"Мифическая","null":"Null"}[card["rarity"]]
    caption = (
        f"🃏 Джоб достаёт карту «{card['name']} ({card['series']})» 🃏\n"
        f"✨ Редкость: {rarity_ru} ✨\n"
        f"💰 Джобсы: +{card['jobs_award']} 💰\n"
        f"«{card['quote']}»"
    )
    try:
        await message.answer_photo(photo=card["image_url"], caption=caption, parse_mode=ParseMode.MARKDOWN)
    except:
        await message.answer(caption, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("mycards"))
@dp.message(F.text.lower().strip() == "Джоб мои карты")
async def my_cards(message: Message):
    user_id = message.from_user.id
    with get_db() as conn:
        rows = conn.execute('''
            SELECT c.name, c.series, c.rarity, uc.count
            FROM user_cards uc
            JOIN cards c ON uc.card_id = c.card_id
            WHERE uc.user_id = ?
            ORDER BY CASE c.rarity
                WHEN 'common' THEN 1 WHEN 'uncommon' THEN 2 WHEN 'rare' THEN 3
                WHEN 'epic' THEN 4 WHEN 'legendary' THEN 5 WHEN 'mythic' THEN 6 WHEN 'null' THEN 7
            END, c.name
        ''', (user_id,)).fetchall()
    if not rows:
        await message.answer("📭 У тебя пока нет карт. Попроси их у Джоба: Джоб дай карту!")
        return
    total = sum(r["count"] for r in rows)
    msg = f"📖 *Твоя коллекция* (всего {total} карт):\n\n"
    # ГРУППИРОВКА ПО РЕДКОСТИ ЧТОБЫ НЕ ЗАБЫЛ 
    grouped = {}
    for r in rows:
        grouped.setdefault(r["rarity"], []).append(r)
    for rarity in ["common","uncommon","rare","epic","legendary","mythic","null"]:
        if rarity not in grouped:
            continue
        emoji = RARITY_EMOJI[rarity]
        ru = {"common":"Простая","uncommon":"Необычная","rare":"Редкая","epic":"Эпическая","legendary":"Легендарная","mythic":"Мифическая","null":"Null"}[rarity]
        msg += f"{emoji} *{ru}:*\n"
        for c in grouped[rarity]:
            msg += f"  • *{c['name']}* ({c['series']}) — {c['count']} шт.\n"
        msg += "\n"
    await message.answer(msg, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("jobs"))
@dp.message(F.text.lower().strip() == "Джоб мой баланс")
async def show_balance(message: Message):
    with get_db() as conn:
        row = conn.execute("SELECT total_jobs FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    jobs = row["total_jobs"] if row else 0
    await message.answer(f"💰 Джоб пересчитал твои заначки: {jobs} джобсов. Потрать их с умом (В будущем).")

async def main():
    init_db()
    print("✅ Джоб запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())