# main.py
import logging
import sys

from config import validate_config, LOG_FILE_PATH
from utils.price_loader import load_price_data, fetch_historical_extended
from utils.chart_generator import generate_price_chart
from utils.news_loader import load_news
from utils.summary_generator import generate_summary, compute_extended_metrics
from report_builder import build_pdf_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)

def main():
    validate_config()
    price = load_price_data()
    # Fetch historical data and compute extended reference-only metrics for rendering
    extended_metrics = None
    try:
        historical_full, benchmark_closes, sector_closes, earnings_date = fetch_historical_extended()
        # pass both the smaller historical_30d (for backward compatibility) and the full series
        # compute_extended_metrics will prefer historical_full when available
        extended_metrics = compute_extended_metrics(
            historical_30d={},
            index_open=None,
            index_close=None,
            earnings_date=earnings_date,
            historical_full=historical_full,
            benchmark_closes=benchmark_closes,
            sector_closes=sector_closes,
        )
    except Exception:
        # If fetch or compute fails, continue without extended metrics
        extended_metrics = None
    # generate chart (report_builder will regenerate if missing; this ensures file exists)
    generate_price_chart(price)
    news = load_news()
    summary = generate_summary(price, news)
    build_pdf_report(price, news, summary, extended_metrics=extended_metrics)
    return 0

if __name__ == "__main__":
    sys.exit(main())
