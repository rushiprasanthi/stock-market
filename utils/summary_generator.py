# utils/summary_generator.py
import logging
logger = logging.getLogger(__name__)

class SummaryGenerator:
    def generate(self, price, news):
        bullets = []

        if price["market_state"] == "OPEN":
            bullets.append(
                f"The stock opened at {price['open']:.2f} and last traded at {price['last']:.2f}."
            )
        else:
            bullets.append(
                f"The stock opened at {price['open']:.2f} and closed at {price['last']:.2f}."
            )

        bullets.append(
            f"The day's high was {price['high']:.2f} and the low was {price['low']:.2f}."
        )

        if any(news.values()):
            bullets.append(
                "Stock-specific, geopolitical, and market-related news were published."
            )
        else:
            bullets.append(
                "No significant stock, geopolitical, or market-related news was published."
            )

        return bullets

def generate_summary(price, news):
    return SummaryGenerator().generate(price, news)
