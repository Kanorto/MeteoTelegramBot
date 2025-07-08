"""Helpers for working with X-RAS magnetic storm forecast."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import aiohttp

BASE_URL = "https://xras.ru"

# Default region used on the site (Москва)
DEFAULT_REGION = "RAL5"

REGION_JS_URL = f"{BASE_URL}/regions_js_dk.php"


async def fetch_forecast(region: str = DEFAULT_REGION) -> Optional[dict]:
    """Fetch 3-day forecast for the given region code."""

    url = f"{BASE_URL}/txt/kpf_{region}.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
    return None


def format_forecast(data: dict) -> str:
    """Format short forecast information for sending to users."""

    if not data or "data" not in data:
        return "Нет данных о магнитных бурях"

    lines = []
    for day in data["data"]:
        date = day.get("time")
        kp = day.get("max_kp")
        lines.append(f"{date}: Kp={kp}")
    return "\n".join(lines)


_regions_cache: Optional[Dict[str, Dict[str, str]]] = None


def _parse_regions_js(js: str) -> Dict[str, Dict[str, str]]:
    """Parse regions_js_dk.php content."""

    m = re.search(r"var reglist = \[(.*?)]\s*;", js, re.S)
    if not m:
        return {}
    items = re.findall(r'\["([^\"]+)","([^\"]+)","([^\"]+)","([^\"]+)"\]', m.group(1))
    result: Dict[str, Dict[str, str]] = {}
    for code, name, alias, geo in items:
        result[code] = {"name": name, "alias": alias, "geo": geo}
    return result


async def fetch_regions() -> Dict[str, Dict[str, str]]:
    """Return mapping of region code to region info."""

    global _regions_cache
    if _regions_cache is not None:
        return _regions_cache

    async with aiohttp.ClientSession() as session:
        async with session.get(REGION_JS_URL) as resp:
            if resp.status != 200:
                return {}
            text = await resp.text()

    _regions_cache = _parse_regions_js(text)
    return _regions_cache
