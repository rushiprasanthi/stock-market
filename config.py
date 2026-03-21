# config.py
import os
from datetime import datetime

# ===============================
# BASIC STOCK SETTINGS
# ===============================

STOCK_NAME = "RELIANCE.NS"
STOCK_FULL_NAME = "Reliance Industries Ltd"

USE_TODAY_DATE = True
MANUAL_DATE = "2026-01-20"

# ===============================
# TIMEZONE & REGION AUTO-DETECTION
# ===============================

if STOCK_NAME.endswith(".NS") or STOCK_NAME.endswith(".BO"):
    EXCHANGE_TIMEZONE = "Asia/Kolkata"
    REGION = "IN"
    LANGUAGE = "en-IN"
else:
    EXCHANGE_TIMEZONE = "US/Eastern"
    REGION = "US"
    LANGUAGE = "en-US"

BASE_SYMBOL = STOCK_NAME.split(".")[0]

# ===============================
# RSS NEWS FEEDS (DYNAMIC)
# ===============================

RSS_FEEDS = {

    # ---------------------------------
    # STOCK-SPECIFIC
    # ---------------------------------
    "stock": [
        # Yahoo Finance dynamic feed
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={BASE_SYMBOL}&region={REGION}&lang={LANGUAGE}",

        # Reuters company coverage
        "https://feeds.reuters.com/reuters/companyNews",

        # Indian sources (better for NSE stocks)
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.moneycontrol.com/rss/latestnews.xml",
    ],

    # ---------------------------------
    # GEOPOLITICAL
    # ---------------------------------
    "geopolitical": [
        "https://feeds.reuters.com/Reuters/worldNews",
    ],

    # ---------------------------------
    # MARKET / MACRO
    # ---------------------------------
    "market": [
        "https://feeds.reuters.com/reuters/marketsNews",
    ],
}

# ===============================
# MARKET HOURS (AUTO ADJUST)
# ===============================

if REGION == "IN":
    MARKET_OPEN_HOUR = 9
    MARKET_OPEN_MINUTE = 15
    MARKET_CLOSE_HOUR = 15
    MARKET_CLOSE_MINUTE = 30
else:
    MARKET_OPEN_HOUR = 9
    MARKET_OPEN_MINUTE = 30
    MARKET_CLOSE_HOUR = 16
    MARKET_CLOSE_MINUTE = 0

# ===============================
# PATHS
# ===============================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CHARTS_DIR = os.path.join(PROJECT_ROOT, "charts")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

PRICE_DATA_RAW_PATH = os.path.join(DATA_RAW_DIR, "price_data_raw.json")
PRICE_DATA_CSV_PATH = os.path.join(DATA_PROCESSED_DIR, "daily_prices.csv")

CHART_OUTPUT_PATH = os.path.join(CHARTS_DIR, "price_chart.png")
PDF_OUTPUT_PATH = os.path.join(REPORTS_DIR, "daily_stock_report.pdf")
LOG_FILE_PATH = os.path.join(LOGS_DIR, "report_builder.log")

# ===============================
# NEWS SETTINGS
# ===============================

NEWS_LOOKBACK_HOURS = 24
MAX_NEWS_PER_CATEGORY = 8

# ===============================
# CHART SETTINGS
# ===============================

CHART_WIDTH = 6
CHART_HEIGHT = 3.5
CHART_DPI = 150

# ===============================
# PDF FONT SIZES
# ===============================

PDF_FONT_SIZE_TITLE = 26
PDF_FONT_SIZE_META = 11
PDF_FONT_SIZE_SECTION = 14
PDF_FONT_SIZE_BODY = 10
PDF_FONT_SIZE_SMALL = 8

# ===============================
# HELPERS
# ===============================

def get_report_date():
    if USE_TODAY_DATE:
        return datetime.now().strftime("%Y-%m-%d")
    return MANUAL_DATE

def ensure_directories():
    for d in [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CHARTS_DIR,
        REPORTS_DIR,
        LOGS_DIR,
    ]:
        os.makedirs(d, exist_ok=True)

def validate_config():
    if not STOCK_NAME:
        raise ValueError("STOCK_NAME cannot be empty")
    if not EXCHANGE_TIMEZONE:
        raise ValueError("EXCHANGE_TIMEZONE must be set")
    if not USE_TODAY_DATE and not MANUAL_DATE:
        raise ValueError("MANUAL_DATE required when USE_TODAY_DATE=False")

ensure_directories()
