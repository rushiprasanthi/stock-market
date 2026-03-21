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
    # volume may be present in the quote indicators
    volume = None
    try:
        volume = int(quote.get("volume", [None])[0])
    except Exception:
        volume = None

    tz = pytz.timezone(EXCHANGE_TIMEZONE)
    now = datetime.now(tz)

    market_open = is_market_open(now)

    price_data = {
        "open": round(open_p, 2),
        "high": round(high_p, 2),
        "low": round(low_p, 2),
        "last": round(close_p, 2),
        "volume": int(volume) if volume is not None else None,
        "high_time": now.strftime("%H:%M"),
        "low_time": now.strftime("%H:%M"),
        "as_of_time": now.strftime("%d %b %Y, %H:%M %Z"),
        "market_state": "OPEN" if market_open else "CLOSED",
    }

    logger.info("PRICE DATA: %s", price_data)
    return price_data


def fetch_historical_30d(min_days=30):
    """Fetch historical daily OHLCV (oldest->newest) and index open/close and earnings date when available.

    Returns a tuple: (historical_30d, index_open, index_close, earnings_date)
    - historical_30d is a dict with keys: dates, open, high, low, close, volume (lists oldest->newest)
    - index_open/index_close are floats or None
    - earnings_date is a string 'YYYY-MM-DD' or None
    """
    try:
        from config import REGION
    except Exception:
        REGION = 'US'

    if REGION == 'IN':
        index_symbol = '^NSEI'
    else:
        index_symbol = '^GSPC'

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{STOCK_NAME}"
    params = {"interval": "1d", "range": "60d"}
    headers = HEADERS
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        res = data.get('chart', {}).get('result')
        rows = []
        if res:
            r0 = res[0]
            timestamps = r0.get('timestamp', [])
            quote = r0.get('indicators', {}).get('quote', [])
            opens = quote[0].get('open', []) if quote else []
            highs = quote[0].get('high', []) if quote else []
            lows = quote[0].get('low', []) if quote else []
            closes = quote[0].get('close', []) if quote else []
            vols = quote[0].get('volume', []) if quote else []
            tz = pytz.timezone(EXCHANGE_TIMEZONE)
            from datetime import datetime as _dt
            for ts, o, h, l, c, v in zip(timestamps, opens, highs, lows, closes, vols):
                if c is None:
                    continue
                dt_utc = _dt.utcfromtimestamp(ts).replace(tzinfo=pytz.utc)
                dt_local = dt_utc.astimezone(tz)
                rows.append({'date': dt_local.strftime('%Y-%m-%d'), 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v})

        # Ensure chronological order oldest->newest
        historical = rows

        # Build historical_30d structure (use up to last 30 trading rows)
        last_30 = historical[-30:] if historical else []
        dates = [r['date'] for r in last_30]
        opens = [float(r['open']) for r in last_30]
        highs = [float(r['high']) for r in last_30]
        lows = [float(r['low']) for r in last_30]
        closes = [float(r['close']) for r in last_30]
        volumes = [int(r['volume']) if r.get('volume') is not None else 0 for r in last_30]

        historical_30d = {
            'dates': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
        }

        # Fetch index open/close for most recent session
        index_open = None
        index_close = None
        try:
            idx_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{index_symbol}"
            idx_resp = requests.get(idx_url, params={"interval": "1d", "range": "5d"}, headers=headers, timeout=10)
            idx_resp.raise_for_status()
            idx_data = idx_resp.json()
            idx_res = idx_data.get('chart', {}).get('result')
            if idx_res:
                r0 = idx_res[0]
                idx_quote = r0.get('indicators', {}).get('quote', [])
                if idx_quote:
                    idx_opens = idx_quote[0].get('open', [])
                    idx_closes = idx_quote[0].get('close', [])
                    # take most recent non-None
                    for o in reversed(idx_opens):
                        if o is not None:
                            index_open = float(o)
                            break
                    for c in reversed(idx_closes):
                        if c is not None:
                            index_close = float(c)
                            break
        except Exception:
            index_open = None
            index_close = None

        # Attempt to fetch earnings date via yfinance if available
        earnings_date = None
        try:
            import yfinance as yf
            from dateutil.parser import parse as _parse_date
            ticker = yf.Ticker(STOCK_NAME.split('.')[0])
            cal = ticker.calendar
            if hasattr(cal, 'empty') and not cal.empty:
                try:
                    vals = cal.iloc[:,0].dropna()
                    if not vals.empty:
                        ed = vals.iloc[0]
                        earnings_date = _parse_date(str(ed)).strftime('%Y-%m-%d')
                except Exception:
                    earnings_date = None
        except Exception:
            earnings_date = None

        return historical_30d, index_open, index_close, earnings_date
    except Exception:
        return {
            'dates': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []
        }, None, None, None


def fetch_historical_extended(min_trading_days=90, benchmark_days=90):
    """Fetch extended historical daily OHLCV and benchmark closes.

    Returns tuple:
      (historical_Nd, benchmark_closes, sector_closes, earnings_date)

    Each series is oldest->newest. On failure or insufficient depth, returns empty lists.
    """
    try:
        from config import REGION
    except Exception:
        REGION = 'US'

    if REGION == 'IN':
        index_symbol = '^NSEI'
    else:
        index_symbol = '^GSPC'

    # Try to fetch a larger calendar range to capture >= min_trading_days
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{STOCK_NAME}"
    params = {"interval": "1d", "range": "360d"}
    headers = HEADERS
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        res = data.get('chart', {}).get('result')
        rows = []
        if res:
            r0 = res[0]
            timestamps = r0.get('timestamp', [])
            quote = r0.get('indicators', {}).get('quote', [])
            opens = quote[0].get('open', []) if quote else []
            highs = quote[0].get('high', []) if quote else []
            lows = quote[0].get('low', []) if quote else []
            closes = quote[0].get('close', []) if quote else []
            vols = quote[0].get('volume', []) if quote else []
            tz = pytz.timezone(EXCHANGE_TIMEZONE)
            from datetime import datetime as _dt
            for ts, o, h, l, c, v in zip(timestamps, opens, highs, lows, closes, vols):
                if c is None:
                    continue
                dt_utc = _dt.utcfromtimestamp(ts).replace(tzinfo=pytz.utc)
                dt_local = dt_utc.astimezone(tz)
                rows.append({'date': dt_local.strftime('%Y-%m-%d'), 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v})

        # Keep chronological order oldest->newest
        historical = rows
        # Build lists
        closes = [float(r['close']) for r in historical]
        opens = [float(r['open']) for r in historical]
        highs = [float(r['high']) for r in historical]
        lows = [float(r['low']) for r in historical]
        volumes = [int(r['volume']) if r.get('volume') is not None else 0 for r in historical]
        dates = [r['date'] for r in historical]

        historical_full = {
            'dates': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
        }

        # Fetch benchmark closes (index_symbol) for the recent period
        benchmark_closes = []
        try:
            idx_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{index_symbol}"
            idx_resp = requests.get(idx_url, params={"interval": "1d", "range": "120d"}, headers=headers, timeout=10)
            idx_resp.raise_for_status()
            idx_data = idx_resp.json()
            idx_res = idx_data.get('chart', {}).get('result')
            idx_rows = []
            if idx_res:
                r0 = idx_res[0]
                timestamps = r0.get('timestamp', [])
                quote = r0.get('indicators', {}).get('quote', [])
                closes_list = quote[0].get('close', []) if quote else []
                tz = pytz.timezone(EXCHANGE_TIMEZONE)
                from datetime import datetime as _dt
                for ts, c in zip(timestamps, closes_list):
                    if c is None:
                        continue
                    dt_utc = _dt.utcfromtimestamp(ts).replace(tzinfo=pytz.utc)
                    dt_local = dt_utc.astimezone(tz)
                    idx_rows.append({'date': dt_local.strftime('%Y-%m-%d'), 'close': float(c)})
                benchmark_closes = [r['close'] for r in idx_rows]
        except Exception:
            benchmark_closes = []

        # Sector benchmark not available: use same as benchmark_closes
        sector_closes = benchmark_closes.copy() if benchmark_closes else []

        # Attempt to fetch earnings date via yfinance if available (best-effort)
        earnings_date = None
        try:
            import yfinance as yf
            from dateutil.parser import parse as _parse_date
            ticker = yf.Ticker(STOCK_NAME.split('.')[0])
            cal = ticker.calendar
            if hasattr(cal, 'empty') and not cal.empty:
                try:
                    vals = cal.iloc[:,0].dropna()
                    if not vals.empty:
                        ed = vals.iloc[0]
                        earnings_date = _parse_date(str(ed)).strftime('%Y-%m-%d')
                except Exception:
                    earnings_date = None
        except Exception:
            earnings_date = None

        return historical_full, benchmark_closes, sector_closes, earnings_date
    except Exception:
        return {'dates': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}, [], [], None
