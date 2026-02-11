# main.py
import logging
import sys

from config import validate_config, LOG_FILE_PATH
from utils.price_loader import load_price_data
from utils.chart_generator import generate_price_chart
from utils.news_loader import load_news
from utils.summary_generator import generate_summary
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
    # generate chart (report_builder will regenerate if missing; this ensures file exists)
    generate_price_chart(price)
    news = load_news()
    summary = generate_summary(price, news)
    build_pdf_report(price, news, summary)
    return 0

if __name__ == "__main__":
    sys.exit(main())
