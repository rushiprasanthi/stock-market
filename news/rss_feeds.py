# news/rss_feeds.py

RSS_FEEDS = {

    # =====================================================
    # STOCK-SPECIFIC (company-level impact)
    # =====================================================
    "stock": [
        # Yahoo Finance – company specific
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL&region=US&lang=en-US",

        # Reuters – company news (high trust)
        "https://feeds.reuters.com/reuters/companyNews",

        # Nasdaq press releases
        "https://www.nasdaq.com/feed/rssoutbound?symbol=AAPL",
    ],

    # =====================================================
    # GEOPOLITICAL (market-moving global events)
    # =====================================================
    "geopolitical": [
        # Reuters – World & Politics
        "https://feeds.reuters.com/Reuters/worldNews",
        "https://feeds.reuters.com/Reuters/politicsNews",

        # BBC – Global events
        "http://feeds.bbci.co.uk/news/world/rss.xml",

        # Associated Press – World
        "https://apnews.com/apf-worldnews",
    ],

    # =====================================================
    # MARKET / MACRO (rates, inflation, economy, energy)
    # =====================================================
    "market": [
        # Reuters – Markets & Business
        "https://feeds.reuters.com/reuters/marketsNews",
        "https://feeds.reuters.com/reuters/businessNews",

        # CNBC – Markets
        "https://www.cnbc.com/id/15839069/device/rss/rss.html",

        # Financial Times – Markets
        "https://www.ft.com/markets?format=rss",

        # MarketWatch – Top market stories
        "https://feeds.marketwatch.com/marketwatch/topstories/",
    ],
}

