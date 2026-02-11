# utils/chart_generator.py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from config import CHART_OUTPUT_PATH, CHART_DPI, CHART_WIDTH, CHART_HEIGHT

def generate_price_chart(ohlc_summary, output_path=CHART_OUTPUT_PATH):
    """
    Generates a wide PNG chart suitable for the right column of the report.
    """
    high = ohlc_summary["high"]
    low = ohlc_summary["low"]
    open_p = ohlc_summary["open"]
    last_p = ohlc_summary["last"]

    # Use strict landscape dimensions requested (6 x 3.5 inches)
    fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))

    ax.barh(0, high - low, left=low, height=0.5, edgecolor="black", alpha=0.85)
    ax.barh(1, abs(last_p - open_p) or 0.01, left=min(open_p, last_p), height=0.5, edgecolor="black", alpha=0.9)

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["High–Low", "Open–Last"])
    ax.set_xlabel("Price")
    ax.set_title("Daily Price Range")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=CHART_DPI)
    plt.close()

    return output_path
