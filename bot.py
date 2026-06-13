import asyncio
import random
import sqlite3
import html
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from flask import Flask
from threading import Thread

# === Веб-сервер (отдельный поток, чтобы Render не убивал) ===
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
# =========================================================

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
        # БАЗА ДАННЫХ КАРТ
        conn.execute("DELETE FROM cards")
        cards_data = [
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
        for card in cards_data:
            conn.execute("INSERT INTO cards (name, series, rarity, image_url, quote, jobs_award) VALUES (?,?,?,?,?,?)", card)
        conn.commit()
        # ПРОВЕРКА КОЛИЧЕСТВА КАРТИ
        count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        print(f"Инициализация БД: добавлено {count} карт")

RARITY_CHANCES = {"common":0.44,"uncommon":0.22,"rare":0.15,"epic":0.10,"legendary":0.05,"mythic":0.03,"null":0.01}
RARITY_EMOJI = {"common":"⚪","uncommon":"🟢","rare":"🔵","epic":"🟣","legendary":"🟠","mythic":"🔴","null":"⚫"}

def get_random_card(roll_count):
    print("DEBUG: get_random_card вызвана, roll_count=", roll_count)
    r = random.random()
    cum = 0
    chosen = "common"
    for rarity, chance in RARITY_CHANCES.items():
        cum += chance
        if r <= cum:
            chosen = rarity
            break
    print(f"Выбрана редкость: {chosen}")
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
        print(f"Сработала защита, новая редкость: {chosen}")
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM cards WHERE rarity = ? ORDER BY RANDOM() LIMIT 1", (chosen,))
        card = cur.fetchone()
        if card is None:
            print(f"ОШИБКА: нет карт с редкостью {chosen}")
            # fallback – взять любую карту
            cur = conn.execute("SELECT * FROM cards ORDER BY RANDOM() LIMIT 1")
            card = cur.fetchone()
        return dict(card)

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
    if now - last >= timedelta(hours=4):
        return True, None
    remaining = timedelta(hours=4) - (now - last)
    return False, f"{remaining.seconds//3600} ч {(remaining.seconds%3600)//60} мин"

def give_card_to_user(user_id, card, now):
    with get_db() as conn:
        conn.execute("UPDATE users SET roll_count = roll_count + 1 WHERE user_id = ?", (user_id,))
        conn.execute("INSERT INTO user_cards (user_id, card_id, count) VALUES (?,?,1) ON CONFLICT(user_id, card_id) DO UPDATE SET count = count + 1", (user_id, card["card_id"]))
        conn.execute("UPDATE users SET total_cards = total_cards + 1, total_jobs = total_jobs + ?, last_roll = ? WHERE user_id = ?", (card["jobs_award"], now.isoformat(), user_id))

bot = Bot(token=TOKEN)
dp = Dispatcher()

def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = text.rstrip('!.,;')
    return ' '.join(text.split())

@dp.message(Command("start"))
async def cmd_start(message: Message):
    register_user(message.from_user.id, message.from_user.username or "no_name")
    await message.answer(
        "📺 *Добро пожаловать в сериальную коллекцию, боец!*\n"
        "Меня зовут *Джоб*, и я помогаю собирать карты легендарных персонажей.\n\n"
        "🎴 *Как играть:*\n"
        "• Каждые 4 часа проси у меня карту: «*Джоб дай карту*»\n"
        "• Смотри свою коллекцию: «*Джоб мои карты*»\n"
        "• Узнавай баланс джобсов: «*Джоб мой баланс*»\n\n"
        "💰 Джобсы пригодятся в будущем магазине. А пока просто копи.\n\n"
        "🏆 Попади в глобальный *ТОП 10 по джобсам!*\n\n" 
        "Да начнётся коллекция!",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📋 *Команды Джоба:*\n\n"
        "/start - запустить бота\n"
        "/help - это сообщение\n"
        "/topjobs - глобальный топ 10 по джобсам!\n"
        "/roll или Джоб дай карту - получить случайную карту (раз в 4 часа)\n"
        "/mycards или Джоб мои карты - показать коллекцию\n"
        "/jobs или Джоб мой баланс - сколько джобсов накопилось"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("roll"))
async def roll_card(message: Message):
    print("DEBUG: /roll команда получена")
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username or "no_name")
    ok, rem = can_roll(user_id)
    if not ok:
        await message.answer(f"⏳ У Джоба больше нет карт сейчас для вас, отдыхайте, но приходите через ({rem})")
        return
    with get_db() as conn:
        roll_cnt = conn.execute("SELECT roll_count FROM users WHERE user_id = ?", (user_id,)).fetchone()["roll_count"]
    card = get_random_card(roll_cnt)
    give_card_to_user(user_id, card, datetime.now())
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
        print(f"Ошибка отправки фото: {e}")
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

@dp.message(Command("topjobs"))
async def top_jobs(message: Message):
    try:
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT username, total_jobs FROM users
                WHERE total_jobs > 0
                ORDER BY total_jobs DESC
                LIMIT 10
            ''').fetchall()
        if not rows:
            await message.answer("💰 Пока никто не заработал ни одного джобса. Начни первым!")
            return
        text = "🏆 <b>Топ 10 по джобсам:</b>\n\n"
        medals = {1:"🥇",2:"🥈",3:"🥉",4:"4️⃣",5:"5️⃣",6:"6️⃣",7:"7️⃣",8:"8️⃣",9:"9️⃣",10:"🔟"}
        for i, row in enumerate(rows, 1):
            raw_username = row["username"]
            if not raw_username or raw_username == "no_name":
                username = "Аноним"
            else:
                username = html.escape(raw_username).replace("@", "")
            medal = medals.get(i, f"{i}.")
            text += f"{medal} <b>{username}</b> — {row['total_jobs']} 🪙\n"
        await message.answer(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Ошибка topjobs: {e}")
        await message.answer("⚠️ Ошибка при загрузке топа. Попробуй позже.")

@dp.message(Command("check_cards"))
async def check_cards(message: Message):
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        sample = conn.execute("SELECT name FROM cards LIMIT 5").fetchall()
        names = [row["name"] for row in sample]
        await message.answer(f"Всего карт: {count}\nПервые 5: {', '.join(names)}")

@dp.message(Command("cards_list"))
async def cards_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    with get_db() as conn:
        rows = conn.execute("SELECT card_id, name FROM cards ORDER BY card_id").fetchall()
        text = "📋 Список карт (ID: название):\n" + "\n".join([f"{r['card_id']}: {r['name']}" for r in rows])
        await message.answer(text)

@dp.message(F.text & ~F.text.startswith("/"))
async def text_commands(message: Message):
    print("DEBUG: текстовая команда получена:", message.text)
    user_id = message.from_user.id
    text = normalize_text(message.text)
    if text in ["джоб дай карту", "джоб дай карту!", "джоб, дай карту"] or text.startswith("джоб дай карту"):
        print("DEBUG: распознана фраза 'джоб дай карту'")
        await roll_card(message)
    elif text in ["джоб мои карты", "джоб, мои карты", "джоб мои карты!"]:
        await my_cards(message)
    elif text in ["джоб мой баланс", "джоб, мой баланс", "джоб мой баланс!"]:
        await show_balance(message)

# ========== АДМИН-КОМАНДЫ ==========
ADMIN_ID = 6990974323

@dp.message(Command("give_jobs"))
async def give_jobs(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Используй: /give_jobs @username количество")
        return
    target_username = args[1].lstrip('@')
    try:
        amount = int(args[2])
    except:
        await message.answer("❌ Количество должно быть числом.")
        return
    with get_db() as conn:
        cur = conn.execute("SELECT user_id, username FROM users WHERE username = ?", (target_username,))
        user = cur.fetchone()
        if not user:
            await message.answer(f"❌ Пользователь @{target_username} не найден в базе (он должен хотя бы раз написать боту).")
            return
        target_id = user["user_id"]
        conn.execute("UPDATE users SET total_jobs = total_jobs + ? WHERE user_id = ?", (amount, target_id))
        await message.answer(f"✅ Выдано {amount} джобсов пользователю @{target_username}.")

@dp.message(Command("give_card"))
async def give_card(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Используй: /give_card @username ID_карты_или_название")
        return
    target_username = args[1].lstrip('@')
    query = ' '.join(args[2:]).strip()
    with get_db() as conn:
        # Находим пользователя
        cur = conn.execute("SELECT user_id, username FROM users WHERE username = ?", (target_username,))
        user = cur.fetchone()
        if not user:
            await message.answer(f"❌ Пользователь @{target_username} не найден.")
            return
        target_id = user["user_id"]
        # Пытаемся найти карту: сначала по ID (если ввод — число)
        card = None
        if query.isdigit():
            cur = conn.execute("SELECT * FROM cards WHERE card_id = ?", (int(query),))
            card = cur.fetchone()
        if not card:
            # Поиск по названию: убираем лишние пробелы, приводим к нижнему регистру
            query_clean = query.lower().replace('  ', ' ').strip()
            cur = conn.execute("SELECT * FROM cards WHERE LOWER(REPLACE(name, ' ', '')) = LOWER(REPLACE(?, ' ', ''))", (query_clean,))
            card = cur.fetchone()
        if not card:
            # Если не нашли — выводим список всех карт с ID
            all_cards = conn.execute("SELECT card_id, name FROM cards ORDER BY card_id").fetchall()
            card_lines = [f"{c['card_id']}: {c['name']}" for c in all_cards[:20]]
            await message.answer("❌ Карта не найдена.\nИспользуй ID или название.\nСписок карт (ID: название):\n" + "\n".join(card_lines))
            return
        card_dict = dict(card)
        now = datetime.now()
        # Выдаём карту
        conn.execute("""
            INSERT INTO user_cards (user_id, card_id, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, card_id) DO UPDATE SET count = count + 1
        """, (target_id, card_dict["card_id"]))
        conn.execute("""
            UPDATE users
            SET total_cards = total_cards + 1,
                total_jobs = total_jobs + ?
            WHERE user_id = ?
        """, (card_dict["jobs_award"], target_id))
        # Отправляем сообщение (с картинкой или без)
        rarity_ru = {"common":"Простая","uncommon":"Необычная","rare":"Редкая","epic":"Эпическая","legendary":"Легендарная","mythic":"Мифическая","null":"Null"}
        caption = (
            f"🃏 *Админ-разработчик бота Джоб лично выдал карту* «{card_dict['name']} ({card_dict['series']})» пользователю @{target_username} 🃏\n"
            f"✨ Редкость: {rarity_ru[card_dict['rarity']]} ✨\n"
            f"💰 Джобсы: +{card_dict['jobs_award']} 💰\n"
            f"«{card_dict['quote']}»"
        )
        try:
            await message.answer_photo(photo=card_dict["image_url"], caption=caption, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await message.answer(caption, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("reset_user"))
async def reset_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /reset_user @username")
        return
    target_username = args[1].lstrip('@')
    with get_db() as conn:
        cur = conn.execute("SELECT user_id, username FROM users WHERE username = ?", (target_username,))
        user = cur.fetchone()
        if not user:
            await message.answer(f"❌ Пользователь @{target_username} не найден.")
            return
        target_id = user["user_id"]
        conn.execute("DELETE FROM user_cards WHERE user_id = ?", (target_id,))
        conn.execute("UPDATE users SET total_cards = 0, total_jobs = 0, last_roll = NULL, roll_count = 0 WHERE user_id = ?", (target_id,))
        await message.answer(f"✅ Прогресс пользователя @{target_username} полностью сброшен.")
# ===============================================

async def main():
    init_db()
    print("✅ Джоб запущен и готов к работе!")
    await dp.start_polling(bot)

keep_alive()

if __name__ == "__main__":
    asyncio.run(main())