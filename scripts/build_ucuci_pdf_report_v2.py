from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "tableau_outputs"
OUT_DIR = ROOT / "output" / "pdf"
PDF_PATH = OUT_DIR / "UCUCI_Loan_Repayment_Analysis_Report.pdf"

PAGE_W, PAGE_H = letter
MARGIN = 54
CONTENT_W = PAGE_W - 2 * MARGIN
TOP = PAGE_H - MARGIN

FONT = "Arial"
FONT_BOLD = "Arial-Bold"
BODY = 12
LEADING = 15

INK = HexColor("#1F2933")
MUTED = HexColor("#52606D")
NAVY = HexColor("#102A43")
GREEN = HexColor("#1F7A4D")
AMBER = HexColor("#B7791F")
RED = HexColor("#B91C1C")
BLUE = HexColor("#2563A6")
TEAL = HexColor("#157A6E")
LIGHT_GREEN = HexColor("#E7F5EE")
LIGHT_AMBER = HexColor("#FFF4D6")
LIGHT_RED = HexColor("#FCE8E8")
LIGHT_BLUE = HexColor("#EAF3F8")
LIGHT_GRAY = HexColor("#F4F6F8")
GRID = HexColor("#D9E2EC")


def setup() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont(FONT, r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\arialbd.ttf"))


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)


def wrap(text: str, width: float, font: str = FONT, size: int = BODY) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    line = ""
    for word in words:
        trial = f"{line} {word}".strip()
        if not line or pdfmetrics.stringWidth(trial, font, size) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def text(
    c: canvas.Canvas,
    value: str,
    x: float,
    y: float,
    width: float,
    font: str = FONT,
    size: int = BODY,
    color: colors.Color = INK,
    leading: int = LEADING,
) -> float:
    c.setFont(font, size)
    c.setFillColor(color)
    for paragraph in str(value).split("\n"):
        if not paragraph.strip():
            y -= leading
            continue
        for line in wrap(paragraph, width, font, size):
            c.drawString(x, y, line)
            y -= leading
    return y


def bullets(c: canvas.Canvas, items: list[str], x: float, y: float, width: float) -> float:
    for item in items:
        lines = wrap(item, width - 18)
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawString(x, y, "-")
        for line in lines:
            c.drawString(x + 16, y, line)
            y -= LEADING
        y -= 2
    return y


def title(c: canvas.Canvas, value: str, subtitle: str = "") -> float:
    y = TOP
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 18)
    c.drawString(MARGIN, y, value)
    if subtitle:
        c.setFont(FONT, BODY)
        c.setFillColor(MUTED)
        c.drawRightString(PAGE_W - MARGIN, y, subtitle)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.8)
    c.line(MARGIN, y - 10, PAGE_W - MARGIN, y - 10)
    return y - 38


def heading(c: canvas.Canvas, value: str, x: float, y: float, color: colors.Color = NAVY) -> float:
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(color)
    c.drawString(x, y, value)
    return y - 22


def rounded_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill: colors.Color, stroke: colors.Color = GRID) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1)
    c.roundRect(x, y - h, w, h, 6, fill=1, stroke=1)


def badge(c: canvas.Canvas, x: float, y: float, label: str, fill: colors.Color, stroke: colors.Color) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.roundRect(x, y - 21, 92, 21, 5, fill=1, stroke=1)
    c.setFillColor(stroke)
    c.setFont(FONT_BOLD, BODY)
    c.drawCentredString(x + 46, y - 15, label)


def legend(c: canvas.Canvas, x: float, y: float) -> None:
    entries = [("Positive", GREEN), ("Monitor", AMBER), ("Risk", RED)]
    c.setFont(FONT, BODY)
    c.setFillColor(MUTED)
    c.drawString(x, y, "Legend:")
    lx = x + 55
    for label, color in entries:
        c.setFillColor(color)
        c.rect(lx, y - 3, 10, 10, fill=1, stroke=0)
        c.setFillColor(INK)
        c.drawString(lx + 15, y, label)
        lx += 86


def lrr_color(value: float) -> colors.Color:
    if value >= 102:
        return GREEN
    if value >= 95:
        return AMBER
    return RED


def delinquency_color(value: float) -> colors.Color:
    if value <= 3:
        return GREEN
    if value <= 6:
        return AMBER
    return RED


def exposure_color(value: float, high: float, medium: float) -> colors.Color:
    if value >= high:
        return RED
    if value >= medium:
        return AMBER
    return GREEN


def draw_table(
    c: canvas.Canvas,
    x: float,
    y: float,
    widths: list[float],
    headers: list[str],
    rows: list[list[str]],
    fill: colors.Color = LIGHT_BLUE,
) -> float:
    pad = 7
    all_rows = [headers] + rows
    heights = []
    wrapped = []
    for idx, row in enumerate(all_rows):
        font = FONT_BOLD if idx == 0 else FONT
        row_lines = [wrap(cell, w - pad * 2, font) for cell, w in zip(row, widths)]
        wrapped.append(row_lines)
        heights.append(max(len(lines) for lines in row_lines) * 15 + 14)
    total_w = sum(widths)
    for r, row_h in enumerate(heights):
        y -= row_h
        c.setFillColor(fill if r == 0 else colors.white)
        c.setStrokeColor(GRID)
        c.rect(x, y, total_w, row_h, fill=1, stroke=1)
        cx = x
        for col, w in enumerate(widths):
            c.rect(cx, y, w, row_h, fill=0, stroke=1)
            c.setFont(FONT_BOLD if r == 0 else FONT, BODY)
            c.setFillColor(NAVY if r == 0 else INK)
            ty = y + row_h - pad - BODY
            for line in wrapped[r][col]:
                c.drawString(cx + pad, ty, line)
                ty -= 15
            cx += w
    return y - 14


def bar_chart(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    labels: list[str],
    values: list[float],
    chart_title: str,
    ymin: float,
    ymax: float,
    color_fn,
    suffix: str = "%",
) -> None:
    rounded_box(c, x, y, w, h, colors.white, GRID)
    c.setFont(FONT_BOLD, 13)
    c.setFillColor(NAVY)
    c.drawString(x + 12, y - 22, chart_title)
    legend(c, x + 12, y - 43)
    px, py = x + 50, y - h + 42
    pw, ph = w - 76, h - 92
    c.setStrokeColor(GRID)
    c.line(px, py, px, py + ph)
    c.line(px, py, px + pw, py)
    for tick in [ymin, (ymin + ymax) / 2, ymax]:
        ty = py + (tick - ymin) / (ymax - ymin) * ph
        c.setStrokeColor(HexColor("#EDF2F7"))
        c.line(px, ty, px + pw, ty)
        c.setFillColor(MUTED)
        c.setFont(FONT, BODY)
        c.drawRightString(px - 7, ty - 4, f"{tick:.0f}")
    gap = 8
    bw = (pw - gap * (len(values) - 1)) / len(values)
    for i, (label, value) in enumerate(zip(labels, values)):
        bx = px + i * (bw + gap)
        bh = max(1, (value - ymin) / (ymax - ymin) * ph)
        c.setFillColor(color_fn(value))
        c.rect(bx, py, bw, bh, fill=1, stroke=0)
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawCentredString(bx + bw / 2, py - 17, label)
        c.drawCentredString(bx + bw / 2, py + bh + 5, f"{value:.1f}{suffix}")


def line_chart(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    labels: list[str],
    values: list[float],
    chart_title: str,
    ymin: float,
    ymax: float,
    color_fn,
    suffix: str = "%",
) -> None:
    rounded_box(c, x, y, w, h, colors.white, GRID)
    c.setFont(FONT_BOLD, 13)
    c.setFillColor(NAVY)
    c.drawString(x + 12, y - 22, chart_title)
    legend(c, x + 12, y - 43)
    px, py = x + 52, y - h + 42
    pw, ph = w - 78, h - 92
    c.setStrokeColor(GRID)
    c.line(px, py, px, py + ph)
    c.line(px, py, px + pw, py)
    for tick in [ymin, (ymin + ymax) / 2, ymax]:
        ty = py + (tick - ymin) / (ymax - ymin) * ph
        c.setStrokeColor(HexColor("#EDF2F7"))
        c.line(px, ty, px + pw, ty)
        c.setFillColor(MUTED)
        c.setFont(FONT, BODY)
        c.drawRightString(px - 7, ty - 4, f"{tick:.0f}")
    pts = []
    for i, value in enumerate(values):
        pts.append((px + i * (pw / (len(values) - 1)), py + (value - ymin) / (ymax - ymin) * ph))
    c.setStrokeColor(BLUE)
    c.setLineWidth(2)
    for p1, p2 in zip(pts, pts[1:]):
        c.line(p1[0], p1[1], p2[0], p2[1])
    c.setLineWidth(1)
    for (cx, cy), label, value in zip(pts, labels, values):
        c.setFillColor(color_fn(value))
        c.circle(cx, cy, 4.5, fill=1, stroke=0)
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawCentredString(cx, py - 18, label)
        c.drawCentredString(cx, cy + 8, f"{value:.1f}{suffix}")


def horizontal_chart(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    labels: list[str],
    values: list[float],
    chart_title: str,
    color_fn,
    suffix: str = "",
) -> None:
    rounded_box(c, x, y, w, h, colors.white, GRID)
    c.setFont(FONT_BOLD, 13)
    c.setFillColor(NAVY)
    c.drawString(x + 12, y - 22, chart_title)
    legend(c, x + 12, y - 43)
    px = x + 150
    base_y = y - h + 34
    pw = w - 178
    row_h = (h - 82) / len(values)
    max_value = max(values) * 1.08
    for idx, (label, value) in enumerate(zip(labels, values)):
        yy = base_y + (len(values) - idx - 1) * row_h
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawRightString(px - 8, yy + 5, label)
        c.setFillColor(color_fn(value))
        c.rect(px, yy, pw * value / max_value, row_h - 7, fill=1, stroke=0)
        c.setFillColor(INK)
        c.drawString(px + pw * value / max_value + 6, yy + 5, f"{value:.1f}{suffix}")


def heatmap(c: canvas.Canvas, x: float, y: float, w: float, h: float, df: pd.DataFrame) -> None:
    rounded_box(c, x, y, w, h, colors.white, GRID)
    c.setFont(FONT_BOLD, 13)
    c.setFillColor(NAVY)
    c.drawString(x + 12, y - 22, "LRR by Grade and Term")
    legend(c, x + 12, y - 43)
    grades = list("ABCDEFG")
    terms = ["36 months", "60 months"]
    lookup = {(row["grade"], row["term"]): row["LRR"] for _, row in df.iterrows()}
    start_y = y - 72
    cell_w = (w - 100) / 2
    cell_h = (h - 105) / len(grades)
    c.setFont(FONT_BOLD, BODY)
    c.setFillColor(NAVY)
    c.drawString(x + 18, start_y + 15, "Grade")
    for j, term in enumerate(terms):
        c.drawCentredString(x + 80 + j * cell_w + cell_w / 2, start_y + 15, term.replace(" months", " m"))
    for i, grade in enumerate(grades):
        yy = start_y - (i + 1) * cell_h
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, BODY)
        c.drawString(x + 24, yy + cell_h / 2 - 4, grade)
        for j, term in enumerate(terms):
            value = lookup[(grade, term)]
            fill = LIGHT_GREEN if value >= 102 else LIGHT_AMBER if value >= 95 else LIGHT_RED
            stroke = GREEN if value >= 102 else AMBER if value >= 95 else RED
            xx = x + 80 + j * cell_w
            c.setFillColor(fill)
            c.setStrokeColor(colors.white)
            c.rect(xx, yy, cell_w, cell_h, fill=1, stroke=1)
            c.setFillColor(stroke)
            c.setFont(FONT_BOLD, BODY)
            c.drawCentredString(xx + cell_w / 2, yy + cell_h / 2 - 4, f"{value:.1f}%")


def analysis_box(c: canvas.Canvas, x: float, y: float, w: float, body: str, fill: colors.Color = LIGHT_GRAY) -> float:
    lines = wrap(body, w - 24, FONT, BODY)
    h = len(lines) * 15 + 42
    rounded_box(c, x, y, w, h, fill, GRID)
    c.setFont(FONT_BOLD, BODY)
    c.setFillColor(NAVY)
    c.drawString(x + 12, y - 18, "What this means")
    text(c, body, x + 12, y - 38, w - 24)
    return y - h - 18


def build_pdf() -> None:
    setup()
    kpis = read_csv("dashboard_kpi_reference.csv")
    kpi = dict(zip(kpis["Metric"], kpis["Value"]))
    by_grade = read_csv("closed_lrr_by_grade.csv")
    by_rate = read_csv("closed_lrr_by_interest_band.csv").dropna(subset=["LRR"])
    by_dti = read_csv("closed_lrr_by_dti_band.csv").dropna(subset=["LRR"])
    by_term = read_csv("closed_lrr_by_term.csv")
    by_purpose = read_csv("closed_lrr_by_purpose.csv")
    by_grade_term = read_csv("closed_lrr_by_grade_term.csv")
    active_grade = read_csv("active_risk_by_grade.csv")
    active_rate = read_csv("active_risk_by_interest_band.csv").dropna(subset=["Delinquency_Rate"])
    active_purpose = read_csv("active_risk_by_purpose.csv")

    c = canvas.Canvas(str(PDF_PATH), pagesize=letter)
    c.setTitle("UCUCI Loan Repayment Analysis Report")

    # Page 1
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 128, PAGE_W, 128, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 25)
    c.drawString(MARGIN, PAGE_H - 58, "UCUCI Bank Loan Repayment Analysis")
    c.setFont(FONT, 15)
    c.drawString(MARGIN, PAGE_H - 86, "Improving loan repayment performance and reducing default exposure")
    y = PAGE_H - 165
    y = heading(c, "Business Context", MARGIN, y)
    y = text(
        c,
        "UCUCI Bank offers retail lending products such as debt consolidation, credit card, home improvement, small business, and personal loans. The bank needs a practical way to understand which borrower and product segments repay well, which segments create default exposure, and which current loans should receive early recovery attention.",
        MARGIN,
        y,
        CONTENT_W,
    )
    y -= 12
    y = heading(c, "Project Objective", MARGIN, y)
    y = text(
        c,
        "The objective is to use historical closed-loan behavior to identify repayment patterns, then apply those patterns to active loans so the bank can intervene before risk turns into charge-off losses.",
        MARGIN,
        y,
        CONTENT_W,
        FONT_BOLD,
    )
    y -= 18
    y = heading(c, "Report Flow", MARGIN, y)
    card_w = (CONTENT_W - 18) / 3
    cards = [
        ("1. Understand", "Data, portfolio split, LRR, default, delinquency, and exposure metrics.", LIGHT_BLUE, BLUE),
        ("2. Learn", "Closed-loan trends show which segments historically repaid weaker.", LIGHT_GREEN, GREEN),
        ("3. Apply", "Active-loan risk is interpreted through the same patterns and exposure logic.", LIGHT_AMBER, AMBER),
    ]
    for i, (head, body, fill, stroke) in enumerate(cards):
        x = MARGIN + i * (card_w + 9)
        rounded_box(c, x, y, card_w, 110, fill, stroke)
        c.setFont(FONT_BOLD, 14)
        c.setFillColor(stroke)
        c.drawString(x + 12, y - 25, head)
        text(c, body, x + 12, y - 48, card_w - 24)
    c.showPage()

    # Page 2
    y = title(c, "Dataset and Metric Framework", "Data foundation")
    y = heading(c, "Dataset Overview", MARGIN, y)
    y = draw_table(
        c,
        MARGIN,
        y,
        [150, CONTENT_W - 150],
        ["Item", "Details"],
        [
            ["Dataset", "UCUCI Bank Loan Dataset"],
            ["Rows and columns", "887,379 rows and 57 columns"],
            ["Loan record quality", "Notebook output confirms no duplicate loan IDs or duplicate member IDs."],
            ["Closed statuses", "Fully Paid, Charged Off, Default"],
            ["Active statuses", "Current, In Grace Period, Late (16-30 days), Late (31-120 days)"],
            ["Evidence base", "Python notebook outputs and Tableau summary files prepared from the same raw dataset."],
        ],
        LIGHT_BLUE,
    )
    y = heading(c, "Key Metrics", MARGIN, y)
    y = draw_table(
        c,
        MARGIN,
        y,
        [150, CONTENT_W - 150],
        ["Metric", "Definition and use"],
        [
            ["Loan Repayment Rate", "SUM(total_pymnt) / SUM(funded_amnt) x 100. Main metric for completed-loan repayment strength."],
            ["Default Rate", "Charged-off loans divided by total loans. Used as the problem statement default view."],
            ["Active Delinquency Rate", "Active loans in grace or late status divided by active loans. Used for live risk monitoring."],
            ["At-Risk Outstanding", "Outstanding principal attached to active delinquent loans. Used for recovery prioritisation."],
        ],
        LIGHT_AMBER,
    )
    y = heading(c, "Data Cleaning Notes", MARGIN, y)
    bullets(
        c,
        [
            "Interest rate was treated as a numeric percentage and loan term was cleaned so 36-month and 60-month loans compare correctly.",
            "DTI analysis focused on practical bands because only 11 records had DTI greater than 100.",
            "Closed loans and active loans were deliberately separated because one explains historical behavior and the other supports current action.",
        ],
        MARGIN,
        y,
        CONTENT_W,
    )
    c.showPage()

    # Page 3
    y = title(c, "Portfolio Snapshot and Analysis Bridge", "Closed loans to active loans")
    y = heading(c, "Portfolio Snapshot", MARGIN, y)
    card_w = (CONTENT_W - 18) / 3
    snapshots = [
        ("Total loans", f"{int(kpi['Total Loans Issued']):,}", LIGHT_BLUE, BLUE),
        ("Closed loans", f"{int(kpi['Closed Loans']):,}", LIGHT_GREEN, GREEN),
        ("Active loans", f"{int(kpi['Active Loans']):,}", LIGHT_AMBER, AMBER),
        ("Completed-loan LRR", f"{kpi['Overall Completed Loan LRR']:.1f}%", LIGHT_GREEN, GREEN),
        ("Active delinquency", f"{kpi['Active Loan Delinquency Rate']:.2f}%", LIGHT_AMBER, AMBER),
        ("At-risk outstanding", f"{kpi['At Risk Outstanding Principal'] / 10_000_000:.1f} Cr", LIGHT_RED, RED),
    ]
    for i, (label, value, fill, stroke) in enumerate(snapshots):
        x = MARGIN + (i % 3) * (card_w + 9)
        yy = y - (i // 3) * 84
        rounded_box(c, x, yy, card_w, 68, fill, stroke)
        c.setFillColor(stroke)
        c.setFont(FONT_BOLD, 17)
        c.drawString(x + 12, yy - 25, value)
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawString(x + 12, yy - 46, label)
    y -= 188
    y = heading(c, "How the Report Uses Closed and Active Loans", MARGIN, y)
    y = text(
        c,
        "Closed loans are the learning set. They reveal which combinations of grade, price, affordability, term, and purpose actually produced weak repayment. Active loans are the action set. Their final outcome is not yet known, so the report uses closed-loan trends to infer which active loans may deteriorate and where recovery effort should begin.",
        MARGIN,
        y,
        CONTENT_W,
    )
    y -= 12
    y = heading(c, "Hypotheses", MARGIN, y)
    draw_table(
        c,
        MARGIN,
        y,
        [54, 248, CONTENT_W - 302],
        ["ID", "Hypothesis", "Decision logic"],
        [
            ["H1", "Lower grades have lower repayment rates.", "Compare completed-loan LRR by grade."],
            ["H2", "Higher interest loans have lower repayment rates.", "Compare completed-loan LRR by interest band."],
            ["H3", "Higher DTI borrowers have lower repayment rates.", "Compare completed-loan LRR by DTI band."],
            ["H4", "Longer terms weaken repayment.", "Compare 36-month and 60-month LRR, then combine with grade."],
            ["H5", "Purpose affects repayment and current exposure.", "Compare closed-loan LRR and active outstanding by purpose."],
            ["H6", "Active loans can be prioritised using closed-loan risk patterns.", "Compare active delinquency and at-risk outstanding across the same risk dimensions."],
        ],
        LIGHT_BLUE,
    )
    c.showPage()

    # Page 4 divider
    c.setFillColor(LIGHT_GREEN)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.rect(0, PAGE_H - 150, PAGE_W, 150, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 25)
    c.drawString(MARGIN, PAGE_H - 70, "Part A: Closed Loan Analysis")
    c.setFont(FONT, 15)
    c.drawString(MARGIN, PAGE_H - 100, "Historical repayment behavior and drivers of completed-loan LRR")
    y = PAGE_H - 205
    text(
        c,
        "This section looks only at loans that have reached a final status. The goal is to identify the historical repayment patterns that UCUCI can use to improve future approvals and to interpret the current active portfolio.",
        MARGIN,
        y,
        CONTENT_W,
        FONT_BOLD,
        14,
        NAVY,
        18,
    )
    c.showPage()

    # Page 5
    y = title(c, "Closed Loans: Credit Grade Drives Repayment", "Historical LRR")
    bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        320,
        by_grade["grade"].tolist(),
        by_grade["LRR"].tolist(),
        "Loan Repayment Rate by Grade",
        80,
        106,
        lrr_color,
    )
    y -= 340
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "LRR is strongest in grades A and B, both above 104%. The trend weakens steadily after grade C and reaches 89.5% in grade G. This confirms that credit grade is a strong historical repayment signal. For business action, lower-grade approvals should need stronger compensating evidence such as lower DTI, shorter term, or stronger income cushion.",
        LIGHT_GREEN,
    )
    c.showPage()

    # Page 6
    y = title(c, "Closed Loans: Pricing Risk", "Historical LRR")
    line_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        350,
        by_rate["Interest Rate Band"].tolist(),
        by_rate["LRR"].tolist(),
        "Loan Repayment Rate by Interest Rate Band",
        78,
        106,
        lrr_color,
    )
    y -= 370
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "Repayment declines as interest rate increases. Loans below 10% interest have 103.7% LRR, but the 25-30% band drops to 82.0%. Higher pricing reflects risk, but it does not fully offset poor repayment behavior in high-rate segments.",
        LIGHT_AMBER,
    )
    c.showPage()

    # Page 7
    y = title(c, "Closed Loans: Affordability Risk", "Historical LRR")
    line_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        350,
        by_dti["DTI Band"].tolist()[:4],
        by_dti["LRR"].tolist()[:4],
        "Loan Repayment Rate by DTI Band",
        88,
        106,
        lrr_color,
    )
    y -= 370
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "DTI is an affordability warning signal. LRR falls from 103.6% in the 0-10 DTI band to 90.4% in the 30-40 band. This means income should not be judged alone; UCUCI should read income together with debt burden and installment size.",
        LIGHT_AMBER,
    )
    c.showPage()

    # Page 8
    y = title(c, "Closed Loans: Tenure Risk", "Historical LRR")
    bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        350,
        by_term["term"].tolist(),
        by_term["LRR"].tolist(),
        "Loan Repayment Rate by Loan Term",
        88,
        106,
        lrr_color,
    )
    y -= 370
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "The 36-month loan group has 103.0% LRR, while the 60-month group drops to 94.6%. Longer tenure increases uncertainty and gives repayment stress more time to appear, so it should be reviewed carefully when paired with weaker borrower characteristics.",
        LIGHT_AMBER,
    )
    c.showPage()

    # Page 9
    y = title(c, "Closed Loans: Combined Grade-Term Risk", "Historical LRR")
    heatmap(c, MARGIN, y, CONTENT_W, 400, by_grade_term)
    y -= 420
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "The combined view is more useful than term alone. A-grade 60-month loans still perform acceptably, but lower-grade 60-month loans are weak. The clearest risk point is G plus 60 months at 88.9% LRR.",
        LIGHT_RED,
    )
    c.showPage()

    # Page 10
    y = title(c, "Closed Loans: Purpose Adds Business Context", "Historical LRR")
    low_purpose = by_purpose.sort_values("LRR").head(8)
    horizontal_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        360,
        low_purpose["purpose"].tolist(),
        low_purpose["LRR"].tolist(),
        "Lowest LRR Loan Purposes",
        lrr_color,
        "%",
    )
    y -= 380
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "Purpose is not as clean a risk signal as grade, but it helps explain business context. Small business loans are the weakest group at 94.8% LRR, followed by moving, medical, other, and vacation. UCUCI should avoid treating all purposes the same when setting review rules or collection messaging.",
        LIGHT_AMBER,
    )
    c.showPage()

    # Page 11 divider
    c.setFillColor(LIGHT_AMBER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(AMBER)
    c.rect(0, PAGE_H - 150, PAGE_W, 150, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 25)
    c.drawString(MARGIN, PAGE_H - 70, "Part B: Active Loan Analysis")
    c.setFont(FONT, 15)
    c.drawString(MARGIN, PAGE_H - 100, "Current delinquency, exposure, and recovery prioritisation")
    y = PAGE_H - 205
    text(
        c,
        "Active loans have not reached their final outcome, so the analysis does not label them as failed. Instead, it uses the patterns learned from closed loans to identify which active segments may behave poorly and where the bank still has time to intervene.",
        MARGIN,
        y,
        CONTENT_W,
        FONT_BOLD,
        14,
        NAVY,
        18,
    )
    c.showPage()

    # Page 12
    y = title(c, "Active Loans: Delinquency Mirrors Historical Risk", "Current risk")
    line_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        350,
        active_grade["grade"].tolist(),
        active_grade["Delinquency_Rate"].tolist(),
        "Active Delinquency Rate by Grade",
        0,
        13,
        delinquency_color,
    )
    y -= 370
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "The active portfolio follows the same grade pattern seen in closed loans. Delinquency rises from 1.0% in grade A to 11.6% in grade G. This supports using grade as a first early-warning filter for live loan monitoring.",
        LIGHT_RED,
    )
    c.showPage()

    # Page 13
    y = title(c, "Active Loans: Pricing Also Signals Live Risk", "Current risk")
    line_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        350,
        active_rate["Interest Rate Band"].tolist(),
        active_rate["Delinquency_Rate"].tolist(),
        "Active Delinquency Rate by Interest Band",
        0,
        12,
        delinquency_color,
    )
    y -= 370
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "Active delinquency rises from 1.1% below 10% interest to 11.2% in the 25-30% interest band. This mirrors the closed-loan LRR pattern: high-rate loans should receive earlier reminders, closer monitoring, and faster collections escalation.",
        LIGHT_RED,
    )
    c.showPage()

    # Page 14
    y = title(c, "Active Loans: Exposure Decides Recovery Priority", "Current risk")
    at_risk = active_grade[["grade", "At_Risk_Outstanding_Crores"]].copy()
    high_cut = at_risk["At_Risk_Outstanding_Crores"].quantile(0.67)
    med_cut = at_risk["At_Risk_Outstanding_Crores"].quantile(0.33)
    bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        225,
        at_risk["grade"].tolist(),
        at_risk["At_Risk_Outstanding_Crores"].tolist(),
        "At-Risk Outstanding Principal by Grade (Cr)",
        0,
        7,
        lambda value: exposure_color(value, high_cut, med_cut),
        "",
    )
    y -= 245
    y = analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "Recovery priority should combine risk with money exposure. Grades C, D, and E hold the largest at-risk outstanding principal: about 6.2 Cr, 5.9 Cr, and 4.6 Cr.",
        LIGHT_RED,
    )
    exposure = active_purpose.sort_values("Outstanding_Crores", ascending=False).head(6)
    max_ex = exposure["Outstanding_Crores"].max()
    horizontal_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        210,
        exposure["purpose"].tolist(),
        exposure["Outstanding_Crores"].tolist(),
        "Top Active Purposes by Outstanding Principal (Cr)",
        lambda value: RED if value >= max_ex * 0.6 else AMBER if value >= max_ex * 0.15 else GREEN,
        "",
    )
    y -= 230
    analysis_box(
        c,
        MARGIN,
        y,
        CONTENT_W,
        "Debt consolidation is the largest active exposure at about 452.8 Cr, followed by credit card loans at about 185.1 Cr. Exposure size decides where losses could become most material.",
        LIGHT_AMBER,
    )
    c.showPage()

    # Page 15
    y = title(c, "Recommendations and Tableau Monitoring Plan", "Business action")
    y = heading(c, "Rule-Based Active Risk Tier", MARGIN, y)
    y = draw_table(
        c,
        MARGIN,
        y,
        [90, 95, 90, 118, 105],
        ["Tier", "Loans", "Share", "Outstanding", "Delinq."],
        [
            ["High", "114,835", "18.46%", "187.79 Cr", "8.96%"],
            ["Medium", "79,825", "12.83%", "80.62 Cr", "12.41%"],
            ["Low", "427,320", "68.70%", "462.92 Cr", "0.00%"],
        ],
        LIGHT_AMBER,
    )
    y = text(c, "The tiering is intentionally simple: it combines grade, DTI, interest, term, and late status so the business can create an explainable collections queue.", MARGIN, y, CONTENT_W)
    y -= 8
    y = heading(c, "Recommended Actions", MARGIN, y)
    y = draw_table(
        c,
        MARGIN,
        y,
        [140, CONTENT_W - 140],
        ["Action", "What UCUCI should do"],
        [
            ["Prioritise recovery", "Start with active delinquent C, D, and E loans sorted by outstanding principal."],
            ["Tighten approvals", "Add extra review for lower grade plus 60-month term, high interest, or high DTI combinations."],
            ["Use affordability checks", "Evaluate income with DTI and installment burden instead of reading income alone."],
            ["Segment by purpose", "Treat small business, house, moving, and renewable energy loans as watch-list purposes for monitoring and communication."],
            ["Operationalise the score", "Use the rule-based risk tier as a daily queue for recovery teams and a weekly portfolio review for managers."],
        ],
        LIGHT_GREEN,
    )
    y = heading(c, "Tableau Monitoring Structure", MARGIN, y)
    y = draw_table(
        c,
        MARGIN,
        y,
        [155, CONTENT_W - 155],
        ["Dashboard", "Purpose"],
        [
            ["Executive Overview", "Track portfolio KPIs: completed-loan LRR, active delinquency, outstanding principal, and at-risk outstanding."],
            ["Closed Loan LRR Drivers", "Explain historical repayment patterns by grade, interest band, DTI band, term, purpose, and grade-term combination."],
            ["Active Risk and Recovery", "Show where current loans need attention using delinquency, exposure, grade, interest, and purpose."],
            ["Story", "Move from portfolio health to historical learning, then active recovery prioritisation and recommendations."],
        ],
        LIGHT_BLUE,
    )
    c.save()


if __name__ == "__main__":
    build_pdf()
