# utils/news_loader.py
import logging
from datetime import datetime, timedelta
import pytz
import feedparser
from time import mktime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import NEWS_LOOKBACK_HOURS, MAX_NEWS_PER_CATEGORY
from config import RSS_FEEDS as CONFIG_FEEDS
from news.rss_feeds import RSS_FEEDS as STATIC_FEEDS


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

    def _parse_feed(self, category, url):
        """
        Fetch and parse a single feed URL. Return (category, list_of_items).
        Each item: {headline, source, publish_time, link}
        """
        items = []
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            # try a requests fetch with a short timeout to avoid blocking
            resp = requests.get(url, headers=headers, timeout=3)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception:
            # fallback to feedparser's own fetch (no retry) with request headers
            try:
                feed = feedparser.parse(url, request_headers=headers)
            except Exception as e:
                logger.warning("Failed to fetch feed %s: %s", url, e)
                return category, items

        source_title = feed.feed.get("title", url)
        for entry in getattr(feed, "entries", []):
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            link = entry.get("link")
            title = entry.get("title", "").strip()
            if not published or not link or not title:
                continue
            if not self._is_recent(published):
                continue
            items.append({
                "headline": title,
                "source": source_title,
                "publish_time": self._format_time(published),
                "link": link,
            })

        return category, items

    def run(self):
        # Expecting RSS_FEEDS to be a dict with keys: 'stock','geopolitical','market'
        output = {"stock": [], "geopolitical": [], "market": []}

        # Merge dynamic stock feeds with static expanded geopolitical & market feeds
        merged_feeds = {
            "stock": CONFIG_FEEDS.get("stock", []),
            "geopolitical": STATIC_FEEDS.get("geopolitical", []),
            "market": STATIC_FEEDS.get("market", []),
        }

        # Collect feeds in parallel to reduce latency
        futures = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for category, feeds in merged_feeds.items():
                for url in feeds:
                    futures.append(executor.submit(self._parse_feed, category, url))

            for future in as_completed(futures):
                try:
                    category, items = future.result()
                except Exception as e:
                    logger.warning("Feed worker raised exception: %s", e)
                    continue
                key = category if category in output else "market"
                output[key].extend(items)

        # Deduplicate headlines and limit per category
        for k in output:
            seen = set()
            unique = []
            for item in output[k]:
                h = item.get("headline")
                if not h or h in seen:
                    continue
                seen.add(h)
                unique.append(item)
            output[k] = unique[:MAX_NEWS_PER_CATEGORY]

        return output


def load_news():
    return NewsLoader().run()
