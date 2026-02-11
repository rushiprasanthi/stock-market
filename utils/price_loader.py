# utils/price_loader.py
import requests
import logging
from datetime import datetime
import pytz

from config import (
    STOCK_NAME,
    EXCHANGE_TIMEZONE,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
)

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

def is_market_open(now):
    open_time = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0)
    close_time = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0)
    return open_time <= now <= close_time

def load_price_data():
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{STOCK_NAME}"
    params = {"interval": "1d", "range": "1d"}

    response = requests.get(url, params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()

    result = response.json()["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]

    open_p = quote["open"][0]
    high_p = quote["high"][0]
    low_p = quote["low"][0]
    close_p = quote["close"][0]

    tz = pytz.timezone(EXCHANGE_TIMEZONE)
    now = datetime.now(tz)

    market_open = is_market_open(now)

    price_data = {
        "open": round(open_p, 2),
        "high": round(high_p, 2),
        "low": round(low_p, 2),
        "last": round(close_p, 2),
        "high_time": now.strftime("%H:%M"),
        "low_time": now.strftime("%H:%M"),
        "as_of_time": now.strftime("%d %b %Y, %H:%M %Z"),
        "market_state": "OPEN" if market_open else "CLOSED",
    }

    logger.info("PRICE DATA: %s", price_data)
    return price_data
