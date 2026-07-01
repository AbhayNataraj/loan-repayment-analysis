from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf"
PDF_PATH = OUT_DIR / "UCUCI_Loan_Repayment_Analysis_Report.pdf"
FIG_DIR = ROOT / "tmp" / "pdfs" / "notebook_figures"
TABLEAU_DIR = ROOT / "tmp" / "pdfs" / "tableau_attach_render"
CROP_DIR = ROOT / "tmp" / "pdfs" / "report_v3_crops"

PAGE_W, PAGE_H = letter
MARGIN_X = 54
TOP = PAGE_H - 54
BOTTOM = 46
CONTENT_W = PAGE_W - 2 * MARGIN_X

FONT = "Arial"
FONT_BOLD = "Arial-Bold"
BODY = 12
LEADING = 15.2

INK = HexColor("#1F2933")
MUTED = HexColor("#5F6C75")
NAVY = HexColor("#102A43")
RULE = HexColor("#D9E2EC")
SOFT_BLUE = HexColor("#EAF3F8")
SOFT_GREEN = HexColor("#E7F5EE")
SOFT_AMBER = HexColor("#FFF4D6")
SOFT_RED = HexColor("#FCE8E8")
GREEN = HexColor("#1F7A4D")
AMBER = HexColor("#B7791F")
RED = HexColor("#B91C1C")


def setup() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CROP_DIR.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont(FONT, r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\arialbd.ttf"))


def crop_whitespace(src: Path, dst: Path, pad: int = 14) -> Path:
    image = Image.open(src).convert("RGB")
    bg = Image.new("RGB", image.size, "white")
    diff = ImageChops.difference(image, bg)
    bbox = diff.getbbox()
    if not bbox:
        image.save(dst)
        return dst
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(image.width, right + pad)
    bottom = min(image.height, bottom + pad)
    image.crop((left, top, right, bottom)).save(dst)
    return dst


def prepare_images() -> dict[str, Path]:
    images = {
        "grade_lrr": FIG_DIR / "cell_040_0.png",
        "interest_lrr": FIG_DIR / "cell_049_0.png",
        "dti_lrr": FIG_DIR / "cell_053_0.png",
        "term_lrr": FIG_DIR / "cell_061_0.png",
        "purpose_lrr": FIG_DIR / "cell_069_0.png",
        "grade_term": FIG_DIR / "cell_073_0.png",
        "subgrade_default": FIG_DIR / "cell_077_0.png",
        "loan_age": FIG_DIR / "cell_082_0.png",
        "active_grade": FIG_DIR / "cell_091_0.png",
        "active_interest": FIG_DIR / "cell_095_0.png",
        "active_purpose": FIG_DIR / "cell_099_0.png",
        "active_exposure_grade": FIG_DIR / "cell_103_0.png",
        "active_exposure_purpose": FIG_DIR / "cell_105_0.png",
        "at_risk_grade": FIG_DIR / "cell_109_0.png",
        "risk_tier": FIG_DIR / "cell_116_0.png",
    }
    for idx in [1, 2, 3, 4]:
        images[f"tableau_{idx}"] = crop_whitespace(
            TABLEAU_DIR / f"page-{idx}.png",
            CROP_DIR / f"tableau_page_{idx}.png",
            pad=24,
        )
    return images


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


def draw_text(
    c: canvas.Canvas,
    value: str,
    x: float,
    y: float,
    width: float,
    font: str = FONT,
    size: int = BODY,
    color: colors.Color = INK,
    leading: float = LEADING,
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


def page_title(c: canvas.Canvas, title: str, eyebrow: str | None = None) -> float:
    y = TOP
    if eyebrow:
        c.setFont(FONT_BOLD, BODY)
        c.setFillColor(MUTED)
        c.drawString(MARGIN_X, y, eyebrow.upper())
        y -= 18
    c.setFont(FONT_BOLD, 18)
    c.setFillColor(NAVY)
    c.drawString(MARGIN_X, y, title)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.line(MARGIN_X, y - 11, PAGE_W - MARGIN_X, y - 11)
    return y - 35


def section(c: canvas.Canvas, label: str, x: float, y: float) -> float:
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(NAVY)
    c.drawString(x, y, label)
    return y - 21


def bullets(c: canvas.Canvas, items: list[str], x: float, y: float, width: float) -> float:
    c.setFont(FONT, BODY)
    c.setFillColor(INK)
    for item in items:
        lines = wrap(item, width - 18)
        c.drawString(x, y, "-")
        for line in lines:
            c.drawString(x + 15, y, line)
            y -= LEADING
        y -= 1.5
    return y


def table(c: canvas.Canvas, x: float, y: float, widths: list[float], rows: list[list[str]], header: bool = True) -> float:
    pad = 7
    c.setStrokeColor(RULE)
    for ridx, row in enumerate(rows):
        font = FONT_BOLD if header and ridx == 0 else FONT
        row_lines = [wrap(cell, w - pad * 2, font, BODY) for cell, w in zip(row, widths)]
        height = max(len(lines) for lines in row_lines) * 15 + 14
        y -= height
        if header and ridx == 0:
            c.setFillColor(SOFT_BLUE)
            c.rect(x, y, sum(widths), height, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.line(x, y + height, x + sum(widths), y + height)
        c.line(x, y, x + sum(widths), y)
        cx = x
        for w, lines in zip(widths, row_lines):
            c.setFont(font, BODY)
            c.setFillColor(NAVY if header and ridx == 0 else INK)
            ty = y + height - pad - BODY
            for line in lines:
                c.drawString(cx + pad, ty, line)
                ty -= 15
            cx += w
    return y - 18


def image_fit(c: canvas.Canvas, path: Path, x: float, y: float, w: float, max_h: float, border: bool = True) -> float:
    im = Image.open(path)
    iw, ih = im.size
    scale = min(w / iw, max_h / ih)
    dw, dh = iw * scale, ih * scale
    dx = x + (w - dw) / 2
    dy = y - dh
    c.drawImage(ImageReader(im), dx, dy, dw, dh, preserveAspectRatio=True, mask="auto")
    if border:
        c.setStrokeColor(RULE)
        c.setLineWidth(0.7)
        c.rect(dx, dy, dw, dh, fill=0, stroke=1)
    return dy - 12


def interpretation(c: canvas.Canvas, y: float, body: str, tone: colors.Color | None = None) -> float:
    x = MARGIN_X
    c.setStrokeColor(tone or RULE)
    c.setLineWidth(2.0)
    c.line(x, y + 3, x, y - 43)
    c.setFont(FONT_BOLD, BODY)
    c.setFillColor(NAVY)
    c.drawString(x + 12, y, "Interpretation")
    return draw_text(c, body, x + 12, y - 18, CONTENT_W - 12, FONT, BODY, INK)


def interpretation_at(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    body: str,
    tone: colors.Color | None = None,
) -> float:
    c.setStrokeColor(tone or RULE)
    c.setLineWidth(2.0)
    c.line(x, y + 3, x, y - 58)
    c.setFont(FONT_BOLD, BODY)
    c.setFillColor(NAVY)
    c.drawString(x + 12, y, "Interpretation")
    return draw_text(c, body, x + 12, y - 18, width - 12, FONT, BODY, INK)


def figure_page(c: canvas.Canvas, title: str, fig1: Path, interp1: str, fig2: Path | None = None, interp2: str | None = None) -> None:
    y = page_title(c, title)
    if fig2 is None:
        y = image_fit(c, fig1, MARGIN_X, y, CONTENT_W, 370)
        interpretation(c, y, interp1, AMBER)
    else:
        y = image_fit(c, fig1, MARGIN_X, y, CONTENT_W, 225)
        y = interpretation(c, y, interp1, AMBER) - 14
        y = image_fit(c, fig2, MARGIN_X, y, CONTENT_W, 225)
        interpretation(c, y, interp2 or "", AMBER)
    c.showPage()


def build_pdf() -> None:
    setup()
    images = prepare_images()
    c = canvas.Canvas(str(PDF_PATH), pagesize=letter)
    c.setTitle("UCUCI Loan Repayment Analysis Report")

    # Page 1
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 118, PAGE_W, 118, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 25)
    c.drawString(MARGIN_X, PAGE_H - 54, "UCUCI Bank Loan Repayment Analysis")
    c.setFont(FONT, 15)
    c.drawString(MARGIN_X, PAGE_H - 82, "Repayment behaviour, active risk, and recovery priorities")
    y = PAGE_H - 155
    y = section(c, "Business context", MARGIN_X, y)
    y = draw_text(
        c,
        "UCUCI Bank needs to understand why some borrower segments repay well while others create default exposure. The report uses completed loans to learn repayment patterns, then applies those patterns to active loans where the bank still has time to intervene.",
        MARGIN_X,
        y,
        CONTENT_W,
    )
    y -= 14
    y = section(c, "Objective", MARGIN_X, y)
    y = bullets(
        c,
        [
            "Identify the key drivers of completed-loan repayment rate.",
            "Separate historical repayment behaviour from current active-loan risk.",
            "Recommend where UCUCI should tighten lending rules and prioritise recovery effort.",
        ],
        MARGIN_X,
        y,
        CONTENT_W,
    )
    y -= 12
    y = section(c, "How to read the report", MARGIN_X, y)
    draw_text(
        c,
        "The closed-loan section explains what has already happened. The active-loan section uses those same patterns to estimate which live loans may behave poorly and where outstanding principal is most exposed.",
        MARGIN_X,
        y,
        CONTENT_W,
        FONT_BOLD,
    )
    c.showPage()

    # Page 2
    y = page_title(c, "Dataset and Metric Setup")
    y = section(c, "Dataset overview", MARGIN_X, y)
    y = table(
        c,
        MARGIN_X,
        y,
        [150, CONTENT_W - 150],
        [
            ["Item", "Details"],
            ["Dataset", "UCUCI Bank Loan Dataset"],
            ["Shape", "887,379 rows and 57 columns"],
            ["Loan record check", "No duplicate loan IDs and no duplicate member IDs were found."],
            ["Main status field", "loan_status"],
            ["Closed loans", "Fully Paid, Charged Off, Default"],
            ["Active loans", "Current, In Grace Period, Late (16-30 days), Late (31-120 days)"],
            ["Files used", "Python notebook outputs, Tableau dashboard PDF, and supporting Tableau summary files."],
        ],
    )
    y -= 12
    y = section(c, "Key metrics", MARGIN_X, y)
    y = table(
        c,
        MARGIN_X,
        y,
        [155, CONTENT_W - 155],
        [
            ["Metric", "Meaning"],
            ["Loan Repayment Rate", "Total amount repaid divided by total funded amount. This is the main completed-loan metric."],
            ["Default Rate", "Charged-off loans divided by total loans."],
            ["Active Delinquency Rate", "Active loans in grace or late status divided by active loans."],
            ["At-Risk Outstanding", "Outstanding principal on active delinquent loans."],
        ],
    )
    y -= 10
    y = section(c, "Initial preparation", MARGIN_X, y)
    bullets(
        c,
        [
            "Interest rates were cleaned as numeric values and terms were standardised before comparison.",
            "DTI values above 100 were treated as extreme cases for banded DTI analysis.",
            "Closed and active loans were analysed separately because they answer different business questions.",
        ],
        MARGIN_X,
        y,
        CONTENT_W,
    )
    c.showPage()

    # Page 3
    y = page_title(c, "Portfolio Health from Tableau")
    y = image_fit(c, images["tableau_1"], MARGIN_X, y, CONTENT_W, 460)
    interpretation(
        c,
        y,
        "The portfolio has 887,379 loans and a completed-loan repayment rate of 100.3%. The overall picture looks stable, but the dashboard also shows 5.10% default rate and concentrated at-risk exposure in grades C, D, and E. This is why the rest of the report goes below the portfolio average.",
        AMBER,
    )
    c.showPage()

    # Page 4
    y = page_title(c, "Business Hypotheses")
    y = draw_text(
        c,
        "The analysis tests whether borrower quality, pricing, affordability, term, and purpose explain repayment behaviour. These hypotheses are then reused for active loans to decide where risk is building.",
        MARGIN_X,
        y,
        CONTENT_W,
    )
    y -= 18
    table(
        c,
        MARGIN_X,
        y,
        [62, 248, CONTENT_W - 310],
        [
            ["ID", "Hypothesis", "How it is checked"],
            ["H1", "Lower grades repay worse.", "Compare LRR by grade on closed loans."],
            ["H2", "Higher interest loans repay worse.", "Compare LRR by interest-rate band."],
            ["H3", "Higher DTI borrowers repay worse.", "Compare LRR by DTI band."],
            ["H4", "60-month loans carry more repayment risk.", "Compare LRR by term and then by grade-term combination."],
            ["H5", "Loan purpose affects repayment.", "Compare LRR by purpose."],
            ["H6", "Closed-loan patterns can guide active-loan monitoring.", "Compare active delinquency and outstanding exposure by the same dimensions."],
        ],
    )
    c.showPage()

    # Closed loan pages
    figure_page(
        c,
        "Closed Loans: Grade and Interest Rate",
        images["grade_lrr"],
        "Repayment weakens as grade worsens. A and B sit above 104% LRR, while G falls below 90%. Grade is therefore one of the clearest historical repayment indicators.",
        images["interest_lrr"],
        "Higher interest bands show lower LRR. The highest band drops sharply, which means pricing alone is not enough to compensate for high-risk lending.",
    )
    figure_page(
        c,
        "Closed Loans: DTI and Loan Term",
        images["dti_lrr"],
        "DTI shows affordability pressure. Repayment declines as DTI rises up to the 30-40 band, so income should be assessed together with borrower debt burden.",
        images["term_lrr"],
        "60-month loans repay worse than 36-month loans. Longer tenure should be treated carefully when it is paired with weaker grade or higher DTI.",
    )
    figure_page(
        c,
        "Closed Loans: Purpose and Combined Grade-Term Risk",
        images["purpose_lrr"],
        "Purpose adds useful business context. Small business, moving, medical, and other loans sit near the weaker end of the repayment range.",
        images["grade_term"],
        "The heatmap shows the weakest combination clearly: lower grades with 60-month terms. G-grade 60-month loans are the lowest repayment cell.",
    )
    figure_page(
        c,
        "Closed Loans: Sub-Grade and Loan-Age Risk",
        images["subgrade_default"],
        "Sub-grade gives a more granular risk view. Charge-off rates generally rise as sub-grade quality declines, which can help UCUCI refine monitoring beyond broad grades.",
        images["loan_age"],
        "The loan-age view shows charge-off risk appears early, especially around the 6-12 month bucket. Early intervention matters before accounts move too far into loss.",
    )

    # Page 9: Tableau closed dashboard
    y = page_title(c, "Closed Loan Dashboard View")
    y = image_fit(c, images["tableau_2"], MARGIN_X, y, CONTENT_W, 470)
    interpretation(
        c,
        y,
        "The Tableau dashboard brings the closed-loan drivers together: grade, interest band, DTI, term, grade-term combination, and purpose all point toward the same conclusion. Repayment risk is not random; it concentrates in predictable borrower and loan characteristics.",
        AMBER,
    )
    c.showPage()

    # Active loan pages
    y = page_title(c, "From Closed Loans to Active Loans")
    y = draw_text(
        c,
        "The active portfolio has not reached final outcome yet. That means the report should not call these loans failed. Instead, it uses the patterns observed in closed loans to identify active borrowers who may need earlier attention.",
        MARGIN_X,
        y,
        CONTENT_W,
        FONT_BOLD,
    )
    y -= 18
    y = section(c, "What changes in active-loan analysis", MARGIN_X, y)
    bullets(
        c,
        [
            "Completed-loan LRR becomes a learning signal, not the active-loan metric.",
            "Active delinquency rate is used to identify live repayment stress.",
            "Outstanding principal is used to decide where recovery action has the biggest financial impact.",
        ],
        MARGIN_X,
        y,
        CONTENT_W,
    )
    y -= 86
    y = section(c, "How closed-loan patterns are used", MARGIN_X, y)
    table(
        c,
        MARGIN_X,
        y,
        [210, CONTENT_W - 210],
        [
            ["Closed-loan pattern", "Active-loan use"],
            ["Lower grades had weaker LRR.", "Use grade as the first early-warning filter."],
            ["High interest bands had weaker LRR.", "Monitor high-rate active loans with earlier reminders."],
            ["Higher DTI and 60-month terms added risk.", "Flag affordability stress before accounts become severely late."],
            ["Purpose changed repayment behaviour.", "Combine purpose risk with outstanding principal before assigning recovery priority."],
        ],
    )
    c.showPage()

    figure_page(
        c,
        "Active Loans: Delinquency by Grade and Interest",
        images["active_grade"],
        "Active delinquency rises from grade A to grade G, matching the closed-loan grade pattern. This supports using grade as an early-warning filter.",
        images["active_interest"],
        "Delinquency also rises with interest band. High-rate active loans should receive faster reminders and closer monitoring.",
    )
    figure_page(
        c,
        "Active Loans: Purpose Risk and Exposure",
        images["active_purpose"],
        "Small business, house, renewable energy, and moving loans show higher active delinquency. Purpose is useful for monitoring tone and priority.",
        images["active_exposure_purpose"],
        "Debt consolidation dominates outstanding principal exposure. A high-risk percentage is important, but exposure size decides where potential losses become most material.",
    )
    figure_page(
        c,
        "Active Loans: Recovery Priority",
        images["at_risk_grade"],
        "At-risk outstanding principal is highest in grades C, D, and E. These grades are the best starting point for recovery action because they combine risk with money exposure.",
        images["risk_tier"],
        "The rule-based risk tier turns the analysis into an operating queue. High and medium tiers should receive more frequent monitoring than low-risk active loans.",
    )

    # Page 14
    y = page_title(c, "Active Risk Dashboard View")
    y = image_fit(c, images["tableau_3"], MARGIN_X, y, CONTENT_W, 470)
    interpretation(
        c,
        y,
        "The active dashboard connects delinquency, exposure, and recovery priority. It shows why UCUCI should not chase only the highest delinquency rate; the best recovery queue combines risk level with outstanding principal.",
        RED,
    )
    c.showPage()

    # Page 15
    y = page_title(c, "Recommendations")
    y = draw_text(
        c,
        "The recommendations combine two ideas: improve future lending quality using closed-loan patterns, and protect the current portfolio through earlier active-loan recovery action.",
        MARGIN_X,
        y,
        CONTENT_W,
    )
    y -= 12
    y = table(
        c,
        MARGIN_X,
        y,
        [160, CONTENT_W - 160],
        [
            ["Recommendation", "Action"],
            ["Prioritise active recovery", "Start with active delinquent loans in grades C, D, and E, sorted by outstanding principal."],
            ["Tighten high-risk approvals", "Add stricter checks when lower grades combine with 60-month term, high DTI, or high interest rate."],
            ["Use affordability checks", "Read annual income together with DTI and installment burden rather than using income alone."],
            ["Monitor high-exposure purposes", "Debt consolidation and credit card loans should stay prominent in Tableau reviews because exposure is large."],
            ["Use Tableau regularly", "Track completed-loan LRR drivers separately from active-loan delinquency and exposure."],
        ],
    )
    y -= 8
    y = section(c, "Final message", MARGIN_X, y)
    y = draw_text(
        c,
        "UCUCI should use historical repayment patterns as a guide, then act early on active loans where delinquency and outstanding principal overlap. This approach improves future lending decisions and gives the bank a practical recovery queue for the current portfolio.",
        MARGIN_X,
        y,
        CONTENT_W,
        FONT_BOLD,
    )
    y -= 12
    y = section(c, "Monitoring checklist", MARGIN_X, y)
    bullets(
        c,
        [
            "Review active delinquent C, D, and E loans daily.",
            "Track high-interest and 60-month active loans weekly.",
            "Refresh Tableau views before each portfolio review so recovery teams work from current exposure.",
        ],
        MARGIN_X,
        y,
        CONTENT_W,
    )
    c.save()


if __name__ == "__main__":
    build_pdf()
