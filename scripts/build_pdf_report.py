#!/usr/bin/env python3
"""Create the visually verified model governance PDF."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/pdf"
PDF_PATH = OUTPUT / "credit_risk_model_governance_report.pdf"
PLOT = ROOT / "artifacts/plots"

WIDTH, HEIGHT = A4
MARGIN = 18 * mm
CONTENT_WIDTH = WIDTH - 2 * MARGIN
NAVY = colors.HexColor("#0B1F3A")
TEAL = colors.HexColor("#0F766E")
BLUE = colors.HexColor("#2563EB")
AMBER = colors.HexColor("#D97706")
RED = colors.HexColor("#B42318")
GREEN = colors.HexColor("#15803D")
SLATE = colors.HexColor("#64748B")
PALE = colors.HexColor("#E8EEF6")
PALE_2 = colors.HexColor("#F8FAFC")
RULE = colors.HexColor("#CBD5E1")
WHITE = colors.white

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("DejaVu", FONT_REGULAR))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", FONT_BOLD))

executive = json.loads((ROOT / "artifacts/metrics/executive_summary.json").read_text())
comparison = pd.read_csv(ROOT / "artifacts/metrics/model_comparison.csv")
risk_bands = pd.read_csv(ROOT / "artifacts/metrics/risk_band_summary.csv")
monitoring = pd.read_csv(ROOT / "artifacts/monitoring/monthly_monitoring.csv")
fairness = pd.read_csv(ROOT / "artifacts/metrics/fairness_summary.csv")
shap = pd.read_csv(ROOT / "artifacts/explanations/global_linear_shap_importance.csv")
quality = pd.read_csv(ROOT / "artifacts/metrics/data_quality_checks.csv")

BODY = ParagraphStyle(
    "Body",
    fontName="DejaVu",
    fontSize=9.4,
    leading=13.4,
    textColor=NAVY,
    alignment=TA_LEFT,
    spaceAfter=4,
)
BODY_SMALL = ParagraphStyle(
    "BodySmall",
    fontName="DejaVu",
    fontSize=7.6,
    leading=10.5,
    textColor=NAVY,
)
BULLET = ParagraphStyle(
    "Bullet",
    parent=BODY,
    leftIndent=11,
    firstLineIndent=-8,
    bulletIndent=0,
    spaceAfter=3,
)
SUBHEAD = ParagraphStyle(
    "Subhead",
    fontName="DejaVu-Bold",
    fontSize=12,
    leading=15,
    textColor=NAVY,
    spaceAfter=5,
)
TITLE = ParagraphStyle(
    "Title",
    fontName="DejaVu-Bold",
    fontSize=24,
    leading=29,
    textColor=NAVY,
)
CAPTION = ParagraphStyle(
    "Caption",
    fontName="DejaVu",
    fontSize=7.2,
    leading=9.4,
    textColor=SLATE,
)
TABLE_HEADER = ParagraphStyle(
    "TableHeader",
    fontName="DejaVu-Bold",
    fontSize=7.2,
    leading=9,
    textColor=WHITE,
    alignment=TA_LEFT,
)
TABLE_CELL = ParagraphStyle(
    "TableCell",
    fontName="DejaVu",
    fontSize=6.7,
    leading=8.5,
    textColor=NAVY,
)


def paragraph(
    c: canvas.Canvas,
    text: str,
    x: float,
    y_top: float,
    width: float,
    style: ParagraphStyle = BODY,
) -> float:
    item = Paragraph(text, style)
    _, height = item.wrap(width, HEIGHT)
    item.drawOn(c, x, y_top - height)
    return y_top - height


def bullet_list(
    c: canvas.Canvas,
    items: list[str],
    x: float,
    y_top: float,
    width: float,
    style: ParagraphStyle = BULLET,
) -> float:
    y = y_top
    for item in items:
        y = paragraph(c, f"- {item}", x, y, width, style) - 2
    return y


def page_header(
    c: canvas.Canvas,
    page: int,
    title: str,
    subtitle: str = "",
    kicker: str = "BANKING CREDIT RISK",
) -> float:
    c.setFillColor(TEAL)
    c.rect(0, HEIGHT - 5 * mm, WIDTH, 5 * mm, fill=1, stroke=0)
    c.setFont("DejaVu-Bold", 7.5)
    c.setFillColor(TEAL)
    c.drawString(MARGIN, HEIGHT - 16 * mm, kicker)
    c.setFont("DejaVu-Bold", 18)
    c.setFillColor(NAVY)
    c.drawString(MARGIN, HEIGHT - 28 * mm, title)
    c.setFont("DejaVu", 7.5)
    c.setFillColor(SLATE)
    c.drawRightString(WIDTH - MARGIN, HEIGHT - 16 * mm, f"{page:02d} / 16")
    c.setStrokeColor(RULE)
    c.line(MARGIN, HEIGHT - 33 * mm, WIDTH - MARGIN, HEIGHT - 33 * mm)
    y = HEIGHT - 40 * mm
    if subtitle:
        y = paragraph(c, subtitle, MARGIN, y, CONTENT_WIDTH, CAPTION) - 4
    return y


def page_footer(c: canvas.Canvas, page: int) -> None:
    c.setStrokeColor(RULE)
    c.line(MARGIN, 15 * mm, WIDTH - MARGIN, 15 * mm)
    c.setFont("DejaVu", 6.7)
    c.setFillColor(SLATE)
    c.drawString(
        MARGIN,
        9.5 * mm,
        "Synthetic portfolio - decision support only - not financial, legal, accounting or lending advice",
    )
    c.drawRightString(WIDTH - MARGIN, 9.5 * mm, f"Aurelia Bank model governance report | {page}")


def section_label(c: canvas.Canvas, text: str, x: float, y: float, width: float) -> float:
    c.setFillColor(NAVY)
    c.roundRect(x, y - 9 * mm, width, 9 * mm, 2 * mm, fill=1, stroke=0)
    c.setFont("DejaVu-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(x + 4 * mm, y - 6.2 * mm, text)
    return y - 13 * mm


def kpi_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    label: str,
    value: str,
    note: str,
    accent: colors.Color = TEAL,
) -> None:
    c.setFillColor(PALE)
    c.roundRect(x, y, width, 30 * mm, 2.5 * mm, fill=1, stroke=0)
    c.setFillColor(accent)
    c.rect(x, y, 2.5 * mm, 30 * mm, fill=1, stroke=0)
    c.setFillColor(SLATE)
    c.setFont("DejaVu-Bold", 7.3)
    c.drawString(x + 6 * mm, y + 22.5 * mm, label)
    c.setFillColor(NAVY)
    c.setFont("DejaVu-Bold", 17)
    c.drawString(x + 6 * mm, y + 11 * mm, value)
    c.setFillColor(SLATE)
    c.setFont("DejaVu", 6.5)
    c.drawString(x + 6 * mm, y + 4.5 * mm, note)


def draw_image(
    c: canvas.Canvas,
    path: Path,
    x: float,
    y: float,
    width: float,
    height: float,
    caption: str,
) -> None:
    c.setStrokeColor(RULE)
    c.setFillColor(WHITE)
    c.roundRect(x, y, width, height, 2 * mm, fill=1, stroke=1)
    image = Image(str(path), width=width - 6 * mm, height=height - 10 * mm, kind="proportional")
    image._restrictSize(width - 6 * mm, height - 10 * mm)
    image.drawOn(c, x + (width - image.drawWidth) / 2, y + 7 * mm)
    paragraph(c, caption, x + 3 * mm, y + 6 * mm, width - 6 * mm, CAPTION)


def data_table(
    c: canvas.Canvas,
    data: list[list[str]],
    x: float,
    y_top: float,
    col_widths: list[float],
    row_heights: list[float] | None = None,
    status_columns: list[int] | None = None,
) -> float:
    wrapped = [
        [Paragraph(str(value), TABLE_HEADER if row_index == 0 else TABLE_CELL) for value in row]
        for row_index, row in enumerate(data)
    ]
    table = Table(wrapped, colWidths=col_widths, rowHeights=row_heights, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE_2]),
    ]
    table.setStyle(TableStyle(style))
    _, height = table.wrap(sum(col_widths), HEIGHT)
    table.drawOn(c, x, y_top - height)
    return y_top - height


def source_line(c: canvas.Canvas, text: str, y: float) -> None:
    c.setFont("DejaVu", 6.4)
    c.setFillColor(SLATE)
    c.drawString(MARGIN, y, text)


def start_page(
    c: canvas.Canvas,
    page: int,
    title: str,
    subtitle: str = "",
    kicker: str = "BANKING CREDIT RISK",
) -> float:
    if page > 1:
        c.showPage()
    return page_header(c, page, title, subtitle, kicker)


def finish_page(c: canvas.Canvas, page: int) -> None:
    page_footer(c, page)


OUTPUT.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(PDF_PATH), pagesize=A4)
c.setTitle("Banking Credit Risk & Explainable Loan Decisioning Platform")
c.setAuthor("Murat Miraç Gedik")
c.setSubject("Synthetic credit risk model governance portfolio report")
c.setKeywords("credit risk, probability of default, SHAP, fairness, model monitoring")

# Page 1 - cover
c.setFillColor(NAVY)
c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
c.setFillColor(TEAL)
c.rect(0, HEIGHT - 8 * mm, WIDTH, 8 * mm, fill=1, stroke=0)
c.setFont("DejaVu-Bold", 8)
c.setFillColor(colors.HexColor("#7DD3C7"))
c.drawString(MARGIN, HEIGHT - 27 * mm, "AURELIA BANK - MODEL RISK ANALYTICS")
paragraph(
    c,
    "Banking Credit Risk &amp;<br/>Explainable Loan Decisioning Platform",
    MARGIN,
    HEIGHT - 62 * mm,
    CONTENT_WIDTH - 15 * mm,
    ParagraphStyle(
        "CoverTitle",
        parent=TITLE,
        fontSize=27,
        leading=34,
        textColor=WHITE,
    ),
)
paragraph(
    c,
    "Model governance report for a deterministic synthetic retail unsecured lending portfolio.",
    MARGIN,
    HEIGHT - 110 * mm,
    125 * mm,
    ParagraphStyle(
        "CoverSub",
        parent=BODY,
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#D7E1EE"),
    ),
)
kpi_card(c, MARGIN, 72 * mm, 50 * mm, "APPLICATIONS", "48,000", "Synthetic portfolio", TEAL)
kpi_card(
    c,
    MARGIN + 55 * mm,
    72 * mm,
    50 * mm,
    "OOT ROC AUC",
    f"{executive['oot_roc_auc']:.3f}",
    "2025 temporal holdout",
    BLUE,
)
kpi_card(
    c,
    MARGIN + 110 * mm,
    72 * mm,
    50 * mm,
    "DISPOSITION",
    "REVIEW",
    "No real lending use",
    AMBER,
)
c.setFillColor(colors.HexColor("#D7E1EE"))
c.setFont("DejaVu", 8)
c.drawString(
    MARGIN, 48 * mm, "Version 1.0.0 | July 2026 | Prepared as a professional portfolio project"
)
c.setFont("DejaVu-Bold", 7.5)
c.setFillColor(colors.HexColor("#FCA5A5"))
c.drawString(
    MARGIN,
    24 * mm,
    "SYNTHETIC DATA - DECISION SUPPORT ONLY - NO CLAIM OF REGULATORY COMPLIANCE",
)
c.showPage()

# Page 2 - executive summary
page = 2
y = page_header(c, page, "Executive summary")
for index, (label, value, note, accent) in enumerate(
    [
        ("OOT ROC AUC", f"{executive['oot_roc_auc']:.3f}", "Gate >= 0.700", TEAL),
        ("Gini", f"{executive['oot_gini']:.3f}", "Rank ordering", BLUE),
        ("Approval recommendation", f"{executive['approval_rate']:.1%}", "PD < 10%", AMBER),
    ]
):
    kpi_card(c, MARGIN + index * 57 * mm, y - 34 * mm, 52 * mm, label, value, note, accent)
y -= 43 * mm
y = section_label(c, "Management conclusion", MARGIN, y, CONTENT_WIDTH)
y = paragraph(
    c,
    "The platform demonstrates a complete model-risk pattern: reproducible synthetic data, "
    "temporal development and validation, an interpretable champion, calibrated PDs, explicit "
    "policy thresholds, exact additive Linear SHAP, fairness diagnostics and monthly monitoring. "
    "The age-band allocation gap is intentionally surfaced as a governance blocker.",
    MARGIN,
    y,
    CONTENT_WIDTH,
)
y -= 3 * mm
y = bullet_list(
    c,
    [
        f"Out-of-time ROC AUC is {executive['oot_roc_auc']:.3f}; calibration slope is {executive['oot_calibration_slope']:.3f}.",
        f"Approve recommendations cover {executive['approval_rate']:.1%} of OOT applications; their observed default rate is {executive['approved_observed_default_rate']:.1%}.",
        f"Linear SHAP reconstructs model log-odds with maximum error {executive['linear_shap_max_additivity_error']:.2e}.",
        f"The maximum demographic parity difference is {executive['fairness_max_demographic_parity_difference']:.1%}; governance review is required.",
        "The current disposition is portfolio-complete but not approved for real lending use.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
draw_image(
    c,
    PLOT / "executive_dashboard.png",
    MARGIN,
    28 * mm,
    CONTENT_WIDTH,
    75 * mm,
    "Figure 1. Executive control tower generated from deterministic OOT evidence.",
)
source_line(c, "Sources: internal artifacts; governance context [S1], [S2], [S4].", 20 * mm)
finish_page(c, page)

# Page 3 - scope
page = 3
y = start_page(c, page, "Purpose, scope and safety boundary")
y = paragraph(
    c,
    "The implementation is an educational and portfolio-grade decision-support system for a "
    "fictional institution. It cannot issue a final approval, decline, price, limit or legally "
    "sufficient adverse-action notice. The API returns a recommendation that must be interpreted "
    "inside an authorized human workflow.",
    MARGIN,
    y,
    CONTENT_WIDTH,
)
y -= 5 * mm
table_data = [
    ["In scope", "Mandatory oversight", "Explicitly out of scope"],
    [
        "12-month PD and score<br/>A-F risk bands<br/>Policy recommendations<br/>Illustrative expected loss<br/>Reason codes and monitoring",
        "Credit officer review<br/>Independent model validation<br/>Fairness investigation<br/>Policy exception process<br/>Legal and disclosure review",
        "Automated final decisions<br/>Real customer data<br/>Pricing or limits<br/>Production adverse action<br/>Claimed legal or accounting compliance",
    ],
]
data_table(c, table_data, MARGIN, y, [CONTENT_WIDTH / 3] * 3, [10 * mm, 58 * mm])
y -= 78 * mm
y = section_label(c, "Human authority boundary", MARGIN, y, CONTENT_WIDTH)
y = bullet_list(
    c,
    [
        "The model estimates risk; policy maps the estimate to a recommendation.",
        "The review workflow can request evidence, override a recommendation or decline to act.",
        "Protected attributes are absent from the model and online contract.",
        "A production implementation would require jurisdiction-specific legal analysis, validation and approval.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
c.setFillColor(colors.HexColor("#FEE2E2"))
c.roundRect(MARGIN, 39 * mm, CONTENT_WIDTH, 36 * mm, 2 * mm, fill=1, stroke=0)
paragraph(
    c,
    "<b>Current model disposition:</b> not approved for real credit decisioning. "
    "Fairness and external-validity work remain open.",
    MARGIN + 5 * mm,
    68 * mm,
    CONTENT_WIDTH - 10 * mm,
    BODY,
)
source_line(
    c,
    "Reference context: EU AI Act [S3], EBA loan origination guidelines [S2], NIST AI RMF [S4].",
    20 * mm,
)
finish_page(c, page)

# Page 4 - data and temporal design
page = 4
y = start_page(c, page, "Portfolio and temporal design")
kpis = [
    ("Development", f"{executive['development_applications']:,}", "2022 to Jun 2024", TEAL),
    ("Validation", f"{executive['validation_applications']:,}", "Jul to Dec 2024", BLUE),
    ("Out-of-time", f"{executive['out_of_time_applications']:,}", "2025", AMBER),
]
for index, (label, value, note, accent) in enumerate(kpis):
    kpi_card(c, MARGIN + index * 57 * mm, y - 34 * mm, 52 * mm, label, value, note, accent)
y -= 44 * mm
y = section_label(c, "Data-generation controls", MARGIN, y, CONTENT_WIDTH)
y = bullet_list(
    c,
    [
        "Deterministic NumPy generator with a fixed seed and canonical SHA-256 evidence.",
        "Application dates span 2022-01-01 through 2025-12-31.",
        "Target is a synthetic 12-month default indicator generated from non-protected risk drivers.",
        "The committed reviewer sample contains 250 rows; full portfolios are compressed CSV files.",
        "Six critical data-quality and safety controls pass before model fitting.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
y -= 2 * mm
quality_table = [["Control", "Actual", "Expected", "Status"]] + quality[
    ["control", "actual", "expected", "status"]
].astype(str).values.tolist()
data_table(c, quality_table, MARGIN, y, [75 * mm, 28 * mm, 28 * mm, 30 * mm])
source_line(
    c,
    "Internal sources: config/project.yaml, src/credit_risk/data.py, artifacts/metrics/data_quality_checks.csv.",
    20 * mm,
)
finish_page(c, page)

# Page 5 - model development
page = 5
y = start_page(c, page, "Model development and champion selection")
draw_image(
    c,
    PLOT / "model_comparison.png",
    MARGIN,
    123 * mm,
    112 * mm,
    94 * mm,
    "Figure 2. Validation ROC AUC.",
)
paragraph(
    c,
    "<b>Champion policy</b><br/>Logistic regression is selected because it leads the validation "
    "comparison on ROC AUC and Brier while supporting exact additive explanations. Histogram "
    "gradient boosting and random forest remain challengers.",
    MARGIN + 117 * mm,
    y,
    CONTENT_WIDTH - 117 * mm,
    BODY,
)
comparison_table = [["Model", "ROC AUC", "Gini", "Brier", "Status"]]
for _, row in comparison.iterrows():
    comparison_table.append(
        [
            row["model"].replace("_", " "),
            f"{row['roc_auc']:.3f}",
            f"{row['gini']:.3f}",
            f"{row['brier']:.3f}",
            row["deployment_status"],
        ]
    )
data_table(c, comparison_table, MARGIN, 112 * mm, [56 * mm, 25 * mm, 22 * mm, 22 * mm, 34 * mm])
y = 76 * mm
y = section_label(c, "Selection gates", MARGIN, y, CONTENT_WIDTH)
bullet_list(
    c,
    [
        "Temporal validation AUC >= 0.700.",
        "Calibration slope within 0.75 to 1.25.",
        "Protected attributes excluded.",
        "Exact explanation identity test passes.",
        "Independent validation still required before any controlled pilot.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "Internal sources: src/credit_risk/modeling.py and artifacts/metrics/model_comparison.csv.",
    20 * mm,
)
finish_page(c, page)

# Page 6 - OOT performance
page = 6
y = start_page(c, page, "Out-of-time performance")
draw_image(
    c, PLOT / "oot_roc_curve.png", MARGIN, 78 * mm, 105 * mm, 135 * mm, "Figure 3. OOT ROC curve."
)
kpi_card(
    c,
    MARGIN + 110 * mm,
    166 * mm,
    52 * mm,
    "ROC AUC",
    f"{executive['oot_roc_auc']:.3f}",
    "Gate >= 0.700",
    TEAL,
)
kpi_card(
    c,
    MARGIN + 110 * mm,
    130 * mm,
    52 * mm,
    "Gini",
    f"{executive['oot_gini']:.3f}",
    "2 x AUC - 1",
    BLUE,
)
kpi_card(
    c,
    MARGIN + 110 * mm,
    94 * mm,
    52 * mm,
    "KS",
    f"{executive['oot_ks']:.3f}",
    "Max separation",
    AMBER,
)
kpi_card(
    c,
    MARGIN + 110 * mm,
    58 * mm,
    52 * mm,
    "PR AUC",
    f"{executive['oot_pr_auc']:.3f}",
    "Default-focused",
    TEAL,
)
y = 49 * mm
y = paragraph(
    c,
    "The champion crosses the predefined synthetic-project discrimination gate with a credible "
    "margin. The result is evidence for this generated portfolio only; it cannot be extrapolated "
    "to a real applicant population without representative data, redevelopment and validation.",
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "Internal source: artifacts/metrics/sample_metrics.json. Metric implementation reference: scikit-learn [S7].",
    20 * mm,
)
finish_page(c, page)

# Page 7 - calibration and deciles
page = 7
y = start_page(c, page, "Calibration and risk deciles")
draw_image(
    c,
    PLOT / "oot_calibration.png",
    MARGIN,
    128 * mm,
    82 * mm,
    86 * mm,
    "Figure 4. OOT calibration.",
)
draw_image(
    c,
    PLOT / "risk_deciles.png",
    MARGIN + 87 * mm,
    128 * mm,
    82 * mm,
    86 * mm,
    "Figure 5. OOT risk deciles.",
)
kpi_card(
    c,
    MARGIN,
    89 * mm,
    52 * mm,
    "Calibration slope",
    f"{executive['oot_calibration_slope']:.3f}",
    "Target 0.75 to 1.25",
    TEAL,
)
kpi_card(
    c,
    MARGIN + 57 * mm,
    89 * mm,
    52 * mm,
    "Brier",
    f"{executive['oot_brier']:.3f}",
    "Lower is better",
    BLUE,
)
kpi_card(
    c,
    MARGIN + 114 * mm,
    89 * mm,
    52 * mm,
    "OOT default rate",
    f"{executive['oot_default_rate']:.1%}",
    "Observed",
    AMBER,
)
y = 78 * mm
y = section_label(c, "Interpretation", MARGIN, y, CONTENT_WIDTH)
bullet_list(
    c,
    [
        "Calibration evaluates whether probability levels match observed event rates.",
        "Risk deciles test ordering and default capture across the score distribution.",
        "Brier combines calibration and discrimination; it is not a calibration-only metric.",
        "Monthly monitoring repeats both performance and distribution checks.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "Calibration reference: scikit-learn probability calibration [S7]. Internal decile table: artifacts/metrics/risk_deciles.csv.",
    20 * mm,
)
finish_page(c, page)

# Page 8 - policy
page = 8
y = start_page(c, page, "Decision policy and score mapping")
policy_table = [
    ["PD interval", "Recommendation", "Required action"],
    ["PD < 10%", "APPROVE_RECOMMENDATION", "Human confirmation may still apply"],
    ["10% <= PD < 22%", "REFER", "Mandatory authorized review"],
    ["PD >= 22%", "DECLINE_RECOMMENDATION", "Mandatory review and disclosure workflow"],
]
data_table(
    c, policy_table, MARGIN, y, [40 * mm, 62 * mm, 59 * mm], [10 * mm, 18 * mm, 18 * mm, 18 * mm]
)
y -= 76 * mm
y = section_label(c, "Score and expected-loss conventions", MARGIN, y, CONTENT_WIDTH)
y = bullet_list(
    c,
    [
        "Score anchor is 650 points at 10% PD; 50 points represent a doubling of odds.",
        "Scores are clipped to 300 to 850 and bands A to F communicate continuous PD.",
        "Illustrative expected loss equals PD x 45% LGD x requested amount.",
        "The expected-loss bridge is not an IFRS 9 impairment model: it has no staging, lifetime PD, discounting or macroeconomic scenarios.",
        "The Excel workbench exposes policy thresholds as editable inputs with formula-driven outputs.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
c.setFillColor(PALE)
c.roundRect(MARGIN, 44 * mm, CONTENT_WIDTH, 38 * mm, 2 * mm, fill=1, stroke=0)
paragraph(
    c,
    "<b>Policy ownership:</b> model development owns estimation evidence; the credit policy "
    "committee owns thresholds; authorized officers own final decisions.",
    MARGIN + 5 * mm,
    74 * mm,
    CONTENT_WIDTH - 10 * mm,
    BODY,
)
source_line(
    c,
    "Internal sources: config/project.yaml, src/credit_risk/policy.py, Excel workbench. IFRS 9 context [S5].",
    20 * mm,
)
finish_page(c, page)

# Page 9 - bands and EL
page = 9
y = start_page(c, page, "Risk bands and illustrative expected loss")
risk_table = [["Band", "Applications", "Average PD", "Observed DR", "Expected loss"]]
for _, row in risk_bands.iterrows():
    risk_table.append(
        [
            row["risk_band"],
            f"{int(row['applications']):,}",
            f"{row['average_pd']:.1%}",
            f"{row['observed_default_rate']:.1%}",
            f"TRY {row['expected_loss'] / 1_000_000:.2f}m",
        ]
    )
data_table(c, risk_table, MARGIN, y, [20 * mm, 34 * mm, 32 * mm, 34 * mm, 41 * mm])
y -= 72 * mm
kpi_card(
    c,
    MARGIN,
    y - 34 * mm,
    52 * mm,
    "OOT EL",
    f"TRY {executive['expected_loss_total'] / 1_000_000:.1f}m",
    "Illustrative",
    AMBER,
)
kpi_card(
    c,
    MARGIN + 57 * mm,
    y - 34 * mm,
    52 * mm,
    "Approval rate",
    f"{executive['approval_rate']:.1%}",
    "PD < 10%",
    TEAL,
)
kpi_card(
    c,
    MARGIN + 114 * mm,
    y - 34 * mm,
    52 * mm,
    "Approved DR",
    f"{executive['approved_observed_default_rate']:.1%}",
    "Observed",
    BLUE,
)
y -= 45 * mm
y = paragraph(
    c,
    "The band table helps a committee understand portfolio mix, risk concentration and the "
    "consequences of changing the approve boundary. Scenario outputs remain illustrative because "
    "approval propensity, pricing response, prepayment and recoveries are not modeled.",
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "Internal sources: artifacts/metrics/risk_band_summary.csv and policy_scenarios.csv. IFRS 9 terminology [S5].",
    20 * mm,
)
finish_page(c, page)

# Page 10 - explainability
page = 10
y = start_page(c, page, "Explainability and reason-code governance")
draw_image(
    c,
    PLOT / "global_linear_shap.png",
    MARGIN,
    104 * mm,
    110 * mm,
    110 * mm,
    "Figure 6. Global Linear SHAP importance.",
)
y = 209 * mm
paragraph(
    c,
    "<b>Exact additive identity</b><br/>For the standardized and one-hot encoded logistic model, "
    "the implementation computes phi_j = beta_j x (x_j - E[x_j]) in log-odds space. The expected "
    "log-odds plus all feature contributions reconstruct the model output to numerical precision.",
    MARGIN + 115 * mm,
    y,
    CONTENT_WIDTH - 115 * mm,
    BODY_SMALL,
)
kpi_card(
    c,
    MARGIN + 115 * mm,
    137 * mm,
    51 * mm,
    "Max additivity error",
    f"{executive['linear_shap_max_additivity_error']:.1e}",
    "Log-odds",
    GREEN,
)
y = 94 * mm
y = section_label(c, "Reason-code contract", MARGIN, y, CONTENT_WIDTH)
bullet_list(
    c,
    [
        "Return the top four risk-increasing contributions for reviewer attention.",
        "Keep protected attributes out of the model and explanation state.",
        "Describe contributions as model evidence, never causal findings.",
        "Do not treat model reason codes as a legally sufficient adverse-action notice.",
        "Preserve the full contribution table for validation and audit.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "SHAP method reference [S6]. Internal sources: src/credit_risk/explainability.py and artifacts/explanations/.",
    20 * mm,
)
finish_page(c, page)

# Page 11 - fairness
page = 11
y = start_page(c, page, "Fairness assessment and governance disposition")
draw_image(
    c,
    PLOT / "fairness_diagnostics.png",
    MARGIN,
    118 * mm,
    105 * mm,
    96 * mm,
    "Figure 7. Approval allocation by protected group.",
)
gender = fairness.loc[fairness["protected_attribute"] == "gender"].iloc[0]
age = fairness.loc[fairness["protected_attribute"] == "age_band"].iloc[0]
kpi_card(
    c,
    MARGIN + 110 * mm,
    169 * mm,
    52 * mm,
    "Gender DP gap",
    f"{gender['demographic_parity_difference']:.1%}",
    "Diagnostic",
    TEAL,
)
kpi_card(
    c,
    MARGIN + 110 * mm,
    132 * mm,
    52 * mm,
    "Age-band DP gap",
    f"{age['demographic_parity_difference']:.1%}",
    "Escalate",
    RED,
)
y = 107 * mm
c.setFillColor(colors.HexColor("#FEE2E2"))
c.roundRect(MARGIN, y - 30 * mm, CONTENT_WIDTH, 30 * mm, 2 * mm, fill=1, stroke=0)
paragraph(
    c,
    "<b>GOVERNANCE REVIEW REQUIRED.</b> The age-band difference exceeds the project's internal "
    "10 percentage-point triage signal. This threshold is not a legal fairness standard.",
    MARGIN + 5 * mm,
    y - 6 * mm,
    CONTENT_WIDTH - 10 * mm,
    BODY,
)
y -= 38 * mm
y = bullet_list(
    c,
    [
        "Investigate credit-history and tenure pathways that may act differently across age groups.",
        "Review sample composition, legitimate risk factors, policy thresholds and measurement uncertainty.",
        "Perform intersectional and jurisdiction-specific analysis with legal and stakeholder input.",
        "Do not suppress the finding or call the model fair because protected attributes were excluded.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "Fairness assessment reference [S8]. Internal evidence: artifacts/metrics/fairness_by_group.csv and fairness_summary.csv.",
    20 * mm,
)
finish_page(c, page)

# Page 12 - monitoring
page = 12
y = start_page(c, page, "Model monitoring and incident response")
draw_image(
    c,
    PLOT / "model_monitoring.png",
    MARGIN,
    105 * mm,
    112 * mm,
    109 * mm,
    "Figure 8. Monthly OOT performance and PSI.",
)
kpi_card(
    c,
    MARGIN + 117 * mm,
    170 * mm,
    49 * mm,
    "Max score PSI",
    f"{executive['maximum_monthly_score_psi']:.3f}",
    "Warning 0.10",
    GREEN,
)
kpi_card(c, MARGIN + 117 * mm, 132 * mm, 49 * mm, "Months", f"{len(monitoring)}", "2025 OOT", BLUE)
y = 96 * mm
y = section_label(c, "Monitoring controls", MARGIN, y, CONTENT_WIDTH)
bullet_list(
    c,
    [
        "Monthly ROC AUC, Brier, observed default rate and approval recommendation rate.",
        "Score PSI plus bureau-score and DTI population-stability diagnostics.",
        "Green, amber and red triage with explicit investigation and rollback guidance.",
        "API throughput, latency, errors and availability exposed to Prometheus.",
        "Model incidents require preserved inputs, output, version, policy state and human action.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "Monitoring references: Evidently drift docs [S9], Prometheus instrumentation [S10]. Internal runbook: docs/operations/monitoring-runbook.md.",
    20 * mm,
)
finish_page(c, page)

# Page 13 - architecture and security
page = 13
y = start_page(c, page, "Architecture, API and security controls")
architecture = [
    ["Layer", "Implementation", "Primary control"],
    [
        "Analytics",
        "Python package and deterministic pipeline",
        "Temporal split, metrics, SHAP identity",
    ],
    ["Decision support", "FastAPI /api/v1/score", "Strict schema; protected fields absent"],
    ["Data", "PostgreSQL schemas and views", "Governance schema separation"],
    ["BI", "Power BI project and Excel workbench", "Formula lineage and source audit"],
    ["Operations", "Prometheus and Grafana", "Availability, latency and errors"],
    ["Runtime", "Docker and Kubernetes", "Non-root, read-only, capabilities dropped"],
    ["Delivery", "GitHub Actions", "Tests, coverage, CodeQL, pip-audit, Trivy"],
]
data_table(c, architecture, MARGIN, y, [32 * mm, 69 * mm, 60 * mm], [10 * mm] + [17 * mm] * 7)
y -= 132 * mm
y = section_label(c, "API response boundary", MARGIN, y, CONTENT_WIDTH)
y = paragraph(
    c,
    "The scoring endpoint returns request ID, model version, 12-month PD, credit score, risk "
    "band, recommendation, human-review flag, illustrative expected loss and four reason codes. "
    "It does not return or accept protected attributes and does not execute an external action.",
    MARGIN,
    y,
    CONTENT_WIDTH,
)
y -= 4 * mm
y = bullet_list(
    c,
    [
        "API-key option and extra-field rejection.",
        "Health, readiness and Prometheus endpoints.",
        "No credentials or production endpoints committed.",
        "Hardened container and restrictive Kubernetes network policy.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "Internal sources: Dockerfile, docker-compose.yml, infra/kubernetes/, src/credit_risk/api.py and service.py.",
    20 * mm,
)
finish_page(c, page)

# Page 14 - reference mapping
page = 14
y = start_page(
    c,
    page,
    "Reference mapping - not a compliance claim",
    "Primary sources inform the control design. Applicability and conformity require qualified legal, accounting, risk and validation review.",
)
references = [
    ["ID", "Primary source", "Control influence", "URL"],
    [
        "S1",
        "Basel Committee - Principles for management of credit risk (2025)",
        "Granting, monitoring, controls",
        "bis.org/bcbs/publ/d595.pdf",
    ],
    [
        "S2",
        "EBA - Guidelines on loan origination and monitoring",
        "Creditworthiness governance",
        "eba.europa.eu/.../EBA GL 2020 06",
    ],
    [
        "S3",
        "Regulation (EU) 2024/1689 - AI Act",
        "High-risk context and oversight",
        "eur-lex.europa.eu/eli/reg/2024/1689/oj",
    ],
    [
        "S4",
        "NIST AI RMF 1.0",
        "Govern, Map, Measure, Manage",
        "nist.gov/itl/ai-risk-management-framework",
    ],
    [
        "S5",
        "IFRS 9 Financial Instruments",
        "Expected-credit-loss terminology",
        "ifrs.org/issued-standards/.../ifrs-9",
    ],
    ["S6", "SHAP documentation", "Additive explanation method", "shap.readthedocs.io/en/latest/"],
    [
        "S7",
        "scikit-learn calibration documentation",
        "Calibration curves and Brier context",
        "scikit-learn.org/stable/modules/calibration.html",
    ],
    [
        "S8",
        "Fairlearn assessment documentation",
        "Disaggregated fairness metrics",
        "fairlearn.org/main/user_guide/assessment/",
    ],
    [
        "S9",
        "Evidently data drift documentation",
        "Distribution shift concepts",
        "docs.evidentlyai.com/metrics/preset_data_drift",
    ],
    [
        "S10",
        "Prometheus instrumentation guidance",
        "Operational metrics design",
        "prometheus.io/docs/practices/instrumentation/",
    ],
]
data_table(
    c, references, MARGIN, y, [15 * mm, 57 * mm, 46 * mm, 43 * mm], [9 * mm] + [17.5 * mm] * 10
)
y -= 194 * mm
y = paragraph(
    c,
    "These references are crosswalk inputs. The project does not certify compliance with Basel "
    "standards, EBA guidelines, the EU AI Act, IFRS 9 or any consumer-credit law.",
    MARGIN,
    y,
    CONTENT_WIDTH,
)
finish_page(c, page)

# Page 15 - validation and limitations
page = 15
y = start_page(c, page, "Validation evidence, limitations and residual risk")
validation_table = [
    ["Control", "Result", "Disposition"],
    ["Data quality", "6 / 6 PASS", "Proceed to model evidence"],
    ["Temporal OOT AUC", f"{executive['oot_roc_auc']:.3f}", "Synthetic gate passes"],
    ["Calibration slope", f"{executive['oot_calibration_slope']:.3f}", "Within 0.75 to 1.25"],
    [
        "SHAP identity",
        f"{executive['linear_shap_max_additivity_error']:.1e}",
        "Passes numerical tolerance",
    ],
    [
        "Monthly score PSI",
        f"max {executive['maximum_monthly_score_psi']:.3f}",
        "Below 0.10 warning",
    ],
    [
        "Fairness",
        f"max DP {executive['fairness_max_demographic_parity_difference']:.1%}",
        "Governance review required",
    ],
    ["Workbook controls", "8 / 8 PASS", "Formula and source checks pass"],
    ["Slide layout", "20 / 20 PASS", "No overflow detected"],
]
data_table(c, validation_table, MARGIN, y, [56 * mm, 39 * mm, 66 * mm], [10 * mm] + [15 * mm] * 8)
y -= 136 * mm
y = section_label(c, "Material limitations", MARGIN, y, CONTENT_WIDTH)
y = bullet_list(
    c,
    [
        "All data are synthetic; no representativeness or production validity is established.",
        "Target generation and model form are simplified and share an intentionally controlled structure.",
        "No reject inference, bureau data licensing, fraud controls or affordability policy is implemented.",
        "Expected loss is illustrative and not an IFRS 9 engine.",
        "Fairness metrics are descriptive and do not resolve legal, causal or normative questions.",
        "No independent validator or production change-approval committee has reviewed the model.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
source_line(
    c,
    "Internal QA evidence: artifacts/manifest.json, reports/workbook/, reports/presentation/ and tests/.",
    20 * mm,
)
finish_page(c, page)

# Page 16 - Turkish summary and roadmap
page = 16
y = start_page(c, page, "Türkçe yönetici özeti ve sonraki adımlar", kicker="YÖNETİCİ ÖZETİ")
y = paragraph(
    c,
    f"Proje, 48.000 sentetik kredi başvurusu üzerinde 12 aylık temerrüt olasılığı, kredi skoru, "
    f"A-F risk segmentasyonu, SHAP neden kodları, politika önerileri ve model izleme katmanlarını "
    f"tek bir yönetişim mimarisinde birleştirir. 2025 dönemindeki zaman dışı testte ROC AUC "
    f"{executive['oot_roc_auc']:.3f}, Gini {executive['oot_gini']:.3f} ve kalibrasyon eğimi "
    f"{executive['oot_calibration_slope']:.3f} olarak ölçülmüştür.",
    MARGIN,
    y,
    CONTENT_WIDTH,
)
y -= 4 * mm
y = section_label(c, "Temel sonuç", MARGIN, y, CONTENT_WIDTH)
y = bullet_list(
    c,
    [
        "Model ve politika ayrılmış, nihai karar yetkisi insan incelemesinde tutulmuştur.",
        "Korunan nitelikler modelden çıkarılmış ve sadece ayrı adalet denetiminde kullanılmıştır.",
        "SHAP katkıları log-odds düzeyinde matematiksel olarak doğrulanmıştır.",
        "Yaş grupları arasındaki belirgin tahsis farkı, gerçek kullanım öncesi zorunlu yönetişim bulgusudur.",
        "Proje portföy seviyesi açısından tamamdır; gerçek kredi kararları için onaylı değildir.",
    ],
    MARGIN,
    y,
    CONTENT_WIDTH,
)
y -= 3 * mm
y = section_label(c, "Kontrollü pilot için yol haritası", MARGIN, y, CONTENT_WIDTH)
roadmap = [
    ["1", "Bağımsız doğrulama", "Metrikleri yeniden üret, varsayımları zorla"],
    ["2", "Adalet incelemesi", "Yaş grubu farkının nedenlerini ve vekil etkileri araştır"],
    ["3", "Hukuk ve politika", "Yetki, bildirim, itiraz ve override akışını onayla"],
    ["4", "Shadow çalışma", "Aksiyon üretmeden izleme ve olay tatbikatı yap"],
    ["5", "Komite kararı", "Sınırlı kapsam, rollback ve periyodik doğrulama"],
]
data_table(
    c,
    [["Aşama", "Çalışma", "Çıkış kriteri"]] + roadmap,
    MARGIN,
    y,
    [18 * mm, 52 * mm, 91 * mm],
    [10 * mm] + [17 * mm] * 5,
)
c.setFillColor(colors.HexColor("#FEE2E2"))
c.roundRect(MARGIN, 39 * mm, CONTENT_WIDTH, 36 * mm, 2 * mm, fill=1, stroke=0)
paragraph(
    c,
    "<b>Son durum:</b> Profesyonel portföy paketi tamamlandı. Gerçek müşteri verisi veya "
    "otomatik kredi kararı için kullanılamaz.",
    MARGIN + 5 * mm,
    68 * mm,
    CONTENT_WIDTH - 10 * mm,
    BODY,
)
finish_page(c, page)

c.save()
print(f"PDF written to {PDF_PATH}")
