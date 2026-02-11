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
)

# Import chart generator from utils
from utils.chart_generator import generate_price_chart

def build_pdf_report(price, news, summary):
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
        "section": ParagraphStyle("section", fontSize=PDF_FONT_SIZE_SECTION, fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("body", fontSize=PDF_FONT_SIZE_BODY),
        "small": ParagraphStyle("small", fontSize=PDF_FONT_SIZE_SMALL, textColor=colors.HexColor("#7a7a7a")),
    }

    elements = []
    # Title and meta row
    elements.append(Paragraph("Daily Stock Summary Report", styles["title"]))
    meta = Table([[Paragraph(f"<b>Stock Name:</b> {STOCK_NAME}", styles["meta"]), Paragraph(f"Report Date: {get_report_date()}", styles["meta_r"])]], colWidths=[3.25*inch, 3.25*inch])
    meta.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    elements.append(meta)
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Table([[""]], colWidths=[doc.width], style=[("LINEBELOW", (0,0), (-1,-1), 1, colors.HexColor("#e0e0e0"))]))
    elements.append(Spacer(1, 0.12*inch))

    # Top two-column area (Price Snapshot + Chart)
    price_table = Table(
        [
            ["Open Price", f"{price['open']:.2f}"],
            ["Close Price", f"{price['last']:.2f}"],
            ["Day High", f"{price['high']:.2f} at {price['high_time']}"],
            ["Day Low", f"{price['low']:.2f} at {price['low_time']}"],
        ],
        colWidths=[2.2*inch, 1.4*inch]
    )
    price_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#d9d9d9")),
        ("FONTNAME", (1,0), (1,-1), "Helvetica-Bold"),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))

    # ensure chart exists (generate if not)
    generate_price_chart(price, output_path=CHART_OUTPUT_PATH)
    chart_img = Image(CHART_OUTPUT_PATH, width=3.2*inch, height=2.3*inch)

    top_table = Table([[price_table, chart_img]], colWidths=[3.2*inch, 3.2*inch])
    top_table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0)]))

    elements.append(Paragraph("Price Snapshot", styles["section"]))
    elements.append(top_table)
    elements.append(Spacer(1, 0.12*inch))
    elements.append(Table([[""]], colWidths=[doc.width], style=[("LINEBELOW", (0,0), (-1,-1), 1, colors.HexColor("#e0e0e0"))]))
    elements.append(Spacer(1, 0.12*inch))

    # Stock-specific & Geopolitical News
    def add_news_block(title, items):
        elements.append(Paragraph(title, styles["section"]))
        if not items:
            elements.append(Paragraph("<i>No relevant headlines published.</i>", styles["body"]))
            return
        for n in items:
            # headline
            elements.append(Paragraph(f"• {n.get('headline','')}", styles["body"]))
            elements.append(Paragraph(f"Source: {n.get('source','')}", styles["body"]))
            elements.append(Paragraph(f"Link: {n.get('link','')}", styles["body"]))
            elements.append(Paragraph(f"Published: {n.get('publish_time','')}", styles["body"]))
            elements.append(Spacer(1, 0.06*inch))

    add_news_block("Stock-Specific News", news.get("stock", []))
    add_news_block("Geopolitical News", news.get("geopolitical", []))

    elements.append(Spacer(1, 0.08*inch))
    elements.append(Table([[""]], colWidths=[doc.width], style=[("LINEBELOW", (0,0), (-1,-1), 1, colors.HexColor("#e0e0e0"))]))
    elements.append(Spacer(1, 0.08*inch))

    # Lower two-column area: Major Market-Impact News (left) and Auto Summary (right)
    left_flow = []
    left_flow.append(Paragraph("Major Market-Impact News", styles["section"]))
    for n in news.get("market", []):
        left_flow.append(Paragraph(f"• {n.get('headline','')}", styles["body"]))
        left_flow.append(Paragraph(f"Source: {n.get('source','')}", styles["body"]))
        left_flow.append(Paragraph(f"Link: {n.get('link','')}", styles["body"]))
        left_flow.append(Spacer(1, 0.04*inch))

    right_flow = [Paragraph("Auto Summary", styles["section"])]
    for b in summary:
        right_flow.append(Paragraph(f"• {b}", styles["body"]))
        right_flow.append(Spacer(1, 0.02*inch))

    # Convert flow lists to simple single-column tables for side-by-side placement
    def flow_to_table(flow):
        return Table([[f] for f in flow], colWidths=[3.2*inch], style=[("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0)])

    lower = Table([[flow_to_table(left_flow), flow_to_table(right_flow)]], colWidths=[3.2*inch, 3.2*inch])
    lower.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))

    elements.append(lower)

    # Footer
    now = datetime.now(pytz.timezone(EXCHANGE_TIMEZONE))
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("This report is auto-generated for informational purposes only. No analysis, prediction, or investment advice is provided.", styles["small"]))
    elements.append(Paragraph(f"Report generated at: {now.strftime('%d %b %Y, %H:%M:%S %Z')}", styles["small"]))

    doc.build(elements)
