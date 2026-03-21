# utils/chart_generator.py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from config import CHART_OUTPUT_PATH, CHART_DPI, CHART_WIDTH, CHART_HEIGHT

def generate_price_chart(ohlc_summary, output_path=CHART_OUTPUT_PATH, width_inches=None):
    """
    Generates a wide PNG chart suitable for the right column of the report.
    """
    high = ohlc_summary["high"]
    low = ohlc_summary["low"]
    open_p = ohlc_summary["open"]
    last_p = ohlc_summary["last"]

    # Determine figure width: if caller supplies width_inches, use it; else use default CHART_WIDTH
    fig_width = width_inches if width_inches is not None else CHART_WIDTH
    fig, ax = plt.subplots(figsize=(fig_width, CHART_HEIGHT))

    # Styling: clean white background, subtle grid, remove top/right spines
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    accent = '#0B3D91'


    # Create two-row subplot: price (top) and volume (bottom)
    fig, (ax_price, ax_volume) = plt.subplots(
        2,
        1,
        figsize=(fig_width, CHART_HEIGHT),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )

    fig.patch.set_facecolor("white")
    ax_price.set_facecolor("white")
    ax_volume.set_facecolor("white")

    # X coordinate for single-day chart
    x = [0]

    # Price: vertical line for high-low
    ax_price.vlines(x, low, high, color="#0B3D91", linewidth=2)

    # Open-Close as thicker vertical bar (candle-like)
    bar_color = "#2E7D32" if last_p >= open_p else "#C62828"
    oc_bottom = min(open_p, last_p)
    oc_height = abs(last_p - open_p) if abs(last_p - open_p) > 0 else 0.001
    ax_price.bar(x, oc_height, bottom=oc_bottom, width=0.2, color=bar_color, align='center')

    # Styling for price axis
    ax_price.set_ylabel("Price")
    ax_price.yaxis.grid(True, color="#e9eef6", linewidth=0.8)
    ax_price.xaxis.set_visible(False)
    ax_price.spines["top"].set_visible(False)
    ax_price.spines["right"].set_visible(False)
    ax_price.spines["left"].set_visible(True)
    ax_price.spines["bottom"].set_visible(False)
    ax_price.tick_params(axis='y', labelsize=9)

    # Volume subplot
    vol = ohlc_summary.get("volume")
    if vol:
        vol_m = vol / 1_000_000.0
    else:
        vol_m = 0

    ax_volume.bar(x, [vol_m], width=0.4, color="#9aa4b2", align='center')
    ax_volume.set_ylabel("Volume (M)")
    ax_volume.yaxis.grid(True, color="#f0f4fa", linewidth=0.6)
    ax_volume.spines["top"].set_visible(False)
    ax_volume.spines["right"].set_visible(False)
    ax_volume.spines["left"].set_visible(True)
    ax_volume.spines["bottom"].set_visible(False)
    ax_volume.tick_params(axis='y', labelsize=8)

    # Hide x-axis ticks and labels (single-day chart)
    ax_volume.set_xticks([])

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=CHART_DPI)
    plt.close()

    return output_path
