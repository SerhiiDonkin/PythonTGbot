"""
Створення чат-боту «Прогноз погоди» на Python для Telegram.

=======Використано матеріали:======
Weather API:
https://openweathermap.org/api

Telegram Bot API
https://core.telegram.org/bots/api

Смайлики:
https://www.freecodecamp.org/ukrainian/news/spysok-emodzi-dlya-kopiyuvannya-ta-vstavlennya/

Бот:
t.me/Serhii_Donkin_WeatherBot_bot

"""

import os
import datetime
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_TOKEN = os.getenv("WEATHER_API_KEY")

if not TELEGRAM_TOKEN or not WEATHER_TOKEN:
    raise ValueError("Не знайдено токени у файлі .env")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє команду /start. Надсилає користувачеві вітальне повідомлення
    з інструкцією ввести назву населеного пункту для отримання прогнозу погоди.
    """
    await update.message.reply_text(
        "👋 Вітаю! Введіть назву населеного пункту, і я скажу, яка там погода ☀️"
    )


def get_weather_sync(city: str) -> str:
    """
    Виконує запит до OpenWeatherMap API та повертає відформатовані дані.
    Викликається синхронно у пулі потоків.
    """
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_TOKEN}&units=metric&lang=uk"

    response = None
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return "⚠️ Не вдалося знайти населений пункт. Перевірте правильність написання."
        return f"❌ Помилка API: {e}"
    except requests.exceptions.RequestException:
        return "❌ Помилка з'єднання з погодним сервісом."

    city_name = data["name"]
    dt = data["dt"]
    temp = data["main"]["temp"]
    temp_min = data["main"]["temp_min"]
    temp_max = data["main"]["temp_max"]
    feels_like = data["main"]["feels_like"]
    desc = data["weather"][0]["description"].capitalize()
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]
    wind_gust = data["wind"].get("gust", 0)
    gust_info = f"🌬 Пориви вітру: {wind_gust} м/с" if wind_gust > 0 else ""
    visibility = data["visibility"]
    clouds = data["clouds"]["all"]
    sunrise = data["sys"]["sunrise"]
    sunset = data["sys"]["sunset"]
    icon_code = data["weather"][0]["icon"]
    code_prefix = icon_code[:2]
    icon_map = {
        "01": "☀️",  # Ясно (Сонце/Місяць)
        "02": "🌤️",  # Невелика хмарність
        "03": "🌥️",  # Хмарно з проясненнями
        "04": "☁️",  # Розсіяні хмари
        "09": "🌧️",  # Невеликий дощ
        "10": "☔",  # Дощ
        "11": "⛈️",  # Гроза
        "13": "❄️",  # Сніг
        "50": "🌫️"  # Туман
    }

    if code_prefix == "01" and icon_code.endswith('n'):
        icon = "🌙"
    else:
        icon = icon_map.get(code_prefix, "❓")

    return (
        f"🏠 Населений пункт: {city.capitalize()} / {city_name}\n"
        f"⌚ Останнє оновлення о: {datetime.datetime.fromtimestamp(dt).strftime('%H:%M')}\n"
        f"🌡 Температура: {temp}°C (відчувається як {feels_like}°C)\n"
        f"{icon} {desc}\n"
        f"⬇️ Мінімальна температура: {temp_min}°C\n"
        f"⬆️ Максимальна температура: {temp_max}°C\n"
        f"⛅ Хмарність: {clouds} %\n"
        f"💨 Вітер: {wind} м/с\n"
        f"{gust_info}\n"
        f"💧 Вологість: {humidity}%\n"
        f"👀 Видимість на дорогах: {round(visibility / 1000, 0)} км \n"
        f"🌅 Схід сонця: {datetime.datetime.fromtimestamp(sunrise).strftime('%H:%M')}\n"
        f"🌇 Захід сонця: {datetime.datetime.fromtimestamp(sunset).strftime('%H:%M')}"
    )


async def send_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє текстові повідомлення користувача як назви міст,
    викликаючи get_weather_sync у пулі потоків.
    """
    city = update.message.text.strip()
    await update.message.reply_text(get_weather_sync(city))


def main() -> None:
    """
    Головна функція. Запускає бота.
    """
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_weather))
    print("Бот запущено...")
    app.run_polling()


if __name__ == "__main__":
    main()
