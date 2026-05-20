import asyncio
import os
import requests

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from deep_translator import GoogleTranslator

# =========================================
# ТОКЕНЫ
# =========================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

if not BOT_TOKEN:
    raise ValueError("Ошибка! Переменная окружения BOT_TOKEN не установлена!")
if not WEATHER_API_KEY:
    raise ValueError("Ошибка! Переменная окружения WEATHER_API_KEY не установлена!")

# =========================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())

# =========================================
# СОСТОЯНИЯ
# =========================================

class UserState(StatesGroup):
    weather = State()
    translate = State()

# =========================================
# МЕНЮ
# =========================================

main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🌤 Погода", callback_data="weather")],
        [InlineKeyboardButton(text="🌍 Переводчик", callback_data="translator")]
    ]
)

# =========================================
# ЯЗЫКИ
# =========================================

language_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 Английский", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇩🇪 Немецкий", callback_data="lang_de")],
        [InlineKeyboardButton(text="🇫🇷 Французский", callback_data="lang_fr")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
    ]
)

# =========================================
# КНОПКА НАЗАД
# =========================================

translate_back_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back")],
        [InlineKeyboardButton(text="🌍 Сменить язык", callback_data="change_language")]
    ]
)
weather_back_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")]
    ]
)

# =========================================
# START
# =========================================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать!\n\nВыбери функцию бота:",
        reply_markup=main_menu
    )

# =========================================
# НАЗАД
# =========================================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=main_menu
    )

@dp.callback_query(F.data == "change_language")
async def change_language(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🌍 Выбери новый язык:",
        reply_markup=language_menu
    )

# =========================================
# ПОГОДА
# =========================================

@dp.callback_query(F.data == "weather")
async def weather(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.weather)
    await callback.message.edit_text(
        "🏙 Напиши название города:",
        reply_markup=weather_back_menu
    )

# =========================================
# ПЕРЕВОДЧИК
# =========================================

@dp.callback_query(F.data == "translator")
async def translator(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌍 Выбери язык перевода:",
        reply_markup=language_menu
    )

# =========================================
# ВЫБОР ЯЗЫКА
# =========================================

@dp.callback_query(F.data.startswith("lang_"))
async def choose_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    await state.set_state(UserState.translate)
    await callback.message.edit_text(
        "✍️ Теперь отправь текст для перевода:",
        reply_markup=translate_back_menu
    )

# =========================================
# ОБРАБОТКА ПОГОДЫ
# =========================================

@dp.message(UserState.weather)
async def get_weather(message: Message):
    city = message.text
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    )
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != 200:
            await message.answer("❌ Город не найден")
            return
        city_name = data["name"]
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        weather_desc = data["weather"][0]["description"]
        result = (
            f"🌍 <b>{city_name}</b>\n\n"
            f"🌡 Температура: <b>{temp}°C</b>\n"
            f"🤔 Ощущается: <b>{feels}°C</b>\n"
            f"💧 Влажность: <b>{humidity}%</b>\n"
            f"🌬 Ветер: <b>{wind} м/с</b>\n"
            f"☁️ Погода: <b>{weather_desc}</b>"
        )
        await message.answer(result, reply_markup=weather_back_menu)
    except Exception as e:
        print(e)
        await message.answer("⚠️ Ошибка получения погоды")

# =========================================
# ОБРАБОТКА ПЕРЕВОДА
# =========================================

@dp.message(UserState.translate)
async def translate_text(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        language = data.get("language")
        translated = GoogleTranslator(source="auto", target=language).translate(message.text)
        await message.answer(f"🌍 Перевод:\n\n{translated}", reply_markup=translate_back_menu)
    except Exception as e:
        print(e)
        await message.answer("⚠️ Ошибка перевода")

# =========================================
# ЗАПУСК
# =========================================

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


