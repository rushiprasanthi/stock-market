# utils/news_loader.py
import logging
from datetime import datetime, timedelta
import pytz
import feedparser
from time import mktime

from config import NEWS_LOOKBACK_HOURS, MAX_NEWS_PER_CATEGORY
from config import RSS_FEEDS


logger = logging.getLogger(__name__)

class NewsLoader:
    def __init__(self):
        self.lookback_hours = NEWS_LOOKBACK_HOURS

    def _is_recent(self, published):
        if not published:
            return False

        if hasattr(published, "tm_year"):
            dt = datetime.utcfromtimestamp(mktime(published)).replace(tzinfo=pytz.UTC)
        else:
            try:
                dt = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
            except Exception:
                return False

        cutoff = datetime.now(pytz.UTC) - timedelta(hours=self.lookback_hours)
        return dt > cutoff

    def _format_time(self, published):
        if hasattr(published, "tm_year"):
            dt = datetime.utcfromtimestamp(mktime(published))
            return dt.strftime("%d %b %Y, %H:%M")
        return "Unknown"

    def run(self):
        # Expecting RSS_FEEDS to be a dict with keys: 'stock','geopolitical','market'
        output = {"stock": [], "geopolitical": [], "market": []}

        for category, feeds in RSS_FEEDS.items():
            for url in feeds:
                try:
                    feed = feedparser.parse(url)
                except Exception as e:
                    logger.warning("Failed to parse feed %s: %s", url, e)
                    continue
                for entry in feed.entries:
                    published = entry.get("published_parsed") or entry.get("updated_parsed")
                    link = entry.get("link")
                    title = entry.get("title", "").strip()

                    if not published or not link or not title:
                        continue
                    if not self._is_recent(published):
                        continue

                    output_key = category if category in output else "market"
                    output[output_key].append({
                        "headline": title,
                        "source": feed.feed.get("title", url),
                        "publish_time": self._format_time(published),
                        "link": link,
                    })

        for k in output:
            output[k] = output[k][:MAX_NEWS_PER_CATEGORY]

        return output

def load_news():
    return NewsLoader().run()
