import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandObject
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
import datetime

import os
API_TOKEN = os.getenv("BOT_TOKEN") or "TOKEN_NOT_SET"
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect("iris.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0,
    role TEXT DEFAULT '',
    vip INTEGER DEFAULT 0,
    description TEXT DEFAULT '',
    age INTEGER DEFAULT NULL,
    last_salary TEXT DEFAULT '',
    last_spin TEXT DEFAULT '',
    admin_level TEXT DEFAULT ''
)
""")
conn.commit()

admin_levels = [
    "младший администратор", "средний администратор", "старший администратор",
    "главный администратор", "создатель", "владелец проекта",
    "команда 🌸iris", "менеджер 🌸iris", "создатель 🌸iris"
]

roles = {
    "🧑‍🔧Механик": 300,
    "🚌Водитель Автобуса": 250,
    "👮‍♂️ Полицейский": 1000,
    "🚛-Дальнобойщик": 400,
    "🧯Пожарный": 1000,
    "👨‍⚕️Медик": 1000
}

vip_price = 1000000

@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = message.text.lower().strip()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()

    if text == "кто я" or text == "кто ты":
        vip = "👑VIP" if user[3] else ""
        age = f"Возраст: {user[5]}" if user[5] else "Возраст не указан"
        desc = f"📝Описание: {user[4]}" if user[4] else ""
        admin = f"🛡 {user[7]}" if user[7] else ""
        await message.answer(f"""🆔 <b>{message.from_user.full_name}</b>
💰 Монеты: {user[1]} EH - Coin🪙
🔧 Работа: {user[2] or "Нет"}
🎂 {age}
{vip}
{admin}
{desc}""")
    elif text == "+возраст":
        await message.answer("Введите ваш возраст (1-100):")
    elif text.isdigit() and 1 <= int(text) <= 100:
        cursor.execute("UPDATE users SET age=? WHERE user_id=?", (int(text), user_id))
        conn.commit()
        await message.answer("Возраст установлен.")
    elif text == "+роль":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=role, callback_data=f"role:{role}")]
            for role in roles.keys()
        ])
        await message.answer("Выберите вашу роль:", reply_markup=keyboard)
    elif text == "🎰":
        now = datetime.datetime.utcnow()
        last = user[6]
        if last and (now - datetime.datetime.fromisoformat(last)).total_seconds() < 3600:
            await message.answer("🎰 Уже крутили. Попробуйте позже.")
        else:
            cursor.execute("UPDATE users SET coins=coins+100, last_spin=? WHERE user_id=?", (now.isoformat(), user_id))
            conn.commit()
            await message.answer("🎰 Поздравляем! Вы выиграли 100 EH - Coin🪙!")
    elif text == "купить вип":
        if user[1] >= vip_price:
            cursor.execute("UPDATE users SET coins=coins-?, vip=1 WHERE user_id=?", (vip_price, user_id))
            conn.commit()
            await message.answer("👑 VIP успешно приобретён!")
        else:
            await message.answer("🚨У вас недостаточно EH-Coin🪙")
    elif text.startswith("описание") and user[3]:
        desc = message.text.replace("описание", "").strip()
        cursor.execute("UPDATE users SET description=? WHERE user_id=?", (desc, user_id))
        conn.commit()
        await message.answer("Описание обновлено.")
    elif text == "правила":
        try:
            with open("rules.txt", "r", encoding="utf-8") as f:
                await message.answer(f.read())
        except:
            await message.answer("Правила пока не установлены.")
    elif text.startswith("установить правила") and message.from_user.id == 7937614077:
        rules = message.text.replace("установить правила", "").strip()
        with open("rules.txt", "w", encoding="utf-8") as f:
            f.write(rules)
        await message.answer("Правила обновлены.")
    elif text == "ук рф":
        await message.answer("🔗 https://www.consultant.ru/document/cons_doc_LAW_10699/")
    elif text == "карта":
        await message.answer("🗺 КАРТА: https://www.google.com/search?q=Emergency+Hamburg+карта")
    elif text == "калл" and message.chat.type != "private":
        await message.answer("@all 🔔", disable_notification=False)

@dp.callback_query()
async def handle_callbacks(callback_query: types.CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    if data.startswith("role:"):
        role = data.split(":", 1)[1]
        cursor.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
        conn.commit()
        await callback_query.message.answer(f"Роль установлена: {role}")
        await callback_query.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())