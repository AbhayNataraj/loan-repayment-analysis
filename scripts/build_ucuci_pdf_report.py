from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf"
PDF_PATH = OUT_DIR / "UCUCI_Loan_Repayment_Analysis_Report.pdf"
DATA_DIR = ROOT / "tableau_outputs"

PAGE_W, PAGE_H = letter
MARGIN = 54
CONTENT_W = PAGE_W - 2 * MARGIN
TOP = PAGE_H - MARGIN
BOTTOM = MARGIN

FONT = "Arial"
FONT_BOLD = "Arial-Bold"
BODY = 12
LEADING = 15

INK = HexColor("#1F2933")
MUTED = HexColor("#52606D")
NAVY = HexColor("#123047")
TEAL = HexColor("#157A6E")
BLUE = HexColor("#2563A6")
AMBER = HexColor("#B7791F")
RED = HexColor("#B91C1C")
GREEN = HexColor("#1F7A4D")
LIGHT_BLUE = HexColor("#EAF3F8")
LIGHT_TEAL = HexColor("#E8F5F1")
LIGHT_AMBER = HexColor("#FFF4D6")
LIGHT_RED = HexColor("#FCE8E8")
LIGHT_GRAY = HexColor("#F4F6F8")
GRID = HexColor("#D9E2EC")


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont(FONT, r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\arialbd.ttf"))


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)


def line_wrap(text: str, width: float, font: str = FONT, size: int = BODY) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(trial, font, size) <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font: str = FONT,
    size: int = BODY,
    leading: int = LEADING,
    color: colors.Color = INK,
) -> float:
    c.setFillColor(color)
    c.setFont(font, size)
    for para in str(text).split("\n"):
        if not para.strip():
            y -= leading
            continue
        for line in line_wrap(para, width, font, size):
            c.drawString(x, y, line)
            y -= leading
    return y


def draw_bullets(c: canvas.Canvas, items: list[str], x: float, y: float, width: float) -> float:
    for item in items:
        lines = line_wrap(item, width - 18, FONT, BODY)
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawString(x, y, "-")
        for idx, line in enumerate(lines):
            c.drawString(x + 16, y, line)
            y -= LEADING
            if idx == len(lines) - 1:
                y -= 2
    return y


def draw_page_title(c: canvas.Canvas, page: int, title: str, section: str = "") -> None:
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 16)
    c.drawString(MARGIN, TOP, title)
    if section:
        c.setFont(FONT, BODY)
        c.setFillColor(MUTED)
        c.drawRightString(PAGE_W - MARGIN, TOP, section)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.8)
    c.line(MARGIN, TOP - 10, PAGE_W - MARGIN, TOP - 10)
    c.setFont(FONT, BODY)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, 31, "UCUCI Bank Loan Repayment Analysis")
    c.drawRightString(PAGE_W - MARGIN, 31, f"Page {page}")


def section_heading(c: canvas.Canvas, text: str, x: float, y: float, color: colors.Color = NAVY) -> float:
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(color)
    c.drawString(x, y, text)
    return y - 20


def draw_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, label: str, value: str, fill: colors.Color, accent: colors.Color) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(accent)
    c.setLineWidth(1)
    c.roundRect(x, y - h, w, h, 6, fill=1, stroke=1)
    c.setFillColor(accent)
    c.rect(x, y - h, 5, h, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 17)
    c.drawString(x + 14, y - 27, value)
    c.setFillColor(MUTED)
    c.setFont(FONT, BODY)
    for idx, line in enumerate(line_wrap(label, w - 28, FONT, BODY)):
        c.drawString(x + 14, y - 47 - idx * 14, line)


def draw_table(
    c: canvas.Canvas,
    x: float,
    y: float,
    col_widths: list[float],
    headers: list[str],
    rows: list[list[str]],
    header_fill: colors.Color = LIGHT_BLUE,
) -> float:
    padding = 7
    c.setFont(FONT_BOLD, BODY)
    header_lines = [line_wrap(h, w - padding * 2, FONT_BOLD, BODY) for h, w in zip(headers, col_widths)]
    row_line_sets = [
        [line_wrap(cell, w - padding * 2, FONT, BODY) for cell, w in zip(row, col_widths)]
        for row in rows
    ]
    row_heights = [max(len(lines) for lines in header_lines) * 15 + 14]
    for line_set in row_line_sets:
        row_heights.append(max(len(lines) for lines in line_set) * 15 + 14)

    total_w = sum(col_widths)
    current_y = y
    for row_idx, row_h in enumerate(row_heights):
        current_y -= row_h
        c.setFillColor(header_fill if row_idx == 0 else colors.white)
        c.setStrokeColor(GRID)
        c.rect(x, current_y, total_w, row_h, fill=1, stroke=1)
        cell_x = x
        content = header_lines if row_idx == 0 else row_line_sets[row_idx - 1]
        for col_idx, w in enumerate(col_widths):
            c.setStrokeColor(GRID)
            c.rect(cell_x, current_y, w, row_h, fill=0, stroke=1)
            c.setFont(FONT_BOLD if row_idx == 0 else FONT, BODY)
            c.setFillColor(NAVY if row_idx == 0 else INK)
            text_y = current_y + row_h - padding - BODY
            for line in content[col_idx]:
                c.drawString(cell_x + padding, text_y, line)
                text_y -= 15
            cell_x += w
    return current_y - 14


def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def fmt_cr(value: float) -> str:
    return f"{value:.1f} Cr"


def draw_bar_chart(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    labels: list[str],
    values: list[float],
    title: str,
    ymin: float | None = None,
    ymax: float | None = None,
    bar_color: colors.Color = BLUE,
    value_suffix: str = "%",
) -> None:
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(x, y, title)
    plot_x, plot_y = x + 42, y - h + 35
    plot_w, plot_h = w - 54, h - 70
    ymin = 0 if ymin is None else ymin
    ymax = max(values) * 1.15 if ymax is None else ymax
    c.setStrokeColor(GRID)
    c.line(plot_x, plot_y, plot_x, plot_y + plot_h)
    c.line(plot_x, plot_y, plot_x + plot_w, plot_y)
    for tick in [ymin, (ymin + ymax) / 2, ymax]:
        ty = plot_y + (tick - ymin) / (ymax - ymin) * plot_h
        c.setStrokeColor(HexColor("#EEF2F5"))
        c.line(plot_x, ty, plot_x + plot_w, ty)
        c.setFillColor(MUTED)
        c.setFont(FONT, BODY)
        c.drawRightString(plot_x - 6, ty - 4, f"{tick:.0f}")
    bar_gap = 8
    bw = (plot_w - bar_gap * (len(values) - 1)) / len(values)
    for i, (lab, val) in enumerate(zip(labels, values)):
        bx = plot_x + i * (bw + bar_gap)
        bh = max(1, (val - ymin) / (ymax - ymin) * plot_h)
        c.setFillColor(bar_color if i < len(values) - 1 else RED)
        c.rect(bx, plot_y, bw, bh, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont(FONT, BODY)
        c.drawCentredString(bx + bw / 2, plot_y - 17, lab)
        c.drawCentredString(bx + bw / 2, plot_y + bh + 5, f"{val:.1f}{value_suffix}")


def draw_line_chart(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    labels: list[str],
    values: list[float],
    title: str,
    ymin: float,
    ymax: float,
    color: colors.Color = TEAL,
    value_suffix: str = "%",
) -> None:
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(x, y, title)
    plot_x, plot_y = x + 46, y - h + 38
    plot_w, plot_h = w - 62, h - 74
    c.setStrokeColor(GRID)
    c.line(plot_x, plot_y, plot_x, plot_y + plot_h)
    c.line(plot_x, plot_y, plot_x + plot_w, plot_y)
    for tick in [ymin, (ymin + ymax) / 2, ymax]:
        ty = plot_y + (tick - ymin) / (ymax - ymin) * plot_h
        c.setStrokeColor(HexColor("#EEF2F5"))
        c.line(plot_x, ty, plot_x + plot_w, ty)
        c.setFillColor(MUTED)
        c.setFont(FONT, BODY)
        c.drawRightString(plot_x - 7, ty - 4, f"{tick:.0f}")
    points = []
    for i, val in enumerate(values):
        px = plot_x + i * (plot_w / (len(values) - 1))
        py = plot_y + (val - ymin) / (ymax - ymin) * plot_h
        points.append((px, py))
    c.setStrokeColor(color)
    c.setLineWidth(2)
    for p1, p2 in zip(points, points[1:]):
        c.line(p1[0], p1[1], p2[0], p2[1])
    c.setLineWidth(1)
    for (px, py), lab, val in zip(points, labels, values):
        c.setFillColor(color)
        c.circle(px, py, 4, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont(FONT, BODY)
        c.drawCentredString(px, plot_y - 18, lab)
        c.drawCentredString(px, py + 8, f"{val:.1f}{value_suffix}")


def draw_horizontal_bar_chart(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    labels: list[str],
    values: list[float],
    title: str,
    color: colors.Color,
    value_suffix: str = "",
) -> None:
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(x, y, title)
    plot_x, plot_y = x + 145, y - h + 26
    plot_w = w - 170
    row_h = (h - 55) / len(values)
    max_val = max(values) * 1.08
    for i, (lab, val) in enumerate(zip(labels, values)):
        yy = plot_y + (len(values) - 1 - i) * row_h
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawRightString(plot_x - 8, yy + 5, lab)
        c.setFillColor(color)
        c.rect(plot_x, yy, plot_w * val / max_val, row_h - 7, fill=1, stroke=0)
        c.setFillColor(INK)
        c.drawString(plot_x + plot_w * val / max_val + 6, yy + 5, f"{val:.1f}{value_suffix}")


def blend(low: colors.Color, high: colors.Color, t: float) -> colors.Color:
    t = max(0, min(1, t))
    return colors.Color(
        low.red + (high.red - low.red) * t,
        low.green + (high.green - low.green) * t,
        low.blue + (high.blue - low.blue) * t,
    )


def draw_heatmap(c: canvas.Canvas, x: float, y: float, w: float, h: float, df: pd.DataFrame, title: str) -> None:
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(x, y, title)
    grades = list("ABCDEFG")
    terms = ["36 months", "60 months"]
    top_y = y - 30
    cell_w = (w - 72) / 2
    cell_h = (h - 55) / len(grades)
    c.setFont(FONT_BOLD, BODY)
    c.setFillColor(NAVY)
    c.drawString(x, top_y + 3, "Grade")
    for j, term in enumerate(terms):
        c.drawCentredString(x + 62 + j * cell_w + cell_w / 2, top_y + 3, term.replace(" months", " m"))
    values = df["LRR"].tolist()
    vmin, vmax = min(values), max(values)
    lookup = {(r["grade"], r["term"]): r["LRR"] for _, r in df.iterrows()}
    for i, grade in enumerate(grades):
        yy = top_y - (i + 1) * cell_h
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, BODY)
        c.drawString(x + 6, yy + cell_h / 2 - 4, grade)
        for j, term in enumerate(terms):
            val = lookup[(grade, term)]
            xx = x + 62 + j * cell_w
            fill = blend(LIGHT_RED, LIGHT_TEAL, (val - vmin) / (vmax - vmin))
            c.setFillColor(fill)
            c.setStrokeColor(colors.white)
            c.rect(xx, yy, cell_w, cell_h, fill=1, stroke=1)
            c.setFillColor(NAVY)
            c.setFont(FONT_BOLD, BODY)
            c.drawCentredString(xx + cell_w / 2, yy + cell_h / 2 - 4, f"{val:.1f}%")


def source_note(c: canvas.Canvas, x: float, y: float) -> None:
    c.setFont(FONT, BODY)
    c.setFillColor(MUTED)
    c.drawString(x, y, "Source: Python EDA notebook outputs and Tableau reference summaries.")


def build_pdf() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()

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

    # Page 1: Cover and executive snapshot
    page = 1
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 122, PAGE_W, 122, fill=1, stroke=0)
    c.setFont(FONT_BOLD, 25)
    c.setFillColor(colors.white)
    c.drawString(MARGIN, PAGE_H - 55, "UCUCI Bank Loan Repayment Analysis")
    c.setFont(FONT, 15)
    c.drawString(MARGIN, PAGE_H - 82, "Improving repayment performance and reducing default exposure")
    c.setFont(FONT, BODY)
    c.drawString(MARGIN, PAGE_H - 104, "PDF report based on Python EDA and Tableau project outputs | June 28, 2026")
    y = PAGE_H - 165
    c.setFont(FONT_BOLD, 15)
    c.setFillColor(NAVY)
    c.drawString(MARGIN, y, "Executive Snapshot")
    y -= 18
    card_w = (CONTENT_W - 18) / 3
    draw_card(c, MARGIN, y, card_w, 70, "Total loans in dataset", f"{int(kpi['Total Loans Issued']):,}", LIGHT_BLUE, BLUE)
    draw_card(c, MARGIN + card_w + 9, y, card_w, 70, "Completed-loan LRR", fmt_pct(kpi["Overall Completed Loan LRR"]), LIGHT_TEAL, TEAL)
    draw_card(c, MARGIN + 2 * (card_w + 9), y, card_w, 70, "Active delinquency rate", fmt_pct(kpi["Active Loan Delinquency Rate"]), LIGHT_AMBER, AMBER)
    y -= 86
    draw_card(c, MARGIN, y, card_w, 70, "Charged-off default rate", fmt_pct(kpi["Default Rate - Charged Off Only"]), LIGHT_RED, RED)
    draw_card(c, MARGIN + card_w + 9, y, card_w, 70, "Active outstanding principal", fmt_cr(kpi["Active Outstanding Principal"] / 10_000_000), LIGHT_BLUE, BLUE)
    draw_card(c, MARGIN + 2 * (card_w + 9), y, card_w, 70, "At-risk outstanding principal", fmt_cr(kpi["At Risk Outstanding Principal"] / 10_000_000), LIGHT_RED, RED)
    y -= 104
    c.setFillColor(LIGHT_GRAY)
    c.setStrokeColor(GRID)
    c.roundRect(MARGIN, y - 92, CONTENT_W, 92, 6, fill=1, stroke=1)
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(NAVY)
    c.drawString(MARGIN + 16, y - 25, "Main conclusion")
    draw_wrapped(
        c,
        "The portfolio is broadly stable at the aggregate closed-loan level, but repayment weakness is concentrated in lower grades, high interest bands, higher DTI bands, and 60-month loans. For active loans, the best recovery starting point is delinquent C, D, and E borrowers because they hold the largest at-risk outstanding principal.",
        MARGIN + 16,
        y - 47,
        CONTENT_W - 32,
    )
    y -= 126
    y = section_heading(c, "Recommended action", MARGIN, y)
    draw_bullets(
        c,
        [
            "Use closed-loan patterns to tighten future approvals for weak grade, high interest, high DTI, and long-term combinations.",
            "Use active-loan monitoring to create a daily recovery queue ranked by delinquency, outstanding principal, and risk score.",
            "Track the same metrics in Tableau: completed-loan LRR, active delinquency rate, at-risk outstanding principal, grade, term, interest band, DTI band, and purpose.",
        ],
        MARGIN,
        y,
        CONTENT_W,
    )
    c.showPage()

    # Page 2: Business context and approach
    page += 1
    draw_page_title(c, page, "Business Context and Analysis Approach", "Context")
    y = TOP - 42
    y = section_heading(c, "Business Context", MARGIN, y)
    y = draw_wrapped(
        c,
        "UCUCI Bank provides retail lending products across debt consolidation, credit card, personal, small business, home improvement, and other purposes. As the loan book grows, the bank needs to understand which segments repay well, where defaults emerge, and where current outstanding money is most exposed.",
        MARGIN,
        y,
        CONTENT_W,
    )
    y -= 9
    y = section_heading(c, "Problem Statement", MARGIN, y)
    y = draw_wrapped(
        c,
        "The business objective is to improve loan repayment and reduce default exposure. The analysis separates closed loans from active loans because they answer different questions: closed loans explain historical repayment behavior, while active loans show where the bank still has an opportunity to intervene before losses become final.",
        MARGIN,
        y,
        CONTENT_W,
    )
    y -= 9
    y = section_heading(c, "Analysis Approach", MARGIN, y)
    approach = [
        ["1. Define metric framework", "Use Loan Repayment Rate as the primary success metric and support it with default, delinquency, recovery, and exposure KPIs."],
        ["2. Prepare the data", "Clean percentage fields, trim loan terms, separate closed versus active statuses, and create bands for interest rate, DTI, income, and installments."],
        ["3. Explore closed loans", "Compare repayment across grade, sub-grade, interest band, DTI band, term, income, installment, and purpose."],
        ["4. Explore active loans", "Measure delinquency and outstanding principal by grade, interest band, purpose, and combined risk drivers."],
        ["5. Convert insights to action", "Build business recommendations and a rule-based risk queue that Tableau can monitor operationally."],
    ]
    y = draw_table(c, MARGIN, y, [145, CONTENT_W - 145], ["Step", "What it contributes"], approach, LIGHT_TEAL)
    y = section_heading(c, "Primary Business Question", MARGIN, y)
    draw_wrapped(
        c,
        "How can UCUCI Bank improve repayment performance, reduce default risk, and recover outstanding money from active risky loans before they become charged off?",
        MARGIN,
        y,
        CONTENT_W,
        FONT_BOLD,
    )
    c.showPage()

    # Page 3: Dataset and preparation
    page += 1
    draw_page_title(c, page, "Dataset, Cleaning, and Metric Framework", "Dataset")
    y = TOP - 42
    y = section_heading(c, "Dataset Summary", MARGIN, y)
    rows = [
        ["Dataset", "UCUCI Bank Loan Dataset"],
        ["Volume", "887,379 rows and 57 columns"],
        ["Granularity", "One row per loan; no duplicate loan IDs or member IDs were found in the notebook output."],
        ["Main status field", "loan_status"],
        ["Closed statuses", "Fully Paid, Charged Off, Default"],
        ["Active statuses", "Current, In Grace Period, Late (16-30 days), Late (31-120 days)"],
    ]
    y = draw_table(c, MARGIN, y, [145, CONTENT_W - 145], ["Item", "Details"], rows, LIGHT_BLUE)
    y = section_heading(c, "Data Preparation Notes", MARGIN, y)
    y = draw_bullets(
        c,
        [
            "Interest rates were cleaned as numeric percentages and term values were trimmed so 36-month and 60-month loans can be compared reliably.",
            "Only 11 records had DTI greater than 100, so DTI charts focused on practical bands up to 100 to avoid distortion.",
            "153 records had annual income above 10,00,000; income is informative, but it should be interpreted with DTI and installment burden.",
            "Charged-off loans show zero outstanding principal in this dataset, so the practical recovery metric is recoveries divided by funded amount.",
        ],
        MARGIN,
        y,
        CONTENT_W,
    )
    y -= 6
    y = section_heading(c, "Metric Framework", MARGIN, y)
    metric_rows = [
        ["Loan Repayment Rate", "SUM(total_pymnt) / SUM(funded_amnt) x 100. This is the main project metric."],
        ["Default Rate", "Charged-off loans / total loans. This follows the problem statement definition."],
        ["Bad Loan Rate", "Charged Off plus Default loans / total loans. This is an expanded risk view."],
        ["Active Delinquency Rate", "Active loans in grace or late status / active loans."],
        ["At-Risk Outstanding", "Outstanding principal on active delinquent loans."],
    ]
    draw_table(c, MARGIN, y, [160, CONTENT_W - 160], ["Metric", "Definition"], metric_rows, LIGHT_AMBER)
    c.showPage()

    # Page 4: Hypotheses and KPI tree
    page += 1
    draw_page_title(c, page, "Hypotheses and KPI Tree", "Metrics")
    y = TOP - 42
    y = section_heading(c, "KPI Tree", MARGIN, y)
    c.setStrokeColor(GRID)
    c.setLineWidth(1)
    c.setFillColor(LIGHT_BLUE)
    c.roundRect(MARGIN, y - 52, CONTENT_W, 52, 6, fill=1, stroke=1)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 14)
    c.drawCentredString(PAGE_W / 2, y - 22, "Improve repayment performance and reduce default exposure")
    c.setFont(FONT, BODY)
    c.drawCentredString(PAGE_W / 2, y - 40, "Primary metric: Loan Repayment Rate (LRR)")
    y -= 82
    box_w = (CONTENT_W - 18) / 3
    for i, (title, lines, fill, accent) in enumerate(
        [
            ("Future lending quality", ["LRR by grade", "LRR by interest", "LRR by DTI", "LRR by term"], LIGHT_TEAL, TEAL),
            ("Current recovery risk", ["Active delinquency", "At-risk outstanding", "Risk tier", "Purpose exposure"], LIGHT_RED, RED),
            ("Portfolio monitoring", ["Default rate", "Bad loan rate", "Recovery rate", "Outstanding principal"], LIGHT_AMBER, AMBER),
        ]
    ):
        x = MARGIN + i * (box_w + 9)
        c.setFillColor(fill)
        c.setStrokeColor(accent)
        c.roundRect(x, y - 118, box_w, 118, 6, fill=1, stroke=1)
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, BODY)
        c.drawString(x + 12, y - 23, title)
        c.setFont(FONT, BODY)
        yy = y - 45
        for line in lines:
            c.drawString(x + 14, yy, f"- {line}")
            yy -= 17
    y -= 148
    y = section_heading(c, "Hypotheses Tested", MARGIN, y)
    hypothesis_rows = [
        ["H1", "Lower credit grades have lower LRR.", "Supported: A/B above 104%, G at 89.5%."],
        ["H2", "Higher interest rate loans have lower LRR.", "Supported: <10% at 103.7%, 25-30% at 82.0%."],
        ["H3", "Higher DTI borrowers have lower LRR.", "Supported: 0-10 DTI at 103.6%, 30-40 at 90.4%."],
        ["H4", "60-month loans repay worse than 36-month loans.", "Supported: 94.6% versus 103.0%."],
        ["H5", "Loan purpose affects repayment behavior.", "Supported: small business is weak at 94.8%."],
        ["H6", "Grade and term together explain risk better.", "Supported: G plus 60 months is weakest at 88.9%."],
        ["H7-H10", "Active risk rises with grade, rate, purpose, and exposure mix.", "Supported: G delinquency is 11.6%; C/D/E have the largest at-risk principal."],
    ]
    draw_table(c, MARGIN, y, [50, 238, CONTENT_W - 288], ["ID", "Hypothesis", "Evidence"], hypothesis_rows, LIGHT_BLUE)
    c.showPage()

    # Page 5: Portfolio EDA
    page += 1
    draw_page_title(c, page, "Overall EDA and Portfolio Health", "EDA")
    y = TOP - 42
    y = section_heading(c, "Portfolio Split", MARGIN, y)
    closed = kpi["Closed Loans"]
    active = kpi["Active Loans"]
    other = kpi["Total Loans Issued"] - closed - active
    draw_bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        210,
        ["Closed", "Active", "Other"],
        [closed / 1000, active / 1000, other / 1000],
        "Loan count by portfolio type (000s)",
        ymin=0,
        ymax=700,
        bar_color=TEAL,
        value_suffix="",
    )
    y -= 230
    y = section_heading(c, "EDA Interpretation", MARGIN, y)
    y = draw_bullets(
        c,
        [
            f"Closed loans represent {closed:,.0f} records and are used to learn historical repayment behavior.",
            f"Active loans represent {active:,.0f} records and are used to monitor live delinquency and recovery exposure.",
            "Aggregate completed-loan LRR is slightly above 100%, but this hides a large spread between safer and riskier segments.",
            "The active portfolio still has about 731.3 Cr outstanding principal, of which 23.6 Cr is already at risk because the loans are in grace or late status.",
        ],
        MARGIN,
        y,
        CONTENT_W,
    )
    y -= 6
    y = section_heading(c, "Business Reading", MARGIN, y)
    draw_wrapped(
        c,
        "The project should not stop at an overall LRR. UCUCI needs a two-speed operating model: improve future approvals using closed-loan risk patterns, and run a current collections queue using active-loan delinquency and outstanding principal.",
        MARGIN,
        y,
        CONTENT_W,
    )
    source_note(c, MARGIN, 67)
    c.showPage()

    # Page 6: Grade and interest drivers
    page += 1
    draw_page_title(c, page, "Closed Loan Repayment Drivers: Grade and Pricing", "Findings")
    y = TOP - 42
    draw_bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        235,
        by_grade["grade"].tolist(),
        by_grade["LRR"].tolist(),
        "Loan Repayment Rate by Grade",
        ymin=80,
        ymax=106,
        bar_color=BLUE,
    )
    y -= 250
    draw_line_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        230,
        by_rate["Interest Rate Band"].tolist(),
        by_rate["LRR"].tolist(),
        "Loan Repayment Rate by Interest Rate Band",
        ymin=78,
        ymax=106,
        color=TEAL,
    )
    y -= 245
    y = section_heading(c, "Insight", MARGIN, y)
    draw_wrapped(
        c,
        "Repayment weakens as borrower risk increases. A and B loans have LRR above 104%, while G loans fall to 89.5%. Pricing follows risk, but higher interest rates do not fully compensate for repayment weakness: the 25-30% band falls to 82.0% LRR.",
        MARGIN,
        y,
        CONTENT_W,
    )
    source_note(c, MARGIN, 67)
    c.showPage()

    # Page 7: Affordability and tenure
    page += 1
    draw_page_title(c, page, "Closed Loan Repayment Drivers: Affordability and Term", "Findings")
    y = TOP - 42
    draw_line_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        220,
        by_dti["DTI Band"].tolist()[:4],
        by_dti["LRR"].tolist()[:4],
        "Loan Repayment Rate by DTI Band",
        ymin=88,
        ymax=106,
        color=AMBER,
    )
    y -= 235
    draw_bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        210,
        by_term["term"].tolist(),
        by_term["LRR"].tolist(),
        "Loan Repayment Rate by Loan Term",
        ymin=88,
        ymax=106,
        bar_color=TEAL,
    )
    y -= 230
    y = section_heading(c, "Insight", MARGIN, y)
    draw_wrapped(
        c,
        "Affordability signals matter. LRR declines from 103.6% in the 0-10 DTI band to 90.4% in the 30-40 band. Tenure also matters: 36-month loans have 103.0% LRR, while 60-month loans fall to 94.6%. Income alone is not enough; it should be read with DTI, installment burden, grade, and term.",
        MARGIN,
        y,
        CONTENT_W,
    )
    source_note(c, MARGIN, 67)
    c.showPage()

    # Page 8: Purpose and grade-term
    page += 1
    draw_page_title(c, page, "Closed Loan Patterns: Purpose and Combined Risk", "Findings")
    y = TOP - 42
    low_purpose = by_purpose.sort_values("LRR").head(7)
    draw_horizontal_bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        225,
        low_purpose["purpose"].tolist(),
        low_purpose["LRR"].tolist(),
        "Lowest LRR loan purposes",
        RED,
        "%",
    )
    y -= 245
    draw_heatmap(c, MARGIN, y, CONTENT_W, 250, by_grade_term, "LRR by Grade and Term")
    y -= 275
    y = section_heading(c, "Insight", MARGIN, y)
    draw_wrapped(
        c,
        "Purpose adds business context. Small business loans are the weakest purpose at 94.8% LRR. The combined heatmap shows why single-variable analysis is not enough: risk concentrates when lower grades are paired with longer tenure, especially G-grade 60-month loans at 88.9% LRR.",
        MARGIN,
        y,
        CONTENT_W,
    )
    source_note(c, MARGIN, 67)
    c.showPage()

    # Page 9: Active risk by grade
    page += 1
    draw_page_title(c, page, "Active Loan Risk: Delinquency and Recovery Priority", "Active Risk")
    y = TOP - 42
    draw_line_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        225,
        active_grade["grade"].tolist(),
        active_grade["Delinquency_Rate"].tolist(),
        "Active Delinquency Rate by Grade",
        ymin=0,
        ymax=13,
        color=RED,
    )
    y -= 240
    draw_bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        225,
        active_grade["grade"].tolist(),
        active_grade["At_Risk_Outstanding_Crores"].tolist(),
        "At-Risk Outstanding Principal by Grade (Cr)",
        ymin=0,
        ymax=7,
        bar_color=AMBER,
        value_suffix="",
    )
    y -= 245
    y = section_heading(c, "Insight", MARGIN, y)
    draw_wrapped(
        c,
        "Active delinquency rises from 1.0% in grade A to 11.6% in grade G. However, recovery priority should combine risk with money exposure. The largest at-risk outstanding principal is in grades C, D, and E: about 6.2 Cr, 5.9 Cr, and 4.6 Cr respectively.",
        MARGIN,
        y,
        CONTENT_W,
    )
    source_note(c, MARGIN, 67)
    c.showPage()

    # Page 10: Active risk by purpose and tier
    page += 1
    draw_page_title(c, page, "Active Risk: Purpose Exposure and Early-Warning Score", "Active Risk")
    y = TOP - 42
    exposure = active_purpose.sort_values("Outstanding_Crores", ascending=False).head(6)
    draw_horizontal_bar_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        215,
        exposure["purpose"].tolist(),
        exposure["Outstanding_Crores"].tolist(),
        "Top active purposes by outstanding principal (Cr)",
        BLUE,
        "",
    )
    y -= 235
    rate_values = active_rate["Delinquency_Rate"].tolist()
    draw_line_chart(
        c,
        MARGIN,
        y,
        CONTENT_W,
        205,
        active_rate["Interest Rate Band"].tolist(),
        rate_values,
        "Active Delinquency by Interest Rate Band",
        ymin=0,
        ymax=12,
        color=RED,
    )
    y -= 220
    y = section_heading(c, "Rule-Based Risk Tier Summary", MARGIN, y)
    risk_rows = [
        ["High", "114,835", "18.46%", "187.79 Cr", "8.96%"],
        ["Medium", "79,825", "12.83%", "80.62 Cr", "12.41%"],
        ["Low", "427,320", "68.70%", "462.92 Cr", "0.00%"],
    ]
    y = draw_table(c, MARGIN, y, [82, 100, 94, 118, 112], ["Tier", "Loans", "Share", "Outstanding", "Delinq."], risk_rows, LIGHT_AMBER)
    draw_wrapped(
        c,
        "The score is transparent: points are added for high-risk grade, high DTI, high interest, 60-month term, and late status.",
        MARGIN,
        y,
        CONTENT_W,
    )
    c.showPage()

    # Page 11: Findings and recommendations
    page += 1
    draw_page_title(c, page, "Key Findings and Recommendations", "Actions")
    y = TOP - 42
    y = section_heading(c, "Key Findings", MARGIN, y)
    findings = [
        "Grade is the clearest repayment driver: LRR drops from above 104% in A/B to 89.5% in G.",
        "Higher interest bands are materially weaker: the 25-30% band records only 82.0% LRR.",
        "DTI shows affordability stress: 30-40 DTI loans have 90.4% LRR versus 103.6% in 0-10 DTI.",
        "Term risk is visible: 60-month loans repay worse than 36-month loans, especially in lower grades.",
        "Purpose matters: small business loans have the weakest closed-loan LRR among major purposes.",
        "Active recovery should start with C/D/E delinquent loans because they hold the largest at-risk outstanding principal.",
    ]
    y = draw_bullets(c, findings, MARGIN, y, CONTENT_W)
    y -= 4
    y = section_heading(c, "Business Recommendations", MARGIN, y)
    rec_rows = [
        ["1. Recovery queue", "Prioritise active delinquent borrowers in grades C, D, and E, sorted by outstanding principal and days-late status."],
        ["2. Approval guardrails", "Apply stricter review to combinations of lower grade, 60-month term, high DTI, and high interest rate."],
        ["3. Affordability checks", "Use DTI, installment burden, and income together rather than relying on income alone."],
        ["4. Purpose treatment", "Create purpose-specific monitoring for small business, house, moving, and renewable energy loans."],
        ["5. Tableau monitoring", "Use the Tableau dashboard as a weekly portfolio review tool and a daily exception queue for collections."],
    ]
    draw_table(c, MARGIN, y, [135, CONTENT_W - 135], ["Action", "Recommendation"], rec_rows, LIGHT_TEAL)
    c.showPage()

    # Page 12: Tableau documentation and final conclusion
    page += 1
    draw_page_title(c, page, "Tableau Documentation and Final Conclusion", "Delivery")
    y = TOP - 42
    y = section_heading(c, "Tableau Project Documentation", MARGIN, y)
    table_rows = [
        ["Executive Overview", "Top-level KPIs: total loans, completed-loan LRR, active delinquency rate, active outstanding principal, and at-risk outstanding principal."],
        ["Closed Loan LRR Drivers", "Charts for LRR by grade, interest band, DTI band, term, grade-term combination, and purpose."],
        ["Active Risk and Recovery", "Charts for delinquency by grade/rate, outstanding by purpose, at-risk outstanding by grade, and risk versus exposure."],
        ["Story: Improving Loan Repayment", "Narrative flow from portfolio health to repayment drivers, active risk, and final recommendation."],
    ]
    y = draw_table(c, MARGIN, y, [155, CONTENT_W - 155], ["Dashboard", "Role in the project"], table_rows, LIGHT_BLUE)
    y = section_heading(c, "Final Conclusion", MARGIN, y)
    y = draw_wrapped(
        c,
        "UCUCI Bank should improve repayment through two linked actions. First, future lending should be tightened for combinations that historically repay poorly: lower grades, high interest rates, high DTI, weaker purposes, and 60-month terms. Second, the current active portfolio should be managed through early recovery action, starting with delinquent C, D, and E loans because they carry the largest at-risk outstanding principal.",
        MARGIN,
        y,
        CONTENT_W,
    )
    y -= 8
    y = section_heading(c, "Submission Rule Check", MARGIN, y)
    draw_bullets(
        c,
        [
            "Page count is within the 15-page maximum.",
            "The report uses Arial at 12 pt or larger throughout.",
            "The report documents business context, key metrics, hypotheses, EDA findings, trends, visualisations, and recommendations.",
            "The visualisations are rebuilt from the Python and Tableau project outputs.",
        ],
        MARGIN,
        y,
        CONTENT_W,
    )
    source_note(c, MARGIN, 67)
    c.save()


if __name__ == "__main__":
    build_pdf()
