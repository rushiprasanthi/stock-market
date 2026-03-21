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


def compute_extended_metrics(historical_30d, index_open=None, index_close=None, earnings_date=None, historical_full=None, benchmark_closes=None, sector_closes=None):
    """Compute derived metrics from historical_30d and index/earnings info.

    Returns extended_metrics dict per spec.
    """
    from statistics import mean, stdev
    from datetime import datetime, date

    ext = {
        "avg_volume_20": None,
        "volume_deviation_pct": None,
        "range_percentile_30": None,
        "stock_pct": None,
        "index_pct": None,
        "relative_diff": None,
        "std_dev_5": None,
        "avg_change_5": None,
        "earnings_date": None,
        "days_until_earnings": None,
        # Advanced Comparative Metrics (to be computed if sufficient data provided)
        "daily_return_zscore": None,
        "vol_30": None,
        "vol_90": None,
        "vol_ratio": None,
        "avg_volume_30": None,
        "avg_volume_90": None,
        "volume_ratio": None,
        "stock_return_30d": None,
        "sector_return_30d": None,
        "relative_diff_30d": None,
        "drawdown_30d": None,
        "rolling_peak_30d": None,
        "beta_30d": None,
    }

    dates = historical_30d.get('dates', [])
    opens = historical_30d.get('open', [])
    highs = historical_30d.get('high', [])
    lows = historical_30d.get('low', [])
    closes = historical_30d.get('close', [])
    volumes = historical_30d.get('volume', [])

    # avg_volume_20
    try:
        last_20_vols = [float(v) for v in volumes[-20:]] if volumes else []
        if last_20_vols:
            ext['avg_volume_20'] = float(mean(last_20_vols))
    except Exception:
        ext['avg_volume_20'] = None

    # today_volume
    try:
        today_volume = float(volumes[-1]) if volumes else None
    except Exception:
        today_volume = None

    # volume_deviation_pct
    try:
        if ext['avg_volume_20'] and ext['avg_volume_20'] != 0 and today_volume is not None:
            ext['volume_deviation_pct'] = ((today_volume - ext['avg_volume_20']) / ext['avg_volume_20']) * 100
    except Exception:
        ext['volume_deviation_pct'] = None

    # daily_range_30d and today_range
    try:
        last_30_ranges = []
        for h, l in zip(highs[-30:], lows[-30:]):
            last_30_ranges.append(float(h) - float(l))
        today_range = float(highs[-1]) - float(lows[-1]) if highs and lows else None
        if last_30_ranges and today_range is not None:
            less_count = sum(1 for v in last_30_ranges if v < today_range)
            ext['range_percentile_30'] = (less_count / len(last_30_ranges)) * 100
    except Exception:
        ext['range_percentile_30'] = None

    # Index relative performance
    try:
        if closes and opens:
            last_open = float(opens[-1])
            last_close = float(closes[-1])
            if last_open != 0:
                ext['stock_pct'] = ((last_close - last_open) / last_open) * 100
        if index_open is not None and index_close is not None and index_open != 0:
            ext['index_pct'] = ((float(index_close) - float(index_open)) / float(index_open)) * 100
        if ext.get('stock_pct') is not None and ext.get('index_pct') is not None:
            ext['relative_diff'] = ext['stock_pct'] - ext['index_pct']
    except Exception:
        ext['stock_pct'] = ext.get('stock_pct') or None
        ext['index_pct'] = ext.get('index_pct') or None
        ext['relative_diff'] = ext.get('relative_diff') or None

    # 5-day statistical summary
    try:
        last_5_closes = [float(c) for c in closes[-5:]] if closes else []
        if len(last_5_closes) >= 2:
            try:
                ext['std_dev_5'] = float(stdev(last_5_closes))
            except Exception:
                from statistics import pvariance
                ext['std_dev_5'] = float(pvariance(last_5_closes) ** 0.5)
        if len(last_5_closes) >= 2:
            changes = []
            for i in range(1, len(last_5_closes)):
                changes.append(last_5_closes[i] - last_5_closes[i-1])
            if changes:
                ext['avg_change_5'] = float(mean(changes))
    except Exception:
        ext['std_dev_5'] = None
        ext['avg_change_5'] = None

    # Earnings proximity
    try:
        if earnings_date:
            if isinstance(earnings_date, str):
                ed = datetime.strptime(earnings_date, '%Y-%m-%d').date()
            elif isinstance(earnings_date, datetime):
                ed = earnings_date.date()
            elif isinstance(earnings_date, date):
                ed = earnings_date
            else:
                ed = None
            ext['earnings_date'] = ed.strftime('%Y-%m-%d') if ed else None
            if ed:
                today = datetime.now().date()
                ext['days_until_earnings'] = (ed - today).days
        else:
            ext['earnings_date'] = None
            ext['days_until_earnings'] = None
    except Exception:
        ext['earnings_date'] = None
        ext['days_until_earnings'] = None

    # Advanced Comparative Metrics — compute when extended historical or full data provided
    try:
        # prefer historical_full if supplied, otherwise fall back to historical_30d
        src = historical_full if historical_full and isinstance(historical_full, dict) and historical_full.get('close') else historical_30d
        src_closes = src.get('close', [])
        src_opens = src.get('open', [])
        src_vols = src.get('volume', [])

        # Need at least 90 trading days for full advanced metrics where specified
        n_closes = len(src_closes)

        # 1) Daily Return Z-Score (30-Day)
        try:
            if n_closes >= 31 and len(src_opens) >= n_closes:
                # most recent day indices
                daily_return = (float(src_closes[-1]) - float(src_opens[-1])) / float(src_opens[-1])
                # previous 30 trading days (exclude most recent)
                prev_30 = []
                # collect (close-open)/open for previous 30 days
                for i in range(max(0, n_closes - 31), n_closes - 1):
                    o = float(src_opens[i])
                    c = float(src_closes[i])
                    if o != 0:
                        prev_30.append((c - o) / o)
                if len(prev_30) >= 2:
                    mean_30 = mean(prev_30)
                    try:
                        std_30 = float(stdev(prev_30))
                    except Exception:
                        std_30 = 0.0
                    if std_30 == 0:
                        ext['daily_return_zscore'] = None
                    else:
                        ext['daily_return_zscore'] = float((daily_return - mean_30) / std_30)
                else:
                    ext['daily_return_zscore'] = None
            else:
                ext['daily_return_zscore'] = None
        except Exception:
            ext['daily_return_zscore'] = None

        # 2) Rolling Volatility Comparison (30d vs 90d)
        try:
            # compute prev 30 and prev 90 daily (close-open)/open returns
            def _collect_prev_returns(src_opens, src_closes, days, exclude_latest=True):
                n = len(src_closes)
                returns = []
                end = n - 1 if exclude_latest else n
                start = max(0, end - days)
                for i in range(start, end):
                    o = float(src_opens[i])
                    c = float(src_closes[i])
                    if o != 0:
                        returns.append((c - o) / o)
                return returns

            r30 = _collect_prev_returns(src_opens, src_closes, 30, exclude_latest=True)
            r90 = _collect_prev_returns(src_opens, src_closes, 90, exclude_latest=True)
            if r30 and len(r30) >= 2:
                try:
                    vol30 = float(stdev(r30)) * 100.0
                    ext['vol_30'] = vol30
                except Exception:
                    ext['vol_30'] = None
            else:
                ext['vol_30'] = None
            if r90 and len(r90) >= 2:
                try:
                    vol90 = float(stdev(r90)) * 100.0
                    ext['vol_90'] = vol90
                except Exception:
                    ext['vol_90'] = None
            else:
                ext['vol_90'] = None

            if ext.get('vol_30') is not None and ext.get('vol_90') is not None and ext['vol_90'] != 0:
                ext['vol_ratio'] = float(ext['vol_30'] / ext['vol_90'])
            else:
                ext['vol_ratio'] = None
        except Exception:
            ext['vol_30'] = None
            ext['vol_90'] = None
            ext['vol_ratio'] = None

        # 3) Volume Regime Shift
        try:
            if src_vols and len(src_vols) >= 30:
                last_30_vols = [float(v) for v in src_vols[-30:]]
                ext['avg_volume_30'] = float(mean(last_30_vols)) if last_30_vols else None
            else:
                ext['avg_volume_30'] = None
            if src_vols and len(src_vols) >= 90:
                last_90_vols = [float(v) for v in src_vols[-90:]]
                ext['avg_volume_90'] = float(mean(last_90_vols)) if last_90_vols else None
            else:
                ext['avg_volume_90'] = None

            if ext.get('avg_volume_30') is not None and ext.get('avg_volume_90') is not None and ext['avg_volume_90'] != 0:
                ext['volume_ratio'] = float(ext['avg_volume_30'] / ext['avg_volume_90'])
            else:
                ext['volume_ratio'] = None
        except Exception:
            ext['avg_volume_30'] = None
            ext['avg_volume_90'] = None
            ext['volume_ratio'] = None

        # 4) Relative Strength vs Sector (30-Day)
        try:
            if n_closes >= 31:
                current_close = float(src_closes[-1])
                close_30_days_ago = float(src_closes[-31])
                if close_30_days_ago != 0:
                    ext['stock_return_30d'] = ((current_close - close_30_days_ago) / close_30_days_ago) * 100.0
                else:
                    ext['stock_return_30d'] = None
            else:
                ext['stock_return_30d'] = None

            # sector benchmark
            if sector_closes and len(sector_closes) >= 31:
                bench_today = float(sector_closes[-1])
                bench_30 = float(sector_closes[-31])
                if bench_30 != 0:
                    ext['sector_return_30d'] = ((bench_today - bench_30) / bench_30) * 100.0
                else:
                    ext['sector_return_30d'] = None
            elif benchmark_closes and len(benchmark_closes) >= 31:
                bench_today = float(benchmark_closes[-1])
                bench_30 = float(benchmark_closes[-31])
                if bench_30 != 0:
                    ext['sector_return_30d'] = ((bench_today - bench_30) / bench_30) * 100.0
                else:
                    ext['sector_return_30d'] = None
            else:
                ext['sector_return_30d'] = None

            if ext.get('stock_return_30d') is not None and ext.get('sector_return_30d') is not None:
                ext['relative_diff_30d'] = float(ext['stock_return_30d'] - ext['sector_return_30d'])
            else:
                ext['relative_diff_30d'] = None
        except Exception:
            ext['stock_return_30d'] = None
            ext['sector_return_30d'] = None
            ext['relative_diff_30d'] = None

        # 5) 30-Day Drawdown
        try:
            if n_closes >= 30:
                last_30 = src_closes[-30:]
                rolling_peak = max(last_30)
                ext['rolling_peak_30d'] = float(rolling_peak)
                current_close = float(src_closes[-1])
                if rolling_peak != 0:
                    ext['drawdown_30d'] = ((current_close - rolling_peak) / rolling_peak) * 100.0
                else:
                    ext['drawdown_30d'] = None
            else:
                ext['rolling_peak_30d'] = None
                ext['drawdown_30d'] = None
        except Exception:
            ext['rolling_peak_30d'] = None
            ext['drawdown_30d'] = None

        # 6) Beta (30-Day vs Benchmark) — use close-to-close returns and require matched length
        try:
            # need at least 31 closes for both series to compute 30 returns
            if len(src_closes) >= 31 and benchmark_closes and len(benchmark_closes) >= 31:
                # take most recent 31 closes of both
                s = [float(x) for x in src_closes[-31:]]
                b = [float(x) for x in benchmark_closes[-31:]]
                # compute close-to-close returns (decimal)
                rs = []
                rb = []
                for i in range(1, len(s)):
                    prev = s[i-1]
                    cur = s[i]
                    if prev != 0:
                        rs.append((cur - prev) / prev)
                for i in range(1, len(b)):
                    prev = b[i-1]
                    cur = b[i]
                    if prev != 0:
                        rb.append((cur - prev) / prev)

                if len(rs) >= 2 and len(rb) >= 2 and len(rs) == len(rb):
                    n = len(rs)
                    mean_s = mean(rs)
                    mean_b = mean(rb)
                    cov = sum((rs[i] - mean_s) * (rb[i] - mean_b) for i in range(n)) / (n - 1)
                    var_b = sum((rb[i] - mean_b) ** 2 for i in range(n)) / (n - 1)
                    if var_b == 0:
                        ext['beta_30d'] = None
                    else:
                        ext['beta_30d'] = float(cov / var_b)
                else:
                    ext['beta_30d'] = None
            else:
                ext['beta_30d'] = None
        except Exception:
            ext['beta_30d'] = None

    except Exception:
        # if anything goes wrong in advanced metrics, keep them None
        ext['daily_return_zscore'] = None
        ext['vol_30'] = None
        ext['vol_90'] = None
        ext['vol_ratio'] = None
        ext['avg_volume_30'] = None
        ext['avg_volume_90'] = None
        ext['volume_ratio'] = None
        ext['stock_return_30d'] = None
        ext['sector_return_30d'] = None
        ext['relative_diff_30d'] = None
        ext['drawdown_30d'] = None
        ext['rolling_peak_30d'] = None
        ext['beta_30d'] = None

    return ext

