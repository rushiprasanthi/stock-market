# report_builder.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from datetime import datetime
import pytz

# Import config constants
from config import (
    PDF_OUTPUT_PATH,
    CHART_OUTPUT_PATH,
    PDF_FONT_SIZE_TITLE,
    PDF_FONT_SIZE_META,
    PDF_FONT_SIZE_SECTION,
    PDF_FONT_SIZE_BODY,
    PDF_FONT_SIZE_SMALL,
    EXCHANGE_TIMEZONE,
    get_report_date,
    STOCK_NAME,
    PRICE_DATA_CSV_PATH,
    CHART_WIDTH,
    CHART_HEIGHT,
)

# Import chart generator from utils
from utils.chart_generator import generate_price_chart

# Design tokens
ACCENT_COLOR = colors.HexColor("#0B3D91")  # deep blue
SECTION_BG = colors.HexColor("#F5F7FA")    # light grey section background
SUMMARY_BG = colors.HexColor("#EAF2FF")    # light blue for summary box


def build_pdf_report(price, news, summary, extended_metrics=None):
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=A4,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = {
        "title": ParagraphStyle("title", fontSize=PDF_FONT_SIZE_TITLE, alignment=TA_CENTER, fontName="Helvetica-Bold"),
        "meta": ParagraphStyle("meta", fontSize=PDF_FONT_SIZE_META),
        "meta_r": ParagraphStyle("meta_r", fontSize=PDF_FONT_SIZE_META, alignment=TA_RIGHT),
        # Header band white text
        "header_title_white": ParagraphStyle("header_title_white", fontSize=18, fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_LEFT, leading=20),
        "header_meta_white": ParagraphStyle("header_meta_white", fontSize=10, fontName="Helvetica", textColor=colors.white, alignment=TA_RIGHT),
    "section": ParagraphStyle("section", fontSize=PDF_FONT_SIZE_SECTION + 1, fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6),
    "summary": ParagraphStyle("summary", fontSize=PDF_FONT_SIZE_BODY - 1, leading=PDF_FONT_SIZE_BODY + 1),
        "body": ParagraphStyle("body", fontSize=PDF_FONT_SIZE_BODY),
        "small": ParagraphStyle("small", fontSize=PDF_FONT_SIZE_SMALL, textColor=colors.HexColor("#7a7a7a")),
    }

    elements = []
    # Header band (accent background)
    header_left = Paragraph(f"<b>Daily Stock Summary Report</b><br/>{STOCK_NAME}", styles["header_title_white"])
    header_right = Paragraph(f"Report Date: {get_report_date()}", styles["header_meta_white"])
    header = Table([[header_left, header_right]], colWidths=[doc.width*0.6, doc.width*0.4])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), ACCENT_COLOR),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 12))

    # Top two-column area (Price Snapshot + Chart)
    # Two-column responsive layout: left for price card, right for chart
    available_width = doc.width
    left_col_width = available_width * 0.55
    right_col_width = available_width * 0.45
    col_gap = 12  # points buffer between columns

    # Compute metrics
    open_p = float(price.get("open", 0) or 0)
    last_p = float(price.get("last", 0) or 0)
    high_p = float(price.get("high", 0) or 0)
    low_p = float(price.get("low", 0) or 0)
    volume = price.get("volume")

    change = last_p - open_p
    percent_change = (change / open_p * 100) if open_p else 0.0
    # Sentiment and momentum qualitative labels removed for trust-first / reference-only output
    sentiment = ""
    momentum_text = "Observed session range"
    intraday_range = high_p - low_p
    if abs(percent_change) > 2:
        vol_level = ""
    elif abs(percent_change) >= 1:
        vol_level = ""
    else:
        vol_level = ""

    # Build price rows
    price_rows = [
        ["Open Price", f"{open_p:,.2f}"],
        ["Close Price", f"{last_p:,.2f}"],
        ["Daily Change", f"{change:+,.2f} ({percent_change:+.2f}%)"],
        ["Intraday Movement", "Observed session range"],
        ["Day Low", f"{low_p:,.2f}"],
        ["Day High", f"{high_p:,.2f}"],
        ["Intraday Range", f"{intraday_range:,.2f}"],
        ["Volatility (% change magnitude)", f"{abs(percent_change):+.2f}%"],
        ["Volume", f"{int(volume):,}" if volume is not None else "N/A"],
    ]

    price_table = Table(price_rows, colWidths=[left_col_width * 0.6, left_col_width * 0.4])
    # base styles: subtle border, inner grid, padding, right-aligned values
    price_table_style = [
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME", (1,0), (1,-1), "Helvetica-Bold"),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#E0E0E0")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#F0F0F0")),
    ]
    # color the Daily Change row red/green
    change_row_index = 2
    change_color = colors.HexColor("#2e7d32") if change > 0 else colors.HexColor("#c62828") if change < 0 else colors.black
    price_table_style.append(("TEXTCOLOR", (1, change_row_index), (1, change_row_index), change_color))
    price_table.setStyle(TableStyle(price_table_style))

    # Wrap in white card with light grey border
    price_card = Table([[price_table]], colWidths=[left_col_width])
    price_card.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.white),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#E0E0E0")),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))

    # ensure chart exists (generate to match right column width)
    chart_width = right_col_width - col_gap
    chart_height = chart_width * 0.6
    width_inches = chart_width / inch
    generate_price_chart(price, output_path=CHART_OUTPUT_PATH, width_inches=width_inches)
    # set Image to exact computed dimensions
    chart_img = Image(CHART_OUTPUT_PATH, width=chart_width, height=chart_height)

    # Parent layout table with internal padding to prevent edge touching
    top_table = Table([[price_card, chart_img]], colWidths=[left_col_width, right_col_width])
    top_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), col_gap/2),
        ("RIGHTPADDING", (0,0), (-1,-1), col_gap/2),
    ]))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Price Snapshot", styles["section"]))
    elements.append(top_table)
    elements.append(Spacer(1, 18))
    elements.append(Table([[""]], colWidths=[doc.width], style=[("LINEBELOW", (0,0), (-1,-1), 1, colors.HexColor("#e0e0e0"))]))
    elements.append(Spacer(1, 0.12*inch))

    # (Earlier sequential daily price block removed — keep only the final appended reference-only sequential section.)

    # Stock-specific & Geopolitical News
    def add_news_block(title, items):
        elements.append(Paragraph(title, styles["section"]))
        if not items:
            elements.append(Paragraph("<i>No relevant headlines published.</i>", styles["body"]))
            return
        for n in items:
            # Create a news card
            headline = Paragraph(f"<b>{n.get('headline','')}</b>", ParagraphStyle("news_head", fontSize=PDF_FONT_SIZE_BODY + 1, fontName="Helvetica-Bold"))
            source = Paragraph(f"{n.get('source','')}", ParagraphStyle("news_source", fontSize=PDF_FONT_SIZE_SMALL, textColor=colors.HexColor("#6b6b6b")))
            link_text = n.get('link','')
            # Use a short, consistent anchor label and ensure color is blue per spec
            link = Paragraph(f'<a href="{link_text}" color="blue">Read More</a>', ParagraphStyle("news_link", fontSize=PDF_FONT_SIZE_BODY, textColor=ACCENT_COLOR))
            published = Paragraph(f"{n.get('publish_time','')}", ParagraphStyle("news_time", fontSize=PDF_FONT_SIZE_SMALL, alignment=TA_RIGHT, textColor=colors.HexColor("#6b6b6b")))

            # Build left (headline + source) and right (time) rows inside the card
            card_inner = Table([[headline, published],[source, link]], colWidths=[doc.width*0.75, doc.width*0.25])
            card_inner.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))

            card = Table([[card_inner]], colWidths=[doc.width])
            card.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1), SECTION_BG),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e6e9ef")),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
            elements.append(card)
            elements.append(Spacer(1, 8))

    # Extended Context Metrics (Reference Only) — render-only, uses precomputed data from data layer
    if extended_metrics:
        em = extended_metrics
        def _fmt_pct(v):
            try:
                return f"{float(v):+.2f}%"
            except Exception:
                return "N/A"

        def _fmt_num(v):
            try:
                return f"{float(v):,.0f}"
            except Exception:
                return "N/A"

        elements.append(Spacer(1, 14))
        elements.append(Paragraph('Extended Context Metrics (Reference Only)', styles['section']))
        elements.append(Paragraph('(Comparative Metrics | No Interpretation | No Forecasting)', ParagraphStyle('sub_ext', fontSize=PDF_FONT_SIZE_SMALL)))
        elements.append(Spacer(1, 8))

        # 20-Day Average Volume
        elements.append(Paragraph(f"20-Day Average Volume: {_fmt_num(em.get('avg_volume_20'))}", styles['body']))
        # Today's Volume vs 20-Day Average
        elements.append(Paragraph(f"Today’s Volume vs 20-Day Average: {_fmt_pct(em.get('volume_deviation_pct'))}", styles['body']))
        elements.append(Spacer(1, 6))

        # Intraday Range Percentile (30-Day)
        rp = em.get('range_percentile_30')
        # Format as numeric with two decimals, no ordinal suffix
        rp_text = f"{rp:.2f} percentile" if (rp is not None) else "N/A"
        elements.append(Paragraph(f"Intraday Range Percentile (30-Day): {rp_text}", styles['body']))
        elements.append(Spacer(1, 6))

        # Index Comparison (Same Session)
        elements.append(Paragraph('Index Comparison (Same Session)', styles['body']))
        elements.append(Paragraph(f"Stock Change: {_fmt_pct(em.get('stock_pct'))}", styles['body']))
        elements.append(Paragraph(f"Index Change: {_fmt_pct(em.get('index_pct'))}", styles['body']))
        elements.append(Paragraph(f"Relative Difference: {_fmt_pct(em.get('relative_diff'))}", styles['body']))
        elements.append(Spacer(1, 6))

        # Earnings block (optional)
        if em.get('earnings_date'):
            ed = em.get('earnings_date')
            de = em.get('days_until_earnings')
            elements.append(Paragraph(f"Next Earnings Date: {ed}", styles['body']))
            elements.append(Paragraph(f"Days Until Earnings: {int(de)}", styles['body']))
            elements.append(Spacer(1, 6))

        elements.append(Paragraph('All metrics are derived strictly from arithmetic comparison of observed data. No trend, performance judgment, or investment implication is expressed.', styles['small']))
        elements.append(Spacer(1, 14))

        # Advanced Comparative Metrics (Reference Only) — render-only, math-based
        if extended_metrics:
            am = extended_metrics
            # Check if any advanced metric exists to render section
            adv_keys = [
                'daily_return_zscore', 'vol_30', 'vol_90', 'vol_ratio',
                'avg_volume_30', 'avg_volume_90', 'volume_ratio',
                'stock_return_30d', 'sector_return_30d', 'relative_diff_30d',
                'rolling_peak_30d', 'drawdown_30d', 'beta_30d'
            ]
            if any(am.get(k) is not None for k in adv_keys):
                elements.append(Spacer(1, 16))
                elements.append(Paragraph('Advanced Comparative Metrics (Reference Only)', styles['section']))
                elements.append(Paragraph('(Math-Based | No Interpretation)', ParagraphStyle('sub_adv', fontSize=PDF_FONT_SIZE_SMALL)))
                elements.append(Spacer(1, 8))

                # Daily Return Z-Score
                drz = am.get('daily_return_zscore')
                if drz is not None:
                    try:
                        elements.append(Paragraph(f'Daily Return Z-Score (30-Day Reference): {float(drz):.2f}', styles['body']))
                    except Exception:
                        pass

                # Rolling volatilities
                v30 = am.get('vol_30')
                v90 = am.get('vol_90')
                vr = am.get('vol_ratio')
                if v30 is not None:
                    elements.append(Paragraph(f'Rolling Volatility (30-Day): {float(v30):.2f}%', styles['body']))
                if v90 is not None:
                    elements.append(Paragraph(f'Rolling Volatility (90-Day): {float(v90):.2f}%', styles['body']))
                if vr is not None:
                    elements.append(Paragraph(f'Volatility Ratio (30d / 90d): {float(vr):.2f}', styles['body']))

                # Volume regime
                av30 = am.get('avg_volume_30')
                av90 = am.get('avg_volume_90')
                vratio = am.get('volume_ratio')
                if av30 is not None:
                    try:
                        elements.append(Paragraph(f'Average Volume (30-Day): {int(av30):,}', styles['body']))
                    except Exception:
                        elements.append(Paragraph(f'Average Volume (30-Day): {av30}', styles['body']))
                if av90 is not None:
                    try:
                        elements.append(Paragraph(f'Average Volume (90-Day): {int(av90):,}', styles['body']))
                    except Exception:
                        elements.append(Paragraph(f'Average Volume (90-Day): {av90}', styles['body']))
                if vratio is not None:
                    elements.append(Paragraph(f'Volume Ratio (30d / 90d): {float(vratio):.2f}', styles['body']))

                # Returns comparison
                sr = am.get('stock_return_30d')
                se = am.get('sector_return_30d')
                rd = am.get('relative_diff_30d')
                if sr is not None:
                    elements.append(Paragraph(f'30-Day Return (Stock): {float(sr):+.2f}%', styles['body']))
                if se is not None:
                    elements.append(Paragraph(f'30-Day Return (Sector): {float(se):+.2f}%', styles['body']))
                if rd is not None:
                    elements.append(Paragraph(f'Return Differential: {float(rd):+.2f}%', styles['body']))

                # Peak and drawdown
                rp = am.get('rolling_peak_30d')
                dd = am.get('drawdown_30d')
                if rp is not None:
                    try:
                        elements.append(Paragraph(f'Maximum 30-Day Peak Close: {float(rp):,.2f}', styles['body']))
                    except Exception:
                        elements.append(Paragraph(f'Maximum 30-Day Peak Close: {rp}', styles['body']))
                if dd is not None:
                    elements.append(Paragraph(f'Current Close vs 30-Day Peak: {float(dd):+.2f}%', styles['body']))

                # Beta
                b30 = am.get('beta_30d')
                if b30 is not None:
                    elements.append(Paragraph(f'Beta (30-Day, vs Benchmark): {float(b30):.2f}', styles['body']))

                elements.append(Spacer(1, 12))

        add_news_block("Stock-Specific News", news.get("stock", []))
    elements.append(Spacer(1, 14))
    add_news_block("Geopolitical News", news.get("geopolitical", []))
    elements.append(Spacer(1, 14))

    elements.append(Spacer(1, 0.08*inch))
    elements.append(Table([[""]], colWidths=[doc.width], style=[("LINEBELOW", (0,0), (-1,-1), 1, colors.HexColor("#e0e0e0"))]))
    elements.append(Spacer(1, 0.08*inch))

    # Lower area: render Market news as individual cards (no outer table) so they can split across pages.
    elements.append(Paragraph("Major Market-Impact News", styles["section"]))
    market_items = news.get("market", [])
    if not market_items:
        elements.append(Paragraph("<i>No relevant headlines published.</i>", styles["body"]))
    else:
        for n in market_items:
            headline = Paragraph(f"<b>{n.get('headline','')}</b>", ParagraphStyle("news_head_mkt", fontSize=PDF_FONT_SIZE_BODY + 1, fontName="Helvetica-Bold"))
            source = Paragraph(f"{n.get('source','')}", ParagraphStyle("news_source_mkt", fontSize=PDF_FONT_SIZE_SMALL, textColor=colors.HexColor("#6b6b6b")))
            link_text = n.get('link','')
            link = Paragraph(f'<a href="{link_text}" color="blue">Read More</a>', ParagraphStyle("news_link_mkt", fontSize=PDF_FONT_SIZE_BODY, textColor=ACCENT_COLOR))
            published = Paragraph(f"{n.get('publish_time','')}", ParagraphStyle("news_time_mkt", fontSize=PDF_FONT_SIZE_SMALL, alignment=TA_RIGHT, textColor=colors.HexColor("#6b6b6b")))

            card_inner = Table([[headline, published],[source, link]], colWidths=[doc.width*0.75, doc.width*0.25])
            card_inner.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))

            card = Table([[card_inner]], colWidths=[doc.width])
            card.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1), SECTION_BG),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e6e9ef")),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
            elements.append(card)
            elements.append(Spacer(1, 8))

    # Build Auto Summary box (highlighted)
    # Generate a trust-safe auto summary from price and news counts (no interpretation or advice)
    # Calculations required by spec
    try:
        pct_change = ((float(price.get("last", 0) or 0) - float(price.get("open", 0) or 0)) / float(price.get("open", 1))) * 100
    except Exception:
        pct_change = 0.0
    intraday_range_val = float(price.get("high", 0) or 0) - float(price.get("low", 0) or 0)
    if pct_change > 0:
        direction_phrase = "above"
    elif pct_change < 0:
        direction_phrase = "below"
    else:
        direction_phrase = "in line with"

    geo_count = len(news.get("geopolitical", []))
    mkt_count = len(news.get("market", []))
    stk_count = len(news.get("stock", []))
    total_activity = geo_count + mkt_count
    # Headline activity is presented as numeric counts only; qualitative labels removed
    headline_activity_level = None

    # Paragraph 1
    p1 = Paragraph(
        f"{STOCK_NAME} closed {abs(pct_change):.2f}% {direction_phrase} its opening price during the session. Intraday range measured {intraday_range_val:.2f}, with volatility (change magnitude) {abs(pct_change):.2f}%.",
        styles["body"]
    )

    # Paragraph 2
    p2 = Paragraph(
        f"Total Headlines (Company / Geopolitical / Market): {stk_count} / {geo_count} / {mkt_count}",
        styles["body"]
    )

    # Bullet points
    bp1 = Paragraph(f"• Open: {float(price.get('open', 0)):.2f} — Close: {float(price.get('last', 0)):.2f}", styles["summary"]) 
    bp2 = Paragraph(f"• High: {float(price.get('high', 0)):.2f} — Low: {float(price.get('low', 0)):.2f}", styles["summary"]) 
    bp3 = Paragraph("• Information flow from news feeds was recorded for the session.", styles["summary"]) 

    closing = Paragraph(
        "This summary presents session metrics and observed information flow without interpretive commentary or forward-looking implications.",
        ParagraphStyle("summary_close", fontSize=PDF_FONT_SIZE_SMALL)
    )

    summary_items = [Paragraph("Auto Summary", styles["section"]), p1, Spacer(1, 6), p2, Spacer(1, 6), bp1, bp2, bp3, Spacer(1, 6), closing]

    # Convert summary_items into a highlighted box
    summary_table = Table([[item] for item in summary_items], colWidths=[3.2*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), SUMMARY_BG),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))

    # (Removed side-by-side wrapper for Market news to allow natural page breaks.)
    # Append the summary box below the market news so it doesn't prevent splitting across pages.
    elements.append(Spacer(1, 14))
    elements.append(summary_table)

    # Market Context Indicators section (must flow naturally; not wrapped in a large parent table)
    # Requirements: append flowables directly to elements
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Market Context Indicators", styles["section"]))
    elements.append(Spacer(1, 8))

    # Calculations
    try:
        pct_change = ((float(price.get("last", 0) or 0) - float(price.get("open", 0) or 0)) / float(price.get("open", 1))) * 100
    except Exception:
        pct_change = 0.0
    intraday_range_calc = float(price.get("high", 0) or 0) - float(price.get("low", 0) or 0)
    # Note: present numeric indicators only (no qualitative labels)
    geopolitical_count = len(news.get("geopolitical", []))
    market_count = len(news.get("market", []))
    stock_count = len(news.get("stock", []))

    # Build two-column table rows
    m_rows = [
        ["Price Change (%)", f"{pct_change:+.2f}%"],
        ["Intraday Range", f"{intraday_range_calc:.2f}"],
        ["Volatility (% change magnitude)", f"{abs(pct_change):+.2f}%"],
        ["Company Headline Count", str(stock_count)],
        ["Geopolitical Headline Count", str(geopolitical_count)],
        ["Market Headline Count", str(market_count)],
        ["Total Headlines (Company / Geopolitical / Market)", f"{stock_count} / {geopolitical_count} / {market_count}"],
    ]

    indicators_table = Table(m_rows, colWidths=[doc.width * 0.55, doc.width * 0.45])
    indicators_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))

    elements.append(indicators_table)

    # Footer
    now = datetime.now(pytz.timezone(EXCHANGE_TIMEZONE))
    elements.append(Spacer(1, 0.12*inch))
    elements.append(Table([[""]], colWidths=[doc.width], style=[("LINEABOVE", (0,0), (-1,-1), 0.5, colors.HexColor("#d9d9d9"))]))
    elements.append(Spacer(1, 0.06*inch))
    elements.append(Paragraph("This report is auto-generated for informational purposes only. No analysis, prediction, or investment advice is provided.", ParagraphStyle("footer_small", fontSize=PDF_FONT_SIZE_SMALL, italic=True, textColor=colors.HexColor("#6b6b6b"))))
    elements.append(Paragraph(f"Report generated at: {now.strftime('%d %b %Y, %H:%M:%S %Z')}", ParagraphStyle("footer_time", fontSize=PDF_FONT_SIZE_SMALL, alignment=TA_RIGHT, textColor=colors.HexColor("#6b6b6b"))))

    # ------------------------------------------------------------------
    # Trust-First reference section (append-only) — append flowables
    # immediately before building the document. This section must not
    # modify existing content or layout; it will use in-memory 5-day
    # closes if available, otherwise fetch historical daily closes from
    # the same data provider (Yahoo) and extract the last 5 valid
    # trading sessions. All results are math-only, reference-only.
    # ------------------------------------------------------------------

    # Try to reuse in-memory `closes` if present (defined earlier) or read processed CSV
    existing_closes = []
    try:
        # Attempt to read processed CSV for recent closes as a fallback
        import csv
        from dateutil.parser import parse as _parse_date
        with open(PRICE_DATA_CSV_PATH, newline='', encoding='utf-8') as _f:
            reader = csv.DictReader(_f)
            for row in reader:
                date_raw = row.get('date') or row.get('time') or ''
                close_raw = row.get('close') or row.get('Close') or ''
                try:
                    close_val = float(close_raw)
                except Exception:
                    continue
                day_name = ''
                date_str = date_raw
                try:
                    dt = _parse_date(date_raw)
                    day_name = dt.strftime('%a')
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    pass
                existing_closes.append({'date': date_str, 'day': day_name, 'close': close_val})
    except Exception:
        existing_closes = existing_closes or []

    use_closes = []  # chronological order: oldest -> newest

    # If we have at least 5 in-memory entries, normalize and use them
    if isinstance(existing_closes, list) and len(existing_closes) >= 5:
        # attempt to parse dates and sort to ensure chronological order
        try:
            from dateutil.parser import parse as _parse_date
            parsed = []
            for r in existing_closes:
                d = r.get('date', '')
                try:
                    dt = _parse_date(d)
                    parsed.append((dt, r))
                except Exception:
                    parsed.append((None, r))
            with_dt = [p for p in parsed if p[0] is not None]
            without_dt = [p for p in parsed if p[0] is None]
            with_dt.sort(key=lambda x: x[0])
            ordered = [r for (_dt, r) in with_dt + without_dt]
            if len(ordered) > 5:
                ordered = ordered[-5:]
            use_closes = ordered
        except Exception:
            # fallback: take last 5 rows and assume they are chronological
            use_closes = existing_closes[-5:]

    # If not enough in-memory closes, fetch historical daily closes from Yahoo
    if len(use_closes) < 5:
        try:
            import requests
            from datetime import datetime as _dt
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{STOCK_NAME}"
            params = {"interval": "1d", "range": "20d"}  # request ~20 calendar days
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            res = data.get('chart', {}).get('result')
            rows = []
            if res:
                r0 = res[0]
                timestamps = r0.get('timestamp', [])
                quote = r0.get('indicators', {}).get('quote', [])
                closes_list = quote[0].get('close', []) if quote else []
                tz = pytz.timezone(EXCHANGE_TIMEZONE)
                for ts, c in zip(timestamps, closes_list):
                    if c is None:
                        continue
                    dt_utc = _dt.utcfromtimestamp(ts).replace(tzinfo=pytz.utc)
                    dt_local = dt_utc.astimezone(tz)
                    rows.append({'date': dt_local.strftime('%Y-%m-%d'), 'day': dt_local.strftime('%a'), 'close': float(c)})
                if len(rows) > 5:
                    rows = rows[-5:]
            use_closes = rows
        except Exception:
            use_closes = use_closes or []

    # Proceed only if we have at least one trading row; prefer 5
    if use_closes and len(use_closes) >= 1:
        # Ensure chronological order oldest->newest
        try:
            from dateutil.parser import parse as _parse_date2
            parsed = []
            for r in use_closes:
                try:
                    dt = _parse_date2(r.get('date', ''))
                    parsed.append((dt, r))
                except Exception:
                    parsed.append((None, r))
            with_dt = [p for p in parsed if p[0] is not None]
            without_dt = [p for p in parsed if p[0] is None]
            with_dt.sort(key=lambda x: x[0])
            ordered = [r for (_dt, r) in with_dt + without_dt]
        except Exception:
            ordered = list(use_closes)

        # Keep only last 5 trading rows (most recent 5)
        if len(ordered) > 5:
            ordered = ordered[-5:]

        # Build chronological math rows (oldest -> newest)
        math_rows = []
        for i, rec in enumerate(ordered):
            date = rec.get('date', '')
            day = rec.get('day', '')
            close_val = float(rec.get('close', 0.0))
            if i == 0:
                change_str = '–'
            else:
                prev = float(ordered[i-1].get('close', 0.0))
                diff = close_val - prev
                change_str = f"{diff:+.2f}"
            math_rows.append([date, day, f"{close_val:.2f}", change_str])

        # Display most recent first
        display_rows = [['Date', 'Day', 'Close Price', 'Change vs Previous Day']] + list(reversed(math_rows))

        seq_table = Table(display_rows, colWidths=[doc.width * 0.25, doc.width * 0.15, doc.width * 0.30, doc.width * 0.30])
        seq_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (2,1), (3,-1), 'RIGHT'),
        ]))

        elements.append(Spacer(1, 20))
        elements.append(Paragraph('Daily Price Change (Sequential Reference)', styles['section']))
        elements.append(Paragraph('(Math-only | No interpretation | No conclusion)', ParagraphStyle('sub_small_ref', fontSize=PDF_FONT_SIZE_SMALL)))
        elements.append(Spacer(1, 8))
        elements.append(seq_table)
        elements.append(Spacer(1, 6))
        elements.append(Paragraph('All differences are computed mathematically. No performance judgement or directional implication is made.', styles['small']))

        # 5-Day Price Extremes (Observed Data)
        try:
            closes_vals = [float(r[2]) for r in math_rows]
            dates_vals = [r[0] for r in math_rows]
            days_vals = [r[1] for r in math_rows]
            max_idx = closes_vals.index(max(closes_vals))
            min_idx = closes_vals.index(min(closes_vals))
            max_val = closes_vals[max_idx]
            max_date = dates_vals[max_idx]
            max_day = days_vals[max_idx]
            min_val = closes_vals[min_idx]
            min_date = dates_vals[min_idx]
            min_day = days_vals[min_idx]

            elements.append(Spacer(1, 14))
            elements.append(Paragraph('5-Day Price Extremes (Observed Data)', styles['section']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f'• Highest close (5-day): {max_val:.2f} on {max_date} ({max_day})', styles['body']))
            elements.append(Paragraph(f'• Lowest close (5-day): {min_val:.2f} on {min_date} ({min_day})', styles['body']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph('Extremes are presented as factual observations only.', styles['small']))
            # 5-Day Close Change (Observed Data) — derived from the same 5 trading rows used above
            try:
                # closes_vals is a list of floats ordered oldest->newest (from math_rows)
                latest_close = float(closes_vals[-1])
                oldest_close = float(closes_vals[0])
                net_change_5d = latest_close - oldest_close
                close_range_5d = float(max_val) - float(min_val)

                elements.append(Spacer(1, 8))
                elements.append(Paragraph('5-Day Close Change (Observed Data)', styles['section']))
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(f'• Net Change (Latest vs Oldest Close): {net_change_5d:+.2f}', styles['body']))
                elements.append(Paragraph(f'• Absolute Close Range (5-day): {close_range_5d:+.2f}', styles['body']))
                # Render additional 5-day statistical metrics from precomputed extended_metrics when available
                try:
                    if extended_metrics:
                        sd5 = extended_metrics.get('std_dev_5')
                        avg5 = extended_metrics.get('avg_change_5')
                        if sd5 is not None:
                            elements.append(Paragraph(f'• 5-Day Standard Deviation (Close): {float(sd5):.2f}', styles['body']))
                        if avg5 is not None:
                            elements.append(Paragraph(f'• Average 5-Day Daily Change: {float(avg5):+.2f}', styles['body']))
                except Exception:
                    # don't break the report if extended metrics are malformed
                    pass
                elements.append(Spacer(1, 6))
                elements.append(Paragraph('All values are derived strictly from arithmetic comparison of closing prices. No trend or performance implication is made.', styles['small']))
            except Exception:
                # if any issue computing the 5-day close change, skip without breaking report
                pass
        except Exception:
            # if any issue computing extremes, skip without breaking report
            pass

    # End appended Trust-First reference section

        # ------------------------------------------------------------------
        # SECTION: Weekly and Monthly Performance Classification
        # Append-only, trust-first, math-only (no interpretation or forecasting)
        # ------------------------------------------------------------------
        try:
            # Ensure we have a broader set of historical rows to locate week/month opens.
            # Attempt to reuse 'ordered' if available; otherwise fetch ~60 days.
            historical_rows = None
            try:
                historical_rows = ordered
            except Exception:
                historical_rows = None

            if not historical_rows or len(historical_rows) < 5:
                import requests
                from datetime import datetime as _dt
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{STOCK_NAME}"
                params = {"interval": "1d", "range": "60d"}
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                res = data.get('chart', {}).get('result')
                rows_all = []
                if res:
                    r0 = res[0]
                    timestamps = r0.get('timestamp', [])
                    quote = r0.get('indicators', {}).get('quote', [])
                    closes_list = quote[0].get('close', []) if quote else []
                    tz = pytz.timezone(EXCHANGE_TIMEZONE)
                    for ts, c in zip(timestamps, closes_list):
                        if c is None:
                            continue
                        dt_utc = _dt.utcfromtimestamp(ts).replace(tzinfo=pytz.utc)
                        dt_local = dt_utc.astimezone(tz)
                        rows_all.append({'date': dt_local.strftime('%Y-%m-%d'), 'day': dt_local.strftime('%a'), 'close': float(c)})
                historical_rows = rows_all

            # Ensure chronological order oldest->newest
            try:
                from dateutil.parser import parse as _parse_date3
                parsed = []
                for r in historical_rows:
                    try:
                        dt = _parse_date3(r.get('date', ''))
                        parsed.append((dt, r))
                    except Exception:
                        parsed.append((None, r))
                with_dt = [p for p in parsed if p[0] is not None]
                without_dt = [p for p in parsed if p[0] is None]
                with_dt.sort(key=lambda x: x[0])
                ordered_all = [r for (_dt, r) in with_dt + without_dt]
            except Exception:
                ordered_all = list(historical_rows or [])

            if not ordered_all:
                raise ValueError("No historical rows available for weekly/monthly computation")

            # Determine current_close as the most recent available closing price (last trading row)
            current_close = float(ordered_all[-1]['close'])

            # Helper to find first trading row on/after a date
            from datetime import datetime as _dt2, timedelta
            from dateutil.parser import parse as _parse_date4
            def _find_first_on_or_after(rows, target_dt):
                for r in rows:
                    try:
                        d = _parse_date4(r.get('date', ''))
                        if d.date() >= target_dt.date():
                            return r
                    except Exception:
                        continue
                return None

            # Week opening: first trading day of current calendar week (Monday-based)
            tz = pytz.timezone(EXCHANGE_TIMEZONE)
            now_local = datetime.now(tz)
            monday = now_local - timedelta(days=now_local.weekday())
            week_open_row = _find_first_on_or_after(ordered_all, monday)

            # Month opening: first trading day of current calendar month
            month_start = now_local.replace(day=1)
            month_open_row = _find_first_on_or_after(ordered_all, month_start)

            # If not found in range, fall back to oldest available row
            if not week_open_row:
                week_open_row = ordered_all[0]
            if not month_open_row:
                month_open_row = ordered_all[0]

            week_open_price = float(week_open_row['close'])
            month_open_price = float(month_open_row['close'])

            weekly_change = current_close - week_open_price
            monthly_change = current_close - month_open_price

            weekly_result = 'Profit' if weekly_change > 0 else ('Loss' if weekly_change < 0 else 'Neutral')
            monthly_result = 'Profit' if monthly_change > 0 else ('Loss' if monthly_change < 0 else 'Neutral')

            # Append Weekly section
            elements.append(Spacer(1, 12))
            elements.append(Paragraph('Weekly Performance Classification (Price-Based Only)', styles['section']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"Week Opening Price: {week_open_price:.2f}", styles['body']))
            elements.append(Paragraph(f"Current Closing Price: {current_close:.2f}", styles['body']))
            elements.append(Paragraph(f"Weekly Change: {weekly_change:+.2f}", styles['body']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph('Result derived strictly through arithmetic comparison. No interpretation, forecasting, or performance implication is applied.', styles['small']))

            # Append Monthly section
            elements.append(Spacer(1, 12))
            elements.append(Paragraph('Monthly Performance Classification (Price-Based Only)', styles['section']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"Month Opening Price: {month_open_price:.2f}", styles['body']))
            elements.append(Paragraph(f"Current Closing Price: {current_close:.2f}", styles['body']))
            elements.append(Paragraph(f"Monthly Change: {monthly_change:+.2f}", styles['body']))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph('Outcome determined strictly through mathematical comparison. No sentiment, prediction, or investment judgment is implied.', styles['small']))
        except Exception:
            # Do not break report; if any error occurs, skip weekly/monthly sections
            pass

    doc.build(elements)
