import asyncio
import random
import sqlite3
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from flask import Flask
from threading import Thread

# === Мини вебсервер для Render (чтобы не было тайм аута) ===
app_web = Flask('')

@app_web.route('/')
def home():
    return "Бот Джоб работает"

def run():
    port = int(os.environ.get('PORT', 5000))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ========================================================

TOKEN = os.environ["BOT_TOKEN"]
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
        conn.execute("DELETE FROM cards")
        # 2 варианта, должны быть ссылки на это (i.postimg.cc) либо нахуй переделывать и давать прямую ссылку (если не робит)
        cards_data = [
            ("Хоумлендер", "The Boys", "null", "https://i.postimg.cc/B8mcpvtw/Homelander.jpg", "Я здесь бог.", 3000),
            ("Мясник", "The Boys", "mythic", "https://i.postimg.cc/8J1v2gfH/Butcher.jpg", "Мы спасём эту чёртову страну!", 1700),
            ("Декстер Морган", "Dexter", "mythic", "https://i.postimg.cc/V0JJwffZ/Dexter.jpg", "Сегодня ночью — охота.", 1700),
            ("Тони Сопрано", "The Sopranos", "mythic", "https://i.postimg.cc/tZTTdqVf/Tony.jpg", "Я пришёл за утками.", 1700),
            ("Ганнибал Лектер", "Hannibal", "mythic", "https://i.postimg.cc/mcpCM65Z/Hannibal.jpg", "Печень — с бобами.", 1700),
            ("Уолтер Уайт", "Breaking Bad", "mythic", "https://i.postimg.cc/v18HMYXZ/Walter.jpg", "Я — тот, кто стучит.", 1700),
            ("Королева Мэйв", "The Boys", "legendary", "https://i.postimg.cc/Mn9J7ybS/Maeve.jpg", "Хватит притворяться, Хоумлендер.", 800),
            ("Джесси Пинкман", "Breaking Bad", "legendary", "https://i.postimg.cc/gLFCz4d5/Jesse.jpg", "Наука, bitch!", 800),
            ("Тринити-киллер", "Dexter", "legendary", "https://i.postimg.cc/4YLj7Xst/Trinity.jpg", "Всё кончено, Декстер.", 800),
            ("Сол Гудман", "Better Call Saul", "legendary", "https://i.postimg.cc/hfKY2XGb/Saul.jpg", "Позвоните Солу!", 800),
            ("Уилл Грэм", "Hannibal", "legendary", "https://i.postimg.cc/fSD8qPML/Will.jpg", "Это красиво.", 800),
            ("Энни (Старлайт)", "The Boys", "epic", "https://i.postimg.cc/mt2stXCw/Annie.jpg", "Я верю в добро, даже если его почти не осталось.", 400),
            ("Дебра Морган", "Dexter", "epic", "https://i.postimg.cc/2bFs5h6Y/Debra.jpg", "Ты мне отвратителен, но я люблю тебя, брат.", 400),
            ("Кристофер Молтисанти", "The Sopranos", "epic", "https://i.postimg.cc/SJKByXpS/Christopher.jpg", "Моя судьба — кино, а не это дерьмо.", 400),
            ("Ким Уэкслер", "Better Call Saul", "epic", "https://i.postimg.cc/fV9gLm2H/Kim.jpg", "Ты в деле, Сол.", 400),
            ("Гус Фринг", "Breaking Bad", "epic", "https://i.postimg.cc/LhQy3NrF/Gus.jpg", "Всё, что я делаю, я делаю для бизнеса.", 400),
            ("Депп", "The Boys", "rare", "https://i.postimg.cc/TL7cQ3Nr/Deep.jpg", "Меня никто не уважает… даже осьминог.", 200),
            ("Сержант Докс", "Dexter", "rare", "https://i.postimg.cc/ykSTXBmm/Doakes.jpg", "Я узнаю убийцу, когда вижу его.", 200),
            ("Поли Уолнатс", "The Sopranos", "rare", "https://i.postimg.cc/gnRvLspZ/Paulie.jpg", "Что ты там говоришь?", 200),
            ("Лало Саламанка", "Better Call Saul", "rare", "https://i.postimg.cc/XGmCpGz0/Lalo.jpg", "Расскажи это снова.", 200),
            ("Хэнк Шрейдер", "Breaking Bad", "rare", "https://i.postimg.cc/Czy8088N/Hank.jpg", "Я найду тебя, Хайзенберг.", 200),
            ("Абигайл Хоббс", "Hannibal", "rare", "https://i.postimg.cc/cK5KbtZs/Abigail.jpg", "Я не хотела этого.", 200),
            ("Ханна Маккей", "Dexter", "uncommon", "https://i.postimg.cc/9rtDjnVB/Hannah.jpg", "Мы созданы друг для друга, Декстер.", 100),
            ("Кармела Сопрано", "The Sopranos", "uncommon", "https://i.postimg.cc/7JrZFgRG/Carmela.jpg", "Я знаю, кто ты, Тони.", 100),
            ("Майк Эрмантраут", "Better Call Saul", "uncommon", "https://i.postimg.cc/Sn1NS0PL/Mike.jpg", "Я просчитываю каждый шаг.", 100),
            ("Тодд Алуист", "Breaking Bad", "uncommon", "https://i.postimg.cc/dZ9wggdy/Todd.jpg", "Ничего личного.", 100),
            ("Французик", "The Boys", "common", "https://i.postimg.cc/5QpWsLd8/Frenchie.jpg", "Я люблю этот мир, но он не любит меня.", 50),
            ("Винс Масука", "Dexter", "common", "https://i.postimg.cc/svVW6hZS/Masuka.jpg", "Это отличный день, чтобы быть живым!", 50),
            ("Дядя Джуниор", "The Sopranos", "common", "https://i.postimg.cc/nXrDZf2r/UncleJunior.jpg", "У тебя никогда не было яиц.", 50),
            ("Чак Макгилл", "Better Call Saul", "common", "https://i.postimg.cc/HcDcQcg9/Chuck.jpg", "Люди не меняются.", 50),
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
    if roll_count < 10 and chosen in ["legendary","mythic","null"]:
        allowed = {k:v for k,v in RARITY_CHANCES.items() if k not in ["legendary","mythic","null"]}
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

# ----- Функция для "нормы" текста ( не будет пробелов, знаков препинания) -----
def normalize_text(text: str) -> str:
    # удаляем лишние пробелы, знаки препинания в конце, приводим к нижнему регистру
    text = text.strip().lower()
    # убираем восклицательные знаки, точки, запятые в конце
    text = text.rstrip('!.,;')
    # заменяем множественные пробелы на один
    return ' '.join(text.split())

@dp.message(Command("start"))
async def cmd_start(message: Message):
    register_user(message.from_user.id, message.from_user.username or "no_name")
    await message.answer(
        "📺 *Добро пожаловать в сериальную коллекцию, боец!*\n"
        "Меня зовут *Джоб*, и я помогаю собирать карты легендарных персонажей.\n\n"
        "🎴 *Как играть:*\n"
        "• Каждые 2 часа проси у меня карту: «*Джоб дай карту*»\n"
        "• Смотри свою коллекцию: «*Джоб мои карты*»\n"
        "• Узнавай баланс джобсов: «*Джоб мой баланс*»\n\n"
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
        "«Джоб дай карту» — получить карту (раз в 2 часа)\n"
        "«Джоб мои карты» — показать коллекцию\n"
        "«Джоб мой баланс» — сколько джобсов накопилось"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

# Мини обработчик текстовых команд (Джоб дай карту, Джоб мои карты, Джоб мой баланс)
@dp.message(F.text)
async def text_commands(message: Message):
    user_id = message.from_user.id
    text = normalize_text(message.text)
    
    # Проверяем фразы
    if text in ["джоб дай карту", "джоб дай карту!", "джоб, дай карту"] or text.startswith("джоб дай карту"):
        # Вызываем ту же логику, что и /roll
        await roll_card(message)
    elif text in ["джоб мои карты", "джоб, мои карты", "джоб мои карты!"]:
        await my_cards(message)
    elif text in ["джоб мой баланс", "джоб, мой баланс", "джоб мой баланс!"]:
        await show_balance(message)

@dp.message(Command("roll"))
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
    except Exception as e:
        # Если не удалось отправить картинку, отправляем только текст для теста бота и т.д.
        await message.answer(caption, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("mycards"))
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
async def show_balance(message: Message):
    with get_db() as conn:
        row = conn.execute("SELECT total_jobs FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    jobs = row["total_jobs"] if row else 0
    await message.answer(f"💰 Джоб пересчитал твои заначки: {jobs} джобсов. Потрать их с умом (В будущем).")

async def main():
    init_db()
    print("✅ Джоб запущен и готов к работе!")
    await dp.start_polling(bot)

# Запуск вебсервера (чтобы Render не пиздел дохуя) и бота
keep_alive()

if __name__ == "__main__":
    asyncio.run(main())