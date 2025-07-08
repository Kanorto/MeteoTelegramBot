from typing import Callable, Dict

from . import open_meteo, yandex

ProviderFunc = Callable[[float, float], object]

PROVIDERS: Dict[str, ProviderFunc] = {
    "open-meteo": open_meteo.fetch_weather,
    "yandex": yandex.fetch_weather,
}

FORMATTERS: Dict[str, Callable[[dict], str]] = {
    "open-meteo": open_meteo.format_weather,
}
