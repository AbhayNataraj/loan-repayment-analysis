from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageChops
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "UCUCI_Loan_Repayment_Analysis_Report.pdf"
DATA = ROOT / "tableau_outputs"
TABLEAU = ROOT / "tmp" / "pdfs" / "tableau_attach_render"
CROP = ROOT / "tmp" / "pdfs" / "report_v4_crops"
DASH = ROOT / "assets" / "tableau_dashboards"
CLIP1 = DASH / "portfolio_health.png"
CLIP2 = DASH / "closed_repayment_drivers.png"
CLIP3 = DASH / "active_risk_recovery.png"

PAGE_W, PAGE_H = letter
M = 54
TOP = PAGE_H - 54
BOTTOM = 44
W = PAGE_W - 2 * M

FONT = "Arial"
BOLD = "Arial-Bold"
BODY = 12
LEAD = 15.2

INK = HexColor("#1F2933")
MUTED = HexColor("#5B6770")
NAVY = HexColor("#102A43")
RULE = HexColor("#D9E2EC")
GREEN = HexColor("#1F7A4D")
AMBER = HexColor("#B7791F")
RED = HexColor("#B91C1C")
BLUE = HexColor("#2563A6")
PALE_BLUE = HexColor("#EAF3F8")
PALE_GREEN = HexColor("#E7F5EE")
PALE_AMBER = HexColor("#FFF4D6")
PALE_RED = HexColor("#FCE8E8")


def setup() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    CROP.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont(FONT, r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont(BOLD, r"C:\Windows\Fonts\arialbd.ttf"))


def csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


def crop(src: Path, name: str, pad: int = 20) -> Path:
    dst = CROP / name
    im = Image.open(src).convert("RGB")
    diff = ImageChops.difference(im, Image.new("RGB", im.size, "white"))
    bbox = diff.getbbox()
    if bbox:
        l, t, r, b = bbox
        im = im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))
    im.save(dst)
    return dst


def panel(src: Path, name: str, box: tuple[int, int, int, int], pad: int = 8) -> Path:
    dst = CROP / name
    im = Image.open(src).convert("RGB")
    l, t, r, b = box
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(im.width, r + pad), min(im.height, b + pad)
    im.crop((l, t, r, b)).save(dst)
    return dst


def prepare_panels() -> dict[str, Path]:
    return {
        "kpi_row": panel(CLIP1, "kpi_row.png", (14, 49, 1186, 163), 6),
        "portfolio_mix": panel(CLIP1, "portfolio_mix.png", (8, 202, 474, 482), 5),
        "at_risk_overview": panel(CLIP1, "at_risk_overview.png", (488, 202, 951, 482), 5),
        "subgrade_scatter": panel(CLIP1, "subgrade_scatter.png", (8, 504, 951, 685), 5),
        "closed_grade": panel(CLIP2, "closed_grade.png", (13, 63, 493, 268), 6),
        "closed_income_dti": panel(CLIP2, "closed_income_dti.png", (528, 63, 1008, 268), 6),
        "closed_public_records": panel(CLIP2, "closed_public_records.png", (13, 282, 493, 472), 6),
        "closed_grade_term": panel(CLIP2, "closed_grade_term.png", (528, 282, 1008, 472), 6),
        "closed_interest": panel(CLIP2, "closed_interest.png", (13, 493, 494, 682), 6),
        "active_grade": panel(CLIP3, "active_grade.png", (12, 61, 337, 342), 6),
        "active_recency": panel(CLIP3, "active_recency.png", (367, 61, 692, 342), 6),
        "active_utilization": panel(CLIP3, "active_utilization.png", (718, 61, 1020, 342), 6),
        "active_purpose_exposure": panel(CLIP3, "active_purpose_exposure.png", (12, 361, 337, 642), 6),
        "active_scatter": panel(CLIP3, "active_scatter.png", (367, 361, 692, 642), 6),
        "active_inquiries": panel(CLIP3, "active_inquiries.png", (718, 361, 1020, 642), 6),
    }


def wrap(s: str, width: float, font: str = FONT, size: int = BODY) -> list[str]:
    words = str(s).split()
    out, line = [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if not line or pdfmetrics.stringWidth(trial, font, size) <= width:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def text(c: canvas.Canvas, s: str, x: float, y: float, width: float, font: str = FONT, size: int = BODY, color=INK, lead=LEAD) -> float:
    c.setFont(font, size)
    c.setFillColor(color)
    for para in str(s).split("\n"):
        if not para.strip():
            y -= lead
            continue
        for line in wrap(para, width, font, size):
            c.drawString(x, y, line)
            y -= lead
    return y


def h1(c: canvas.Canvas, s: str, eyebrow: str | None = None) -> float:
    y = TOP
    if eyebrow:
        c.setFont(BOLD, BODY)
        c.setFillColor(MUTED)
        c.drawString(M, y, eyebrow.upper())
        y -= 18
    c.setFont(BOLD, 18)
    c.setFillColor(NAVY)
    c.drawString(M, y, s)
    c.setStrokeColor(RULE)
    c.line(M, y - 11, PAGE_W - M, y - 11)
    return y - 35


def h2(c: canvas.Canvas, s: str, y: float) -> float:
    c.setFont(BOLD, 14)
    c.setFillColor(NAVY)
    c.drawString(M, y, s)
    return y - 21


def bullets(c: canvas.Canvas, items: list[str], y: float, x: float = M, width: float = W) -> float:
    c.setFont(FONT, BODY)
    c.setFillColor(INK)
    for item in items:
        lines = wrap(item, width - 16)
        c.drawString(x, y, "-")
        for line in lines:
            c.drawString(x + 15, y, line)
            y -= LEAD
        y -= 1
    return y


def table(c: canvas.Canvas, y: float, widths: list[float], rows: list[list[str]], fill=PALE_BLUE) -> float:
    pad = 7
    x = M
    for ridx, row in enumerate(rows):
        font = BOLD if ridx == 0 else FONT
        cells = [wrap(cell, w - 2 * pad, font, BODY) for cell, w in zip(row, widths)]
        rh = max(len(v) for v in cells) * 15 + 14
        y -= rh
        if ridx == 0:
            c.setFillColor(fill)
            c.rect(x, y, sum(widths), rh, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.line(x, y, x + sum(widths), y)
        c.line(x, y + rh, x + sum(widths), y + rh)
        cx = x
        for w, lines in zip(widths, cells):
            c.setFont(font, BODY)
            c.setFillColor(NAVY if ridx == 0 else INK)
            ty = y + rh - pad - BODY
            for line in lines:
                c.drawString(cx + pad, ty, line)
                ty -= 15
            cx += w
    return y - 18


def analysis(c: canvas.Canvas, y: float, label: str, s: str) -> float:
    c.setFont(BOLD, BODY)
    c.setFillColor(NAVY)
    c.drawString(M, y, f"Analysis - {label}:")
    return text(c, s, M, y - 18, W)


def lrr_color(v: float):
    return GREEN if v >= 100 else AMBER if v >= 95 else RED


def delinquency_color(v: float):
    return GREEN if v <= 3 else AMBER if v <= 6 else RED


def bar_chart(c: canvas.Canvas, x: float, y: float, w: float, h: float, labels, values, title: str, ymin: float, ymax: float, color_fn, suffix="%") -> None:
    c.setFont(BOLD, 13)
    c.setFillColor(NAVY)
    c.drawString(x, y, title)
    px, py = x + 42, y - h + 34
    pw, ph = w - 56, h - 64
    c.setStrokeColor(RULE)
    c.line(px, py, px, py + ph)
    c.line(px, py, px + pw, py)
    for tick in [ymin, (ymin + ymax) / 2, ymax]:
        ty = py + (tick - ymin) / (ymax - ymin) * ph
        c.setStrokeColor(HexColor("#EEF2F5"))
        c.line(px, ty, px + pw, ty)
        c.setFont(FONT, BODY)
        c.setFillColor(MUTED)
        c.drawRightString(px - 6, ty - 4, f"{tick:.0f}")
    gap = 8
    bw = (pw - gap * (len(values) - 1)) / len(values)
    for i, (lab, val) in enumerate(zip(labels, values)):
        bx = px + i * (bw + gap)
        bh = max(1, (val - ymin) / (ymax - ymin) * ph)
        c.setFillColor(color_fn(float(val)))
        c.rect(bx, py, bw, bh, fill=1, stroke=0)
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawCentredString(bx + bw / 2, py - 17, str(lab))
        c.drawCentredString(bx + bw / 2, py + bh + 5, f"{float(val):.1f}{suffix}")


def line_chart(c: canvas.Canvas, x: float, y: float, w: float, h: float, labels, values, title: str, ymin: float, ymax: float, color_fn, suffix="%") -> None:
    c.setFont(BOLD, 13)
    c.setFillColor(NAVY)
    c.drawString(x, y, title)
    px, py = x + 48, y - h + 36
    pw, ph = w - 66, h - 68
    c.setStrokeColor(RULE)
    c.line(px, py, px, py + ph)
    c.line(px, py, px + pw, py)
    for tick in [ymin, (ymin + ymax) / 2, ymax]:
        ty = py + (tick - ymin) / (ymax - ymin) * ph
        c.setStrokeColor(HexColor("#EEF2F5"))
        c.line(px, ty, px + pw, ty)
        c.setFont(FONT, BODY)
        c.setFillColor(MUTED)
        c.drawRightString(px - 7, ty - 4, f"{tick:.0f}")
    pts = [(px + i * pw / (len(values) - 1), py + (float(v) - ymin) / (ymax - ymin) * ph) for i, v in enumerate(values)]
    c.setStrokeColor(BLUE)
    c.setLineWidth(1.8)
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1])
    c.setLineWidth(1)
    for (cx, cy), lab, val in zip(pts, labels, values):
        c.setFillColor(color_fn(float(val)))
        c.circle(cx, cy, 4.5, fill=1, stroke=0)
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawCentredString(cx, py - 18, str(lab))
        c.drawCentredString(cx, cy + 8, f"{float(val):.1f}{suffix}")


def hbar(c: canvas.Canvas, x: float, y: float, w: float, h: float, labels, values, title: str, color_fn, suffix="") -> None:
    c.setFont(BOLD, 13)
    c.setFillColor(NAVY)
    c.drawString(x, y, title)
    px, py = x + 145, y - h + 30
    pw = w - 170
    row_h = (h - 58) / len(values)
    max_v = max(values) * 1.08
    for idx, (lab, val) in enumerate(zip(labels, values)):
        yy = py + (len(values) - 1 - idx) * row_h
        c.setFont(FONT, BODY)
        c.setFillColor(INK)
        c.drawRightString(px - 8, yy + 5, str(lab))
        c.setFillColor(color_fn(float(val)))
        c.rect(px, yy, pw * float(val) / max_v, row_h - 7, fill=1, stroke=0)
        c.setFillColor(INK)
        c.drawString(px + pw * float(val) / max_v + 6, yy + 5, f"{float(val):.1f}{suffix}")


def image_fit(c: canvas.Canvas, path: Path, y: float, max_h: float) -> float:
    im = Image.open(path)
    scale = min(W / im.width, max_h / im.height)
    dw, dh = im.width * scale, im.height * scale
    x = M + (W - dw) / 2
    c.drawImage(ImageReader(im), x, y - dh, dw, dh, preserveAspectRatio=True, mask="auto")
    c.setStrokeColor(RULE)
    c.rect(x, y - dh, dw, dh, fill=0, stroke=1)
    return y - dh - 18


def image_at(c: canvas.Canvas, path: Path, x: float, y: float, w: float, max_h: float, border: bool = True) -> float:
    im = Image.open(path)
    scale = min(w / im.width, max_h / im.height)
    dw, dh = im.width * scale, im.height * scale
    dx = x + (w - dw) / 2
    c.drawImage(ImageReader(im), dx, y - dh, dw, dh, preserveAspectRatio=True, mask="auto")
    if border:
        c.setStrokeColor(RULE)
        c.rect(dx, y - dh, dw, dh, fill=0, stroke=1)
    return y - dh - 18


def build() -> None:
    setup()
    panels = prepare_panels()
    kpis = dict(zip(csv("dashboard_kpi_reference.csv")["Metric"], csv("dashboard_kpi_reference.csv")["Value"]))
    grade = csv("closed_lrr_by_grade.csv")
    rate = csv("closed_lrr_by_interest_band.csv").dropna(subset=["LRR"])
    dti = csv("closed_lrr_by_dti_band.csv").dropna(subset=["LRR"]).iloc[:4]
    term = csv("closed_lrr_by_term.csv")
    purpose = csv("closed_lrr_by_purpose.csv").sort_values("LRR").head(7)
    gt = csv("closed_lrr_by_grade_term.csv")
    active_grade = csv("active_risk_by_grade.csv")
    active_rate = csv("active_risk_by_interest_band.csv").dropna(subset=["Delinquency_Rate"])
    active_purpose = csv("active_risk_by_purpose.csv").sort_values("Outstanding_Crores", ascending=False).head(6)

    dash1 = crop(CLIP1, "portfolio_dashboard.png")
    dash2 = crop(CLIP2, "closed_dashboard.png")
    dash3 = crop(CLIP3, "active_dashboard.png")

    c = canvas.Canvas(str(OUT), pagesize=letter, initialFontName=FONT, initialFontSize=BODY, initialLeading=LEAD)
    c.setTitle("UCUCI Loan Repayment Analysis Report")

    # 1
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 118, PAGE_W, 118, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(BOLD, 25)
    c.drawString(M, PAGE_H - 54, "UCUCI Bank Loan Repayment Analysis")
    c.setFont(FONT, 15)
    c.drawString(M, PAGE_H - 82, "Improving repayment performance and reducing default exposure")
    y = PAGE_H - 155
    y = h2(c, "Problem Statement", y)
    y = text(c, "UCUCI Bank has a large retail loan portfolio covering debt consolidation, credit card, home improvement, small business, personal, and other loan purposes. While the portfolio-level repayment rate looks healthy, defaults and delinquency are not evenly distributed. Some borrower segments repay consistently, while others create avoidable credit loss and recovery pressure.", M, y, W)
    y -= 10
    y = text(c, "The business problem is to identify which loan characteristics are linked with weak repayment, then use those patterns to improve future lending decisions and prioritise recovery for active loans before they become charged off.", M, y, W, BOLD)
    y -= 16
    y = h2(c, "Business Objective", y)
    y = bullets(c, [
        "Find the main drivers of completed-loan repayment rate across grade, interest rate, DTI, term, purpose, and combined risk groups.",
        "Use completed-loan behaviour to infer which active loans are more likely to become repayment problems.",
        "Recommend practical policy and recovery actions that can improve repayment performance and reduce default exposure."
    ], y)
    c.showPage()

    # 2
    y = h1(c, "Dataset and Metric Setup")
    y = h2(c, "Dataset overview", y)
    y = table(c, y, [150, W - 150], [
        ["Item", "Details"],
        ["Dataset", "UCUCI Bank Loan Dataset"],
        ["Shape", "887,379 rows and 57 columns"],
        ["Loan record check", "No duplicate loan IDs and no duplicate member IDs were found."],
        ["Main status field", "loan_status"],
        ["Closed loans", "Fully Paid, Charged Off, Default"],
        ["Active loans", "Current, In Grace Period, Late (16-30 days), Late (31-120 days)"],
    ])
    y -= 12
    y = h2(c, "Key metrics", y)
    y = table(c, y, [160, W - 160], [
        ["Metric", "Meaning"],
        ["Loan Repayment Rate", "Total amount repaid divided by total funded amount. LRR can be above 100% because repayments include interest and fees in addition to principal."],
        ["Default Rate", "Charged-off loans divided by total loans."],
        ["Active Delinquency Rate", "Active loans in grace or late status divided by active loans."],
        ["At-Risk Outstanding", "Outstanding principal on active delinquent loans."],
        ["Practical Recovery Rate", "Recoveries divided by funded amount for charged-off loans. This KPI only explains post-charge-off recovery, not normal repayment."],
    ])
    y -= 8
    y = h2(c, "Preparation notes", y)
    bullets(c, [
        "Interest rate, term, issue date, and last payment date were cleaned into comparable numeric or banded fields.",
        "Closed loans and active loans were separated so completed repayment outcomes and live intervention risk are not mixed.",
        "LRR uses SUM(total_pymnt) / SUM(funded_amnt). Practical recovery rate uses recoveries / funded amount only for charged-off loans, because charged-off loans have zero outstanding principal in this dataset."
    ], y)
    c.showPage()

    # 3
    y = h1(c, "Portfolio Health Snapshot")
    y = image_at(c, panels["kpi_row"], M, y, W, 92)
    col_w = (W - 16) / 2
    top_y = y - 18
    image_at(c, panels["portfolio_mix"], M, top_y, col_w, 180)
    image_at(c, panels["at_risk_overview"], M + col_w + 16, top_y, col_w, 180)
    y = top_y - 230
    y = analysis(c, y, "portfolio health", "The portfolio has 887,379 loans and completed-loan LRR of 100.3%. LRR is above 100% because borrowers repay principal plus interest and other repayment components. However, the default rate is 5.08%, recovery rate on charged-off loans is only 6.1%, and at-risk outstanding principal is concentrated in grades C, D, and E.")
    y -= 8
    analysis(c, y, "business implication", "The headline repayment rate is useful, but it should not hide segment risk. UCUCI should protect the current portfolio by prioritising recovery where at-risk outstanding principal is highest, while using the closed-loan patterns to tighten future approvals.")
    c.showPage()

    # 4
    y = h1(c, "EDA Approach and Hypotheses")
    y = text(c, "The analysis tests whether repayment behaviour is explained by borrower quality, pricing, affordability, loan structure, and loan purpose. The same logic is then applied to active loans to decide where risk is building.", M, y, W)
    y -= 16
    y = h2(c, "EDA steps taken", y)
    y = bullets(c, [
        "Validated loan count, duplicate IDs, status groups, and the fields needed for repayment, delinquency, exposure, and recovery metrics.",
        "Created closed-loan views for grade, sub-grade, interest rate, DTI, income, term, public records, purpose, and combined grade-term risk.",
        "Created active-loan views for delinquency, outstanding principal, last-payment recency, revolving utilization, recent inquiries, purpose exposure, and operational risk tiers."
    ], y)
    y -= 8
    y = h2(c, "Hypotheses used in the report", y)
    table(c, y, [W / 2, W / 2], [
        ["Closed-loan hypotheses", "Active-loan hypotheses"],
        ["Lower credit grades should show weaker LRR.", "Lower grades should show higher active delinquency."],
        ["Higher interest rates should reduce repayment performance.", "High revolving utilization should signal repayment pressure."],
        ["Low income with high DTI should weaken affordability.", "Recent credit inquiries should indicate rising credit stress."],
        ["Public records and 60-month terms should reduce repayment.", "Stale last payments should increase recovery urgency."],
        ["Purpose, sub-grade, and loan age should add risk detail.", "Recovery priority should combine delinquency, exposure, recency, utilization, and inquiries."],
    ])
    c.showPage()

    # 5
    y = h1(c, "Closed Loans: Grade and Interest")
    y = image_at(c, panels["closed_grade"], M, y, W, 230)
    y = analysis(c, y, "hypothesis assumed", "Lower grades should have lower repayment rates because grade captures borrower credit quality. Result: A and B loans are above 104% LRR, while G falls to 89.5%, so grade remains the clearest historical repayment signal.")
    y -= 8
    y = image_at(c, panels["closed_interest"], M, y, W, 150)
    analysis(c, y, "hypothesis assumed", "Higher interest should indicate greater borrower risk and repayment burden. Result: loans below 10% interest have 103.7% LRR, while the 25-30% band drops to 82.0%; higher pricing alone is not enough to offset high-risk lending.")
    c.showPage()

    # 6
    y = h1(c, "Closed Loans: Affordability and Records")
    y = image_at(c, panels["closed_public_records"], M, y, W, 210)
    y = analysis(c, y, "hypothesis assumed", "Borrowers with public records should repay worse because prior credit events indicate financial stress. Result: LRR declines from 100.7% for borrowers with no public record to about 94.4%-94.8% once records appear.")
    y -= 8
    y = image_at(c, panels["closed_income_dti"], M, y, W, 170)
    analysis(c, y, "hypothesis assumed", "High DTI should be more dangerous when income is low because less repayment capacity is available. Result: borrowers earning <=25K in the 30-40 DTI band show 86.4% LRR, while stronger-income groups generally repay better at the same DTI level.")
    c.showPage()

    # 7
    y = h1(c, "Closed Loans: Purpose and Combined Risk")
    hbar(c, M, y, W, 250, purpose["purpose"], purpose["LRR"], "Weakest Purpose Segments by LRR", lrr_color, "%")
    y -= 268
    y = analysis(c, y, "hypothesis assumed", "Loan purpose can indicate different borrower intent and risk context. Result: small business, moving, medical, and other loans are among the weaker repayment segments. Debt consolidation has very large active exposure, but completed-loan LRR is around 100.1%, so it is mainly an exposure-concentration concern.")
    y -= 8
    y = image_at(c, panels["closed_grade_term"], M, y, W, 210)
    analysis(c, y, "hypothesis assumed", "Longer terms should weaken repayment when combined with lower credit grades because uncertainty and repayment burden last longer. Result: G-grade 60-month loans show 88.9% LRR, while A-grade 36-month loans show 104.3%.")
    c.showPage()

    # 8
    y = h1(c, "Closed Loans: More Granular Risk Signals")
    img1 = ROOT / "tmp" / "pdfs" / "notebook_figures" / "cell_077_0.png"
    img2 = ROOT / "tmp" / "pdfs" / "notebook_figures" / "cell_082_0.png"
    y = image_fit(c, img1, y, 250)
    y = analysis(c, y, "sub-grade", "Charge-off rate generally increases as sub-grade quality declines. Sub-grade helps refine monitoring beyond broad A to G grades.") - 8
    y = image_fit(c, img2, y, 210)
    analysis(c, y, "loan age", "Charge-off risk is highest in the early loan-age buckets, especially around 6-12 months. Early intervention should happen before accounts age too far into trouble.")
    c.showPage()

    # 9
    y = h1(c, "Closed Loan Driver Summary")
    y = image_fit(c, dash2, y, 430)
    analysis(c, y, "closed loans", "The closed-loan view confirms that weak repayment is concentrated by lower grade, high interest, public records, lower income plus high DTI, and weaker long-term grade combinations. These patterns become the basis for monitoring active loans.")
    c.showPage()

    # 10
    y = h1(c, "Applying Closed-Loan Learning to Active Loans")
    y = text(c, "Active loans have not reached their final outcome. The objective is not to label them as failed, but to identify which live accounts look similar to the historical weak-repayment segments.", M, y, W, BOLD)
    y -= 18
    y = table(c, y, [210, W - 210], [
        ["Closed-loan pattern", "Active-loan use"],
        ["Lower grades had weaker LRR.", "Use grade as the first early-warning filter."],
        ["High interest bands had weaker LRR.", "Monitor high-rate active loans earlier and review pricing-risk overlap."],
        ["High DTI, public records, and 60-month terms added risk.", "Flag affordability and credit-history stress before accounts become severely late."],
        ["Purpose changed repayment behaviour.", "Combine purpose risk with outstanding principal before assigning recovery priority."],
    ])
    y -= 8
    y = h2(c, "Active-loan decision logic", y)
    bullets(c, [
        "A loan should move up the recovery queue when it combines delinquency with high outstanding principal.",
        "A risky segment with low exposure should be monitored, but it should not distract from larger recoverable balances.",
        "The strongest warning signal is overlap: lower grade, high rate, longer term, late status, recent inquiries, and high utilization appearing together."
    ], y)
    c.showPage()

    # 11
    y = h1(c, "Active Loans: Delinquency Risk")
    y = image_at(c, panels["active_grade"], M, y, W, 245)
    y = analysis(c, y, "hypothesis assumed", "Active delinquency should rise in lower grades if historical repayment risk is already appearing in the live portfolio. Result: delinquency rises from 1.0% in grade A to 11.6% in grade G.")
    y -= 8
    y = image_at(c, panels["active_utilization"], M, y, W, 240)
    analysis(c, y, "hypothesis assumed", "High revolving utilization should signal repayment pressure because borrowers have less unused credit capacity. Result: active delinquency increases from 2.2% in the 0-30% utilization band to 5.4% in the 100%+ band.")
    c.showPage()

    # 12
    y = h1(c, "Active Loans: Purpose and Exposure")
    active_purpose_risk = csv("active_risk_by_purpose.csv").sort_values("Delinquency_Rate", ascending=False).head(8)
    hbar(c, M, y, W, 245, active_purpose_risk["purpose"], active_purpose_risk["Delinquency_Rate"], "Highest Active Delinquency by Purpose", delinquency_color, "%")
    y -= 262
    y = analysis(c, y, "purpose risk", "Small business, house, renewable energy, and moving loans show higher active delinquency. These groups should be watched more closely when they also carry meaningful exposure.")
    y -= 8
    max_exp = active_purpose["Outstanding_Crores"].max()
    hbar(c, M, y, W, 215, active_purpose["purpose"], active_purpose["Outstanding_Crores"], "Top Active Purposes by Outstanding Principal (Cr)", lambda v: RED if v > max_exp * 0.55 else AMBER if v > max_exp * 0.12 else GREEN, "")
    y -= 232
    analysis(c, y, "exposure", "Debt consolidation and credit card loans carry the largest active outstanding principal. Debt consolidation should be monitored because the exposure is large, not because its completed-loan LRR is poor. Recovery priority should consider both risk percentage and money exposure.")
    c.showPage()

    # 13
    y = h1(c, "Active Loans: Recovery Priority")
    col_w = (W - 16) / 2
    top_y = y
    image_at(c, panels["active_recency"], M, top_y, col_w, 250)
    image_at(c, panels["active_scatter"], M + col_w + 16, top_y, col_w, 250)
    y = top_y - 265
    y = analysis(c, y, "payment recency", "At-risk outstanding is largest in the 0-1 month band at 12.35 Cr, followed by 2-3 months at 7.90 Cr and no-payment-date loans at 3.31 Cr. Recency should help determine how quickly recovery contact is triggered.")
    y -= 8
    y = image_at(c, panels["active_inquiries"], M, y, W, 215)
    analysis(c, y, "recent inquiries", "Recent credit inquiries add another active warning signal. Delinquency increases from 2.7% for borrowers with no recent inquiries to 6.8% for borrowers with 5+ inquiries.")
    c.showPage()

    # 14
    y = h1(c, "Active Risk and Recovery Summary")
    y = image_fit(c, dash3, y, 430)
    y = analysis(c, y, "active portfolio", "The active-risk view links delinquency with exposure. It supports a recovery strategy that starts where risk and outstanding principal are both high, rather than chasing only the highest delinquency percentage.")
    y -= 10
    y = h2(c, "Priority order suggested by the analysis", y)
    bullets(c, [
        "First priority: delinquent C, D, and E grade loans with high outstanding principal.",
        "Second priority: loans in the 0-1 month and 2-3 month recency bands before exposure becomes harder to recover.",
        "Third priority: active loans with high revolving utilization, 3+ recent inquiries, or high-risk purpose segments, reviewed after exposure size is considered."
    ], y)
    c.showPage()

    # 15
    y = h1(c, "Recommendations")
    y = text(c, "The recommendations combine historical repayment patterns with current active-loan exposure. The aim is to improve future loan quality while reducing the chance that active delinquent loans become final losses.", M, y, W)
    y -= 10
    y = table(c, y, [160, W - 160], [
        ["Recommendation", "Business action"],
        ["Prioritise active recovery", "Start with delinquent C, D, and E loans, then rank by outstanding principal. These grades hold about 16.7 Cr of at-risk principal combined."],
        ["Add payment-recency monitoring", "Use last payment recency to trigger faster recovery action. The 0-1 month and 2-3 month bands hold 12.35 Cr and 7.90 Cr of at-risk exposure."],
        ["Tighten future lending rules", "Add stricter review when lower grades, high DTI, high interest rates, public records, and 60-month terms overlap. G-grade 60-month loans show 88.9% LRR and the 25-30% interest band shows 82.0% LRR."],
        ["Strengthen affordability checks", "Assess income with DTI, revolving utilization, and recent inquiries. Active delinquency reaches 5.4% at 100%+ utilization and 6.8% for borrowers with 5+ recent inquiries."],
        ["Act earlier in the loan lifecycle", "Because charge-off risk appears early, intervention should start before loans become severely late."],
    ], PALE_GREEN)
    y -= 8
    y = h2(c, "Final conclusion", y)
    text(c, "UCUCI should use closed-loan repayment patterns to improve approval discipline and use active-loan delinquency plus outstanding principal to guide recovery effort. The strongest opportunity is not one broad policy change, but targeted action on the combinations where weak repayment and high exposure meet.", M, y, W, BOLD)
    c.save()


if __name__ == "__main__":
    build()
