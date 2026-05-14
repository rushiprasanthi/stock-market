
Project overview
----------------
Stock Market Daily Report is an automated, lightweight engineering system that generates a human-ready daily PDF report for a single equity symbol. The system:

- Fetches live intraday price (OHLCV) for the configured equity.
- Pulls historical series (30d and extended up to ~360d) for analytics.
- Aggregates recent news from multiple RSS feeds (stock-specific, market, geopolitical).
- Computes a suite of derived metrics and regime signals (volatility, drawdown, relative performance, volume regimes, beta).
- Generates a compact visualization (wide PNG) and assembles a professional PDF report.

Real-world problem it solves
- Provides concise, reproducible daily briefing materials for an investor, analyst or PM who needs one-page context and quantitative signals on a given stock without manually collecting data.
- Useful for watchlists, pre-market or post-market recaps, automated reporting pipelines or as an input to trading/decision workflows.

Why this project matters (engineering goals)
- Automate data collection and narrative synthesis so human analysts get decision-ready insight with reproducible code.
- Make metrics auditable and deterministic (explicit data sources and computed metrics).
- Keep the codebase modular so components (price ingestion, news ingestion, charting, metrics, report generation) can be scaled or replaced independently.

Core features
-------------
- Single-command run that builds a complete PDF report (price, chart, bullets, extended metrics).
- Live intraday price ingestion from Yahoo Finance (public v8 chart API).
- Historical data ingestion for 30-day and extended series (up to ~360d) to compute regimes and more advanced signals.
- RSS-based news aggregation with parallel fetchers, deduplication and time-window filtering.
- Chart generation: single-day compact price + volume visualization saved as a PNG (Matplotlib).
- Summary generation: human-readable bullets derived from price state and news presence.
- Extended metrics computation: 20/30/90-day averages, z-scores, volatility and beta computations, drawdown and days-until-earnings (best-effort via yfinance).
- Config-driven: symbol, exchange-region, lookback settings, file paths and chart/pdf styling are centrally defined.

System architecture (deep dive)
-------------------------------
High-level layered architecture:
- Input layer
  - External data sources: Yahoo Finance chart API, RSS feeds.
  - Optional: yfinance for calendar/earnings (best-effort).
- Ingestion & normalization
  - Price ingestion: fetch latest day and optionally extended historical series. Normalize timestamps to exchange timezone.
  - News ingestion: concurrent RSS fetches with recency cutoff and de-duplication.
- Processing / analytics
  - Summary generator: deterministic bullet creation from price & news.
  - Extended metrics engine: computes rolling volatilities, z-scores, relative performance, volume ratios, beta, drawdowns.
- Presentation / persistence
  - Chart generator: renders a compact PNG to represent price + volume.
  - Report builder: assembles chart, bullets, metadata and extended metrics into a PDF artifact.
- File system
  - All artifacts (raw data, processed CSVs, charts, reports, logs) stored under the repository-managed data and artifact directories.

Request / data lifecycle (single run)
1. main.py validates config and ensures required directories exist.
2. load_price_data() -> hits Yahoo API to obtain intraday OHLCV for the configured symbol (1d interval). Returns a small dict that captures open/high/low/last/volume/as_of, and a market state (OPEN/CLOSED).
3. fetch_historical_extended() -> attempts to fetch extended historical daily OHLCV series (up to several hundred days) and benchmark closes for index/sector when available. Also attempts to obtain earnings date via yfinance (optional).
4. compute_extended_metrics() -> transforms historical data into a rich metrics dict (rolling vol, relative returns, beta, drawdowns, volume regime signals).
5. generate_price_chart() -> renders a compact two-tier chart (price vertical-line + open-close bar; volume bar beneath). Exports PNG to CHART_OUTPUT_PATH.
6. load_news() -> concurrently fetches and parses configured RSS feeds, filters by recency and deduplicates.
7. generate_summary() -> composes human-readable bullet points for the report body.
8. build_pdf_report() -> (report_builder.py) composes PDF using chart + summary + extended metrics + metadata and writes PDF_OUTPUT_PATH.

Processing pipeline / component interactions
- main.py orchestrates the flow and handles graceful degradation (continued execution even if extended metrics or news fail).
- Modules are designed to be pure in behavior: ingest -> normalize -> return plain data structures (dicts/lists) for downstream modules.
- Components use standard concurrent patterns:
  - news_loader uses ThreadPoolExecutor to keep RSS collection parallel.
  - I/O operations are bounded by short timeouts and fallback paths (e.g., feedparser fallback when requests fetch fails).

Technical stack & rationale
--------------------------
Languages & core runtime
- Python 3.8+ — good balance of ecosystem maturity, data-processing libraries and readability.

Primary libraries (observed via imports)
- requests — reliable HTTP client used for Yahoo + RSS fetch fallbacks.
- feedparser — robust RSS parsing and normalization.
- pytz — timezone conversions to present local exchange times correctly.
- matplotlib (Agg) — server-friendly chart rendering to PNG.
- concurrent.futures — for parallel RSS fetches (standard lib).
- yfinance (optional) — used best-effort to obtain earnings calendar; absence of yfinance is handled.
- dateutil — for flexible date parsing in metrics (if available).
- statistics — standard library for mean/stdev etc.
- logging — centralized logging to file and stdout.

Why these choices
- requests + feedparser provide robust external ingestion while keeping dependencies minimal.
- Matplotlib (Agg backend) allows headless image generation suitable for server or cron runs.
- Use of standard library concurrency (ThreadPoolExecutor) is simple, effective for I/O-bound tasks and avoids additional complexity (no Celery/async required for small-scale daily runs).
- Keeping file-based outputs (charts/reports) makes the system straightforward to run in local CI, cron or small cloud instances.

Project tree (inferred)
-----------------------
A professional project tree (generated from repository contents and inferred structure):

.
├── .gitignore
├── README.md                # (this file you are reading)
├── config.py                # central configuration and path helpers
├── main.py                  # orchestrator / CLI entrypoint
├── report_builder.py        # (report composition & PDF export)
├── requirements.txt
├── charts/                  # generated charts (PNG)
├── data/
│   ├── raw/                 # raw JSONs from suppliers
│   └── processed/           # derived CSV / curated time-series
├── logs/                    # runtime logs
├── reports/                 # generated PDF reports
├── utils/
│   ├── price_loader.py      # price & historical ingestion
│   ├── news_loader.py       # RSS fetching, parallelization, dedup
│   ├── chart_generator.py   # PNG generation (matplotlib)
│   └── summary_generator.py # summary bullets and metrics engine
├── news/
│   └── rss_feeds.py         # (static list of well-known RSS feeds)
├── images/                  # static images for report templates (logo etc.)
├── tests/ or test_build_report.py  # unit/integration test scripts
└── other doc files/notes    # design notes, prompt files, problem lists

Notes:
- config.py centralizes all environment-like settings (symbol, timezone, lookback, file paths). It's the main tuning point to run the system for another symbol or region.
- report_builder.py is the report composition layer that finally writes the PDF and likely pulls in the PNGs and text blocks.

Module / API documentation
--------------------------
This section documents the important modules and their key functions (function signatures and responsibilities are inferred from the codebase):

1) main.py
- Purpose: orchestrates a single end-to-end run. Validates config, obtains price & historical, computes metrics, produces chart, aggregates news, generates summary and writes the PDF.
- Entry: python main.py
- Behavior: tolerant to partial failures. If extended metrics fail, proceeds to generate report without them.

2) utils/price_loader.py
- Exports:
  - load_price_data() -> dict
    - Fetches Yahoo Finance v8 chart for configured STOCK_NAME with params interval=1d&range=1d.
    - Normalizes times to exchange timezone and returns OHLCV-ish dict:
      { open, high, low, last, volume, high_time, low_time, as_of_time, market_state }
  - fetch_historical_30d(min_days=30) -> (historical_30d, index_open, index_close, earnings_date)
    - Fetches up to ~60d, returns structured historical dict expected by metrics engine.
  - fetch_historical_extended(min_trading_days=90, benchmark_days=90) -> (historical_full, benchmark_closes, sector_closes, earnings_date)
    - Attempts a larger fetch (~360d) and collects benchmark close series for relative computations.
- Observations: requests + JSON-unwrapping of Yahoo chart structure; timestamps are converted to local exchange times via pytz.

3) utils/news_loader.py
- Exports:
  - load_news() -> dict
    - Uses NewsLoader.run() to fetch RSS feeds grouped into categories: stock, geopolitical, market.
    - Parallel fetch via ThreadPoolExecutor; applies a recency cutoff (NEWS_LOOKBACK_HOURS) and deduplication; limits results per category (MAX_NEWS_PER_CATEGORY).
    - Each item returned as: {headline, source, publish_time, link}

4) utils/chart_generator.py
- Exports:
  - generate_price_chart(ohlc_summary, output_path=..., width_inches=None) -> output_path
    - Generates a compact two-row figure: price (vline + open/close bar) and volume (M scaled) using Matplotlib Agg. Saves PNG.

5) utils/summary_generator.py
- Exports:
  - generate_summary(price, news) -> list[str]
    - Produces concise bullet points describing the day's price action and whether substantive news was published.
  - compute_extended_metrics(historical_30d, index_open=None, index_close=None, earnings_date=None, historical_full=None, benchmark_closes=None, sector_closes=None) -> dict
    - Computes a comprehensive set of metrics: avg volumes, percent deviations, 5-day std/avg-change, daily-return z-score, vol_30/vol_90/ratio, avg volume windows, 30-day returns and relative diffs, 30-day drawdown and rolling peak, beta_30d.
    - Designed to prefer historical_full when present and degrade gracefully to 30d data.

6) report_builder.py
- Purpose (observed from imports): build_pdf_report(price, news, summary, extended_metrics=None)
  - Assembles charts and text into a professional PDF and writes to configured PDF_OUTPUT_PATH.
  - The report builder is the single place to change PDF layout, fonts, and export options.

Execution pipeline (step-by-step)
--------------------------------
1. Validate and ensure directories:
   - config.validate_config() and ensure_directories() create data, charts, reports and logs directories.

2. Fetch live price:
   - load_price_data() returns today's OHLCV snapshot and market state.

3. Fetch extended historical (best-effort):
   - fetch_historical_extended() — returns full series and benchmark closes; used to compute advanced metrics.

4. Compute analytics:
   - compute_extended_metrics() calculates regime signals and diagnostic statistics.

5. Charting:
   - generate_price_chart() produces a compact PNG for the report.

6. News:
   - load_news() collects and filters RSS items in parallel.

7. Summary / narrative:
   - generate_summary() builds bullets.

8. Report construction:
   - build_pdf_report() packages narrative, metrics, and chart into a PDF.

Installation guide
------------------
Prerequisites
- Python 3.8+ (3.9 / 3.10 recommended)
- A system with network access to reach Yahoo Finance and configured RSS endpoints.

Recommended quickstart (POSIX / macOS / WSL)
```bash
# clone the repo
git clone https://github.com/rushiprasanthi/stock-market.git
cd stock-market

# create virtualenv
python -m venv .venv
# activate
source .venv/bin/activate

# install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

Notes:
- requirements.txt exists in the repo. The code tolerates missing optional packages (yfinance is used in a try/except — the system will still run without it but earnings-date features will be disabled).
- If you plan to generate PDFs, confirm the report builder dependencies are installed (reportlab, fpdf, wkhtmltopdf, or similar) depending on the implementation used in report_builder.py. The requirements.txt and report_builder.py define exact requirements.

Configuration
- Most settings are centralized in config.py. Important knobs:
  - STOCK_NAME: e.g. "RELIANCE.NS" or "AAPL"
  - USE_TODAY_DATE / MANUAL_DATE
  - REGION, EXCHANGE_TIMEZONE auto-detects by ticker suffix (.NS/.BO -> Asia/Kolkata)
  - RSS_FEEDS: dynamic (stock-specific) + static list in news/rss_feeds.py
  - Paths: DATA_RAW_DIR, DATA_PROCESSED_DIR, CHARTS_DIR, REPORTS_DIR, LOGS_DIR

Tips:
- To change the symbol, update STOCK_NAME in config.py.
- For automation (cron or scheduler), set USE_TODAY_DATE=True for timestamped output using today’s date.

Running the project
-------------------
Development run (local)
```bash
# from repository root, with virtualenv active
python main.py
```

This will:
- ensure directories exist,
- fetch price and news,
- generate a chart at charts/price_chart.png,
- write PDF to reports/daily_stock_report.pdf,
- write logs to logs/report_builder.log.

Production / scheduled run (example using cron)
- Create a small wrapper or use systemd timer to call:
```bash
/path/to/.venv/bin/python /path/to/stock-market/main.py >> /path/to/stock-market/logs/cron_run.log 2>&1
```
- For cloud scheduling, you can create a short-running container image and run it as a scheduled job (see Future Improvements for Docker/K8s guidance).

Sample outputs (representative)
- load_price_data() returns:
```json
{
  "open": 2800.00,
  "high": 2850.50,
  "low": 2790.00,
  "last": 2835.25,
  "volume": 12345678,
  "high_time": "11:45",
  "low_time": "09:35",
  "as_of_time": "20 Jan 2026, 15:30 IST",
  "market_state": "CLOSED"
}
```
- generate_summary(...) returns bullets like:
  - "The stock opened at 2800.00 and closed at 2835.25."
  - "The day's high was 2850.50 and the low was 2790.00."
  - "Stock-specific, geopolitical, and market-related news were published."

Scalability & engineering considerations
---------------------------------------
The repository is intentionally modular to allow incremental scaling. Below are design patterns and suggested upgrades.

Current strengths
- Modular separation of ingestion (price/news), analytics, charting and report generation.
- Parallel RSS ingestion reduces latency and is appropriate for I/O-bound tasks.
- Resilient behavior: many sections are wrapped in try/except to ensure the pipeline produces a report even when optional sources fail.

Performance & scaling suggestions
- Short-term horizontal scale: run many independent instances (one symbol per run) in parallel using container workers (Docker).
- Concurrency model: for larger feed sets or multiple symbols, replace ThreadPoolExecutor with an asynchronous HTTP client (httpx + asyncio) for better throughput on high numbers of I/O requests.
- Data caching: add a local Redis or file-based cache (TTL) for historical data to minimize repeated Yahoo API queries within configured windows.
- Queue & orchestration: adopt a job queue (Celery/RabbitMQ or Redis Queue) to schedule symbol-report jobs, decouple ingestion and PDF generation, and improve retry semantics.
- Observability: integrate structured logging (JSON), and push metrics (Prometheus) for runtime instrumentation (latencies, success/failure rates, API error counts).
- Fault tolerance:
  - Retries with exponential backoff for HTTP calls (requests + urllib3 Retry or Tenacity).
  - Circuit-breaker patterns for flaky external endpoints.
- Storage & archival:
  - Push reports to object storage (S3-compatible) for long-term retention.
  - Persist raw JSON responses in a retention-safe data lake for auditing and backtesting.

Data & DB considerations
- For single-symbol daily reports, file-based artifacts are sufficient.
- For multi-symbol or historical-analysis scale, introduce a time-series optimized store (InfluxDB, TimescaleDB) or columnar store (Parquet files on S3) to support fast retrospective computations.

Engineering improvements for advanced production readiness
- Use a job scheduler (Airflow or Dagster) to orchestrate daily ingestion, analytics and report-building DAGs with clear dependency tracking and retries.
- Containerize with an immutable artifact (Docker image containing Python runtime and the app), run as CronJob (Kubernetes) or scheduled Lambda / Cloud Run job.
- Add a cache layer (Redis) and persistent storage (Postgres / S3) for raw & processed data and artifacts.

Challenges & engineering decisions
---------------------------------
Key tradeoffs observed in the codebase:
- Public data APIs vs. vendor APIs:
  - Using Yahoo Finance v8 endpoints and RSS feeds is cost-free and quick to integrate, but not SLAs-guaranteed. The code handles this by falling back gracefully and making features optional (e.g., earnings via yfinance).
- Simplicity vs. scale:
  - The current synchronous orchestration and file-based artifact model favors simplicity and visibility (easy to run locally). For heavy scale (many symbols or intraday), a message-queue and async/event-driven architecture would be preferable.
- Statistical reliability:
  - Metrics are computed from raw daily series; the code avoids overfitting by using simple statistics (mean/std/stdev) and explicit checks for sufficient data (n>=2 or n>=31) to prevent spurious results.
- Parallelism model:
  - ThreadPoolExecutor is chosen for RSS ingestion because news fetching is I/O-bound. This keeps the runtime and dependency surface small.

Known limitations
- No authentication or rate-limited handling for data providers; if scaled, API keys or rate-aware logic will be required.
- report_builder implementation details and PDF styling are centralized in a single module; changing PDF engine may require changes throughout.
- Tests: there is a test script (test_build_report.py) but a full unit/integration test suite and CI pipeline are not present.

Future improvements (roadmap)
----------------------------
Short-term
- Add Dockerfile and example docker-compose for local reproducible runs.
- Add a small schedule wrapper (systemd timer / cron.example) for sample deployment.
- Provide example environment override via .env and a small config loader to avoid editing config.py directly.

Medium-term
- Containerize and publish an image; add a GitHub Actions workflow to build and push images on release.
- Add robust retry & backoff for HTTP calls (Tenacity).
- Implement caching of historical responses (local file or Redis) with a TTL.
- Add more formal unit tests and CI pipeline that runs linting, tests and static analysis.

Long-term / advanced
- Migrate to an orchestrator (Airflow/Dagster) and store time-series data in a time-series DB.
- Add an authenticated API layer that can serve generated reports over HTTPS (Flask/FastAPI).
- Add real-time streaming (Kafka) for high-frequency updates and downstream consumers.
- Integrate ML/AI:
  - Trend classification models trained on historical features.
  - NLP summarization for news (fine-tuned transformer to generate qualitative commentary).
  - Anomaly detection models for volume or price spikes.

Professional README sections
---------------------------
Architecture diagram (ASCII)
```
+------------------+     +-------------------+     +------------------+
|  Yahoo Finance   |     |  RSS Providers    |     |  Optional yfinance|
|  (price API)     |     |  (feedparser)     |     |  (earnings)      |
+--------+---------+     +---------+---------+     +--------+---------+
         |                         |                        |
         v                         v                        v
  utils/price_loader.py       utils/news_loader.py      utils/price_loader.py
         |                         |                       |
         +-----------+-------------+-----------------------+
                     |
                     v
                main.py (orchestrator)
                     |
       +-------------+------------+
       |                          |
       v                          v
 utils/summary_generator.py   utils/chart_generator.py
       |                          |
       +-------------+------------+
                     |
                     v
             report_builder.py -> reports/daily_stock_report.pdf
                     |
                     v
                  logs/report_builder.log
```

Contribution
------------
- Fork the repository, create a feature branch and open a PR.
- Include unit tests for new analytic behavior (especially around compute_extended_metrics).
- Keep changes modular: prefer adding new functions in utils/ rather than changing monolithic files.
- Document new dependencies in requirements.txt and update README with any changes to runtime or optional features.

License
-------
This repository includes a License file (MIT-style expected). If you intend to reuse or publish, include an explicit LICENSE file in the repo. (If no license present, it defaults to “all rights reserved” — make the license explicit before public redistribution.)

Author
------
Rushiprasanthi — GitHub: @rushiprasanthi
- Project maintained as a personal portfolio / engineering showcase.
- For questions or contribution proposals, open an issue on GitHub.

