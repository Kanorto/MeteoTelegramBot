import asyncio
import logging
from typing import Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from .config import BOT_TOKEN, DEFAULT_NOTIFY_TIME, DEFAULT_MAGNETIC_REGION
from .storage import Storage
from .scheduler import Scheduler
from .weather.providers import PROVIDERS, FORMATTERS
from .weather import open_meteo
from .magnetic import xras

logging.basicConfig(level=logging.INFO)

storage = Storage()
scheduler = Scheduler()


def get_location(city: str) -> Tuple[float, float]:
    # TODO: replace with real geocoding service
    # For demo, return Moscow coordinates
    return 55.7558, 37.6173


def schedule_user_notifications(app: Application, user_id: int, settings: dict):
    time_str = settings.get("notify_time", DEFAULT_NOTIFY_TIME)

    async def send_updates():
        lat, lon = get_location(settings.get("city", "Moscow"))
        provider_name = settings.get("provider", "open-meteo")
        provider = PROVIDERS.get(provider_name, open_meteo.fetch_weather)
        formatter = FORMATTERS.get(provider_name, open_meteo.format_weather)

        weather_data = None
        try:
            weather_data = await provider(lat, lon)
        except Exception as exc:
            logging.exception("Weather fetch failed: %s", exc)
        text = ""
        if weather_data:
            text += "Погода сегодня:\n" + formatter(weather_data) + "\n\n"
        region_code = settings.get("magnetic_region", DEFAULT_MAGNETIC_REGION)
        magnetic_data = await xras.fetch_forecast(region_code)
        if magnetic_data:
            text += xras.format_forecast(magnetic_data)
        else:
            text += "Нет данных о магнитных бурях"
        await app.bot.send_message(chat_id=user_id, text=text)

    scheduler.schedule_daily(time_str, lambda: asyncio.create_task(send_updates()))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    storage.set_user(
        user_id,
        {
            "city": "Moscow",
            "provider": "open-meteo",
            "notify_time": DEFAULT_NOTIFY_TIME,
            "magnetic_region": DEFAULT_MAGNETIC_REGION,
        },
    )
    await update.message.reply_text(
        "Привет! Я бот прогноза погоды и магнитных бурь. Настройки по умолчанию установлены."
    )
    schedule_user_notifications(context.application, user_id, storage.get_user(user_id))


ACTION_PREFIX = "settings_"


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Изменить город", callback_data=f"{ACTION_PREFIX}city")],
        [InlineKeyboardButton("Изменить время", callback_data=f"{ACTION_PREFIX}time")],
        [InlineKeyboardButton("Изменить источник", callback_data=f"{ACTION_PREFIX}provider")],
        [InlineKeyboardButton("Изменить регион магнитных данных", callback_data=f"{ACTION_PREFIX}magnetic")],
    ]
    await update.message.reply_text("Настройки:", reply_markup=InlineKeyboardMarkup(keyboard))


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if data == f"{ACTION_PREFIX}city":
        await query.edit_message_text("Пришлите название города")
        context.user_data["awaiting_city"] = True
    elif data == f"{ACTION_PREFIX}time":
        await query.edit_message_text("Введите время в формате ЧЧ:ММ")
        context.user_data["awaiting_time"] = True
    elif data == f"{ACTION_PREFIX}provider":
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"provider_{name}")] for name in PROVIDERS.keys()
        ]
        await query.edit_message_text("Выберите источник:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == f"{ACTION_PREFIX}magnetic":
        await query.edit_message_text("Введите код региона магнитной активности (например, RAL5)")
        context.user_data["awaiting_region"] = True
    elif data.startswith("provider_"):
        provider = data.split("_", 1)[1]
        user = storage.get_user(user_id)
        user["provider"] = provider
        storage.set_user(user_id, user)
        await query.edit_message_text(f"Источник обновлен: {provider}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    user = storage.get_user(user_id)
    if context.user_data.get("awaiting_city"):
        user["city"] = text
        storage.set_user(user_id, user)
        await update.message.reply_text(f"Город изменен на {text}")
        context.user_data.pop("awaiting_city")
        schedule_user_notifications(context.application, user_id, user)
    elif context.user_data.get("awaiting_time"):
        user["notify_time"] = text
        storage.set_user(user_id, user)
        await update.message.reply_text(f"Время уведомлений {text}")
        context.user_data.pop("awaiting_time")
        schedule_user_notifications(context.application, user_id, user)
    elif context.user_data.get("awaiting_region"):
        user["magnetic_region"] = text
        storage.set_user(user_id, user)
        await update.message.reply_text(f"Регион магнитных данных {text}")
        context.user_data.pop("awaiting_region")
        schedule_user_notifications(context.application, user_id, user)


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = storage.get_user(user_id)
    lat, lon = get_location(user.get("city", "Moscow"))
    provider_name = user.get("provider", "open-meteo")
    provider = PROVIDERS.get(provider_name)
    formatter = FORMATTERS.get(provider_name)
    data = await provider(lat, lon)
    await update.message.reply_text(formatter(data))


async def magnetic_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = storage.get_user(user_id)
    region = user.get("magnetic_region", DEFAULT_MAGNETIC_REGION)
    data = await xras.fetch_forecast(region)
    await update.message.reply_text(xras.format_forecast(data))


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN env variable is required")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("magnetic", magnetic_command))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()


if __name__ == "__main__":
    asyncio.run(main())
