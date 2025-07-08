import datetime as dt
from typing import Optional

import aiohttp

BASE_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_weather(lat: float, lon: float) -> Optional[dict]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
    return None


def format_weather(data: dict) -> str:
    daily = data.get("daily", {})
    today = 0
    if not daily:
        return "Нет данных погоды"
    t_max = daily.get("temperature_2m_max", [None])[today]
    t_min = daily.get("temperature_2m_min", [None])[today]
    precip = daily.get("precipitation_sum", [None])[today]
    return (
        f"Макс: {t_max}°C\n"
        f"Мин: {t_min}°C\n"
        f"Осадки: {precip}мм"
    )
