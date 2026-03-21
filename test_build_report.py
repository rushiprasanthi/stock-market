from report_builder import build_pdf_report
from utils.price_loader import fetch_historical_30d
from utils.summary_generator import compute_extended_metrics

# Dummy data for smoke test
price = {
    "open": 150.00,
    "last": 152.35,
    "high": 153.00,
    "low": 149.50,
    "high_time": "10:45",
    "low_time": "09:35",
}

news = {
    "stock": [
        {"headline": "Apple announces dividend", "source": "Reuters", "link": "https://example.com/article1", "publish_time": "2026-02-11 08:00"},
    ],
    "geopolitical": [
        {"headline": "Trade talks continue", "source": "Reuters", "link": "https://example.com/article2", "publish_time": "2026-02-11 06:00"},
    ],
    "market": [
        {"headline": "Fed indicates rate pause", "source": "Bloomberg", "link": "https://example.com/article3", "publish_time": "2026-02-10 16:00"},
    ],
}

summary = [
    "Strong daily close above open suggests bullish intraday sentiment.",
    "Watch support at 149.50; resistance near 153.00.",
]

if __name__ == '__main__':
    extended_metrics = None
    try:
        historical_30d, index_open, index_close, earnings_date = fetch_historical_30d()
        extended_metrics = compute_extended_metrics(historical_30d, index_open, index_close, earnings_date)
    except Exception:
        # Keep extended_metrics as None if any data fetch/compute fails
        extended_metrics = None

    build_pdf_report(price, news, summary, extended_metrics=extended_metrics)
    print('PDF build attempted - check reports/daily_stock_report.pdf')
