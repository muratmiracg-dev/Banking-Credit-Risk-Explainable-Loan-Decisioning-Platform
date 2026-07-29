#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const artifactModule = path.join(
  process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,
  "@oai/artifact-tool/dist/artifact_tool.mjs",
);
const { Presentation, PresentationFile } = await import(`file://${artifactModule}`);

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUTPUT = path.join(ROOT, "reports/presentation");
const RENDERED = path.join(OUTPUT, "rendered");
const executive = JSON.parse(
  await fs.readFile(path.join(ROOT, "artifacts/metrics/executive_summary.json"), "utf8"),
);

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') quoted = false;
      else field += char;
    } else if (char === '"') quoted = true;
    else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else field += char;
  }
  const headers = rows[0];
  return rows.slice(1).filter((values) => values.length > 1).map((values) =>
    Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])),
  );
}

async function csv(relativePath) {
  return parseCsv(await fs.readFile(path.join(ROOT, relativePath), "utf8"));
}

const comparison = await csv("artifacts/metrics/model_comparison.csv");
const riskBands = await csv("artifacts/metrics/risk_band_summary.csv");
const monitoring = await csv("artifacts/monitoring/monthly_monitoring.csv");
const fairnessSummary = await csv("artifacts/metrics/fairness_summary.csv");
const shap = await csv("artifacts/explanations/global_linear_shap_importance.csv");
const scenarios = await csv("artifacts/metrics/policy_scenarios.csv");

const C = {
  canvas: "#FFFFFF",
  ink: "#0B1F3A",
  panel: "#EDF2F7",
  panel2: "#F8FAFC",
  rule: "#B8BCC4",
  accent: "#6DCBF4",
  blue: "#2563EB",
  teal: "#0F766E",
  tealLight: "#CCFBF1",
  amber: "#D97706",
  amberLight: "#FEF3C7",
  red: "#B42318",
  redLight: "#FEE2E2",
  green: "#15803D",
  greenLight: "#DCFCE7",
  slate: "#64748B",
};
const FONT = "Arial";
const SLIDE = { width: 1280, height: 720 };
const M = 52;

function addBox(slide, x, y, width, height, fill = C.panel, line = C.rule, radius = "rounded-lg") {
  return slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
    borderRadius: radius,
  });
}

function addText(slide, text, x, y, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width, height },
    fill: options.fill ?? "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: options.size ?? 18,
    typeface: FONT,
    color: options.color ?? C.ink,
    bold: options.bold ?? false,
    italic: options.italic ?? false,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "top",
    autoFit: options.autoFit ?? "shrinkText",
  };
  return shape;
}

function addRule(slide, x, y, width, color = C.teal, height = 4) {
  slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width, height },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
}

function addTitle(slide, title, number, kicker = "BANKING CREDIT RISK") {
  addText(slide, kicker, M, 26, 430, 26, { size: 14, bold: true, color: C.teal });
  addText(slide, title, M, 62, 1140, 72, { size: 38, bold: true, color: C.ink });
  addRule(slide, M, 142, 1176, C.rule, 1);
  addText(slide, String(number).padStart(2, "0"), 1166, 24, 60, 24, {
    size: 14,
    bold: true,
    color: C.slate,
    align: "right",
  });
}

function addFooter(slide, number, left = "SYNTHETIC • DECISION SUPPORT ONLY") {
  addRule(slide, M, 678, 1176, C.rule, 1);
  addText(slide, left, M, 687, 740, 20, { size: 12, bold: true, color: C.slate });
  addText(slide, `${number} / 20`, 1130, 687, 96, 20, {
    size: 12,
    color: C.slate,
    align: "right",
  });
}

function addKpi(slide, x, y, width, label, value, note, tone = "teal") {
  const palettes = {
    teal: [C.tealLight, C.teal],
    blue: ["#DBEAFE", C.blue],
    amber: [C.amberLight, C.amber],
    red: [C.redLight, C.red],
  };
  const [fill, accent] = palettes[tone];
  addBox(slide, x, y, width, 142, fill, "none");
  addRule(slide, x, y, 7, accent, 142);
  addText(slide, label, x + 24, y + 20, width - 42, 28, { size: 16, bold: true, color: C.slate });
  addText(slide, value, x + 24, y + 50, width - 42, 48, { size: 34, bold: true, color: C.ink });
  addText(slide, note, x + 24, y + 104, width - 42, 24, { size: 14, color: C.slate });
}

function addBulletList(slide, bullets, x, y, width, height, options = {}) {
  const gap = options.gap ?? 60;
  bullets.forEach((bullet, index) => {
    addBox(slide, x, y + index * gap + 4, 20, 20, options.bulletFill ?? C.teal, "none");
    addText(slide, bullet, x + 34, y + index * gap, width - 34, gap - 4, {
      size: options.size ?? 18,
      color: options.color ?? C.ink,
      bold: options.bold ?? false,
    });
  });
}

function addCard(slide, x, y, width, height, title, body, tone = "neutral") {
  const palette = {
    neutral: [C.panel2, C.rule],
    teal: [C.tealLight, C.teal],
    blue: ["#DBEAFE", C.blue],
    amber: [C.amberLight, C.amber],
    red: [C.redLight, C.red],
    green: [C.greenLight, C.green],
  };
  const [fill, accent] = palette[tone];
  addBox(slide, x, y, width, height, fill, "none");
  addRule(slide, x, y, width, accent, 6);
  addText(slide, title, x + 22, y + 24, width - 44, 40, { size: 21, bold: true });
  addText(slide, body, x + 22, y + 72, width - 44, height - 92, { size: 16, color: C.slate });
}

async function addImage(slide, relativePath, x, y, width, height, alt) {
  const bytes = await fs.readFile(path.join(ROOT, relativePath));
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  addBox(slide, x, y, width, height, C.canvas, C.rule);
  slide.images.add({
    blob: buffer,
    contentType: "image/png",
    alt,
    fit: "contain",
    position: { left: x + 8, top: y + 8, width: width - 16, height: height - 16 },
  });
}

function addNotes(slide, sources, presenter = "") {
  const notes = [
    presenter,
    "",
    "[Sources]",
    ...sources.map((source) => `- ${source}`),
    "[/Sources]",
  ].join("\n");
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(true);
}

function newSlide() {
  const slide = presentation.slides.add();
  slide.background.fill = C.canvas;
  return slide;
}

const presentation = Presentation.create({ slideSize: SLIDE });

// 01 — cover, adapted from Codex Grid slide-01 stacked text flow.
{
  const slide = newSlide();
  addRule(slide, 0, 0, 1280, C.teal, 12);
  addText(slide, "AURELIA BANK • MODEL RISK ANALYTICS", M, 44, 680, 30, {
    size: 16,
    bold: true,
    color: C.teal,
  });
  addText(
    slide,
    "Banking Credit Risk\n& Explainable Loan Decisioning",
    M,
    168,
    1080,
    220,
    { size: 54, bold: true, color: C.ink },
  );
  addText(
    slide,
    "A governed, human-in-the-loop decision-support platform built on a deterministic synthetic portfolio.",
    M,
    430,
    860,
    76,
    { size: 23, color: C.slate },
  );
  addBox(slide, 970, 452, 256, 142, C.panel, "none");
  addText(slide, "48,000", 994, 476, 208, 48, { size: 36, bold: true, color: C.teal });
  addText(slide, "synthetic applications", 994, 532, 208, 28, { size: 16, color: C.slate });
  addText(slide, "Portfolio project • v1.0.0 • 2026", M, 626, 520, 28, { size: 15, color: C.slate });
  addNotes(slide, [
    "artifacts/metrics/executive_summary.json",
    "https://www.bis.org/bcbs/publ/d595.pdf",
  ], "Open with the safety boundary: this is decision support, not automated credit approval.");
}

// 02 — thesis
{
  const slide = newSlide();
  addTitle(slide, "One platform connects credit judgement, evidence and control", 2);
  addKpi(slide, M, 182, 270, "OOT ROC AUC", executive.oot_roc_auc.toFixed(3), "Temporal 2025 holdout", "teal");
  addKpi(slide, 352, 182, 270, "Gini", executive.oot_gini.toFixed(3), "Rank-ordering strength", "blue");
  addKpi(slide, 650, 182, 270, "Approval recommendation", `${(executive.approval_rate * 100).toFixed(1)}%`, "Policy threshold = 10% PD", "amber");
  addKpi(slide, 948, 182, 278, "SHAP additivity error", executive.linear_shap_max_additivity_error.toExponential(1), "Numerical identity check", "teal");
  addText(slide, "Executive thesis", M, 366, 300, 36, { size: 22, bold: true });
  addText(
    slide,
    "The portfolio demonstrates a credible model-risk operating pattern: calibrated PDs, transparent risk segmentation, exact additive explanations, explicit fairness escalation and monthly monitoring — with human authority retained throughout.",
    M,
    414,
    1176,
    150,
    { size: 23, color: C.ink },
  );
  addFooter(slide, 2);
  addNotes(slide, ["artifacts/metrics/executive_summary.json"], "Lead with the actual OOT evidence, then the governance boundary.");
}

// 03 — scope
{
  const slide = newSlide();
  addTitle(slide, "The design separates analytical recommendation from legal decision", 3);
  addCard(slide, M, 180, 350, 390, "In scope", "12-month PD scoring\nA-F risk segmentation\nApprove / refer / decline recommendation\nIllustrative PD × LGD × EAD\nReason codes and monitoring", "green");
  addCard(slide, 465, 180, 350, 390, "Mandatory oversight", "Authorized credit officer review\nPolicy exception workflow\nIndependent model validation\nFairness investigation\nJurisdiction-specific disclosure review", "amber");
  addCard(slide, 838, 180, 388, 390, "Explicitly out of scope", "Automated final approval\nPricing or limit assignment\nProduction adverse-action notices\nReal customer data\nClaimed Basel, EBA, AI Act or IFRS 9 compliance", "red");
  addFooter(slide, 3);
  addNotes(slide, [
    "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "https://www.eba.europa.eu/sites/default/files/document_library/Publications/Guidelines/2020/Guidelines%20on%20loan%20origination%20and%20monitoring/884283/EBA%20GL%202020%2006%20Final%20Report%20on%20GL%20on%20loan%20origination%20and%20monitoring.pdf",
    "docs/governance/model-card.md",
  ]);
}

// 04 — portfolio design
{
  const slide = newSlide();
  addTitle(slide, "Temporal evidence is designed to resemble a real model lifecycle", 4);
  const segments = [
    ["2022–Jun 2024", "Development", executive.development_applications.toLocaleString("en-US"), C.teal],
    ["Jul–Dec 2024", "Validation", executive.validation_applications.toLocaleString("en-US"), C.blue],
    ["2025", "Out-of-time", executive.out_of_time_applications.toLocaleString("en-US"), C.amber],
  ];
  segments.forEach(([period, label, count, color], index) => {
    const x = M + index * 390;
    addBox(slide, x, 220, 350, 230, C.panel2, "none");
    addRule(slide, x, 220, 350, color, 8);
    addText(slide, period, x + 24, 252, 300, 30, { size: 18, bold: true, color });
    addText(slide, label, x + 24, 300, 300, 40, { size: 27, bold: true });
    addText(slide, count, x + 24, 356, 300, 50, { size: 36, bold: true, color: C.ink });
    addText(slide, "applications", x + 24, 410, 300, 24, { size: 16, color: C.slate });
  });
  addText(slide, "Application-time variables only", M, 504, 360, 34, { size: 21, bold: true });
  addText(slide, "Protected attributes are retained solely in a restricted fairness-audit slice and never enter training or online scoring.", M, 548, 1176, 74, { size: 19, color: C.slate });
  addFooter(slide, 4);
  addNotes(slide, ["config/project.yaml", "src/credit_risk/data.py", "artifacts/metrics/executive_summary.json"]);
}

// 05 — architecture
{
  const slide = newSlide();
  addTitle(slide, "Reference architecture makes every decision traceable", 5);
  const stages = [
    ["1", "Synthetic applications", "Deterministic generation\nSchema & DQ gates"],
    ["2", "Feature boundary", "Application-time only\nProtected fields excluded"],
    ["3", "Model & policy", "Calibrated PD\nScore • band • recommendation"],
    ["4", "Evidence layer", "Linear SHAP\nFairness • monitoring • lineage"],
    ["5", "Human action", "Review queue\nOverride & audit record"],
  ];
  stages.forEach(([number, title, body], index) => {
    const x = M + index * 236;
    addBox(slide, x, 230, 204, 260, index === 4 ? C.amberLight : C.panel2, "none");
    addText(slide, number, x + 20, 248, 44, 44, { size: 28, bold: true, color: index === 4 ? C.amber : C.teal });
    addText(slide, title, x + 20, 308, 164, 62, { size: 20, bold: true });
    addText(slide, body, x + 20, 386, 164, 76, { size: 16, color: C.slate });
    if (index < stages.length - 1) addRule(slide, x + 204, 356, 32, C.rule, 3);
  });
  addBox(slide, M, 528, 1148, 84, C.redLight, "none");
  addText(slide, "CONTROL BOUNDARY", M + 22, 548, 200, 26, { size: 15, bold: true, color: C.red });
  addText(slide, "The platform can recommend; only an authorized person or approved downstream policy process can decide.", M + 230, 546, 954, 32, { size: 19, bold: true, color: C.ink });
  addFooter(slide, 5);
  addNotes(slide, ["docs/architecture/system-architecture.md", "https://www.nist.gov/itl/ai-risk-management-framework"]);
}

// 06 — feature governance
{
  const slide = newSlide();
  addTitle(slide, "Feature governance starts before model fitting", 6);
  addBulletList(slide, [
    "17 numeric + 6 categorical application-time predictors with deterministic provenance.",
    "No outcome leakage: post-origination delinquency and collection events are excluded.",
    "Gender and age band never enter preprocessing, training, scoring or reason-code generation.",
    "One-hot / standardized logistic preprocessing is persisted inside the champion pipeline.",
    "Data-quality gates cover schema, uniqueness, binary target, completeness and safety flags.",
  ], M, 188, 680, 360, { gap: 76, size: 18 });
  addBox(slide, 790, 186, 436, 380, C.panel2, "none");
  addText(slide, "Feature boundary", 820, 216, 376, 38, { size: 24, bold: true });
  addText(slide, "MODEL-ELIGIBLE", 820, 282, 180, 26, { size: 14, bold: true, color: C.green });
  addText(slide, "Income • DTI • bureau score • utilization • history • tenure • purpose • channel", 820, 318, 356, 84, { size: 17, color: C.ink });
  addRule(slide, 820, 424, 356, C.rule, 1);
  addText(slide, "AUDIT-ONLY", 820, 448, 180, 26, { size: 14, bold: true, color: C.red });
  addText(slide, "Gender • age band", 820, 484, 356, 40, { size: 20, bold: true, color: C.red });
  addFooter(slide, 6);
  addNotes(slide, ["src/credit_risk/data.py", "src/credit_risk/modeling.py", "artifacts/metrics/data_quality_checks.csv"]);
}

// 07 — model comparison
{
  const slide = newSlide();
  addTitle(slide, "The interpretable champion also leads the validation set", 7);
  await addImage(slide, "artifacts/plots/model_comparison.png", M, 178, 700, 390, "Validation ROC AUC model comparison");
  addCard(slide, 790, 178, 436, 116, "Champion", `Logistic regression\nValidation AUC ${Number(comparison.find((row) => row.model === "logistic_regression").roc_auc).toFixed(3)}`, "green");
  addCard(slide, 790, 314, 436, 116, "Why it wins", "Best AUC and Brier in validation; probability outputs remain directly auditable.", "teal");
  addCard(slide, 790, 450, 436, 116, "Challenge discipline", "Histogram gradient boosting and random forest remain evidence, not discarded experiments.", "blue");
  addFooter(slide, 7);
  addNotes(slide, ["artifacts/metrics/model_comparison.csv", "artifacts/plots/model_comparison.png", "src/credit_risk/modeling.py"]);
}

// 08 — OOT performance
{
  const slide = newSlide();
  addTitle(slide, "Out-of-time evidence confirms stable rank ordering", 8);
  await addImage(slide, "artifacts/plots/oot_roc_curve.png", M, 178, 560, 414, "Out-of-time ROC curve");
  addKpi(slide, 650, 180, 270, "ROC AUC", executive.oot_roc_auc.toFixed(3), "Gate ≥ 0.700", "teal");
  addKpi(slide, 948, 180, 278, "KS", executive.oot_ks.toFixed(3), "Maximum separation", "blue");
  addKpi(slide, 650, 350, 270, "PR AUC", executive.oot_pr_auc.toFixed(3), "Default-focused precision", "amber");
  addKpi(slide, 948, 350, 278, "Brier", executive.oot_brier.toFixed(3), "Probability accuracy", "teal");
  addText(slide, "Performance is sufficient for this synthetic case, not proof of external validity.", 650, 526, 576, 54, { size: 18, bold: true, color: C.red });
  addFooter(slide, 8);
  addNotes(slide, ["artifacts/metrics/sample_metrics.json", "artifacts/plots/oot_roc_curve.png", "https://scikit-learn.org/stable/modules/model_evaluation.html"]);
}

// 09 — calibration & deciles
{
  const slide = newSlide();
  addTitle(slide, "Calibration and deciles answer different governance questions", 9);
  await addImage(slide, "artifacts/plots/oot_calibration.png", M, 180, 520, 390, "Out-of-time calibration curve");
  await addImage(slide, "artifacts/plots/risk_deciles.png", 590, 180, 636, 390, "Risk decile observed and predicted default rates");
  addText(slide, `Calibration slope ${executive.oot_calibration_slope.toFixed(3)}`, M, 590, 520, 34, { size: 20, bold: true, color: C.teal });
  addText(slide, "Reliability: do PD levels match outcomes?", M, 624, 520, 28, { size: 16, color: C.slate });
  addText(slide, "Rank ordering: do risk tiers separate outcomes?", 590, 590, 636, 34, { size: 20, bold: true, color: C.blue });
  addFooter(slide, 9);
  addNotes(slide, ["artifacts/plots/oot_calibration.png", "artifacts/plots/risk_deciles.png", "https://scikit-learn.org/stable/modules/calibration.html"]);
}

// 10 — decision policy
{
  const slide = newSlide();
  addTitle(slide, "Policy translates PD into a transparent review path", 10);
  const policy = [
    ["PD < 10%", "APPROVE\nRECOMMENDATION", "Human confirmation may still apply", "green"],
    ["10% ≤ PD < 22%", "REFER", "Mandatory credit officer review", "amber"],
    ["PD ≥ 22%", "DECLINE\nRECOMMENDATION", "Mandatory review + disclosure workflow", "red"],
  ];
  policy.forEach(([range, label, note, tone], index) => {
    const x = M + index * 390;
    addCard(slide, x, 196, 350, 286, range, `${label}\n\n${note}`, tone);
  });
  addText(slide, "Credit score mapping", M, 520, 260, 32, { size: 20, bold: true });
  addText(slide, "650 points at 10% PD • 50 points to double the odds • clipped to 300–850", 320, 518, 906, 40, { size: 18, color: C.slate });
  addText(slide, "Risk bands and scores communicate model output; they do not replace policy ownership.", M, 586, 1176, 34, { size: 19, bold: true, color: C.red });
  addFooter(slide, 10);
  addNotes(slide, ["config/project.yaml", "src/credit_risk/policy.py", "reports/workbook/credit_risk_decision_workbench.xlsx"]);
}

// 11 — risk bands
{
  const slide = newSlide();
  addTitle(slide, "Risk bands make portfolio composition visible", 11);
  await addImage(slide, "artifacts/plots/executive_dashboard.png", M, 174, 770, 432, "Executive credit risk control tower");
  const maxBand = riskBands.reduce((left, right) => Number(left.applications) > Number(right.applications) ? left : right);
  addCard(slide, 850, 176, 376, 142, "Largest band", `${maxBand.risk_band} • ${Number(maxBand.applications).toLocaleString("en-US")} applications`, "blue");
  addCard(slide, 850, 338, 376, 142, "OOT default rate", `${(executive.oot_default_rate * 100).toFixed(1)}%\nObserved 12-month outcome`, "amber");
  addCard(slide, 850, 500, 376, 106, "Boundary", "A-F bands are communication layers over continuous PD.", "neutral");
  addFooter(slide, 11);
  addNotes(slide, ["artifacts/metrics/risk_band_summary.csv", "artifacts/plots/executive_dashboard.png"]);
}

// 12 — economics / scenarios
{
  const slide = newSlide();
  addTitle(slide, "Threshold scenarios expose the volume–risk trade-off", 12);
  const selected = [scenarios[0], scenarios[4], scenarios[8], scenarios[10]];
  const categories = selected.map((row) => `${(Number(row.approve_max_pd) * 100).toFixed(0)}%`);
  slide.charts.add("bar", {
    position: { left: M, top: 188, width: 700, height: 380 },
    categories,
    series: [
      {
        name: "Approval rate",
        values: selected.map((row) => Number(row.approval_rate)),
        fill: C.teal,
      },
      {
        name: "Approved observed default rate",
        values: selected.map((row) => Number(row.approved_observed_default_rate)),
        fill: C.amber,
      },
    ],
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { fontSize: "16px", typeface: FONT } },
    yAxis: {
      min: 0,
      max: 0.75,
      numberFormatCode: "0%",
      majorGridlines: { style: "solid", fill: C.panel, width: 1 },
      textStyle: { fontSize: "16px", typeface: FONT, color: C.slate },
    },
    xAxis: { textStyle: { fontSize: "16px", typeface: FONT, color: C.slate } },
    chartFill: C.canvas,
    chartLine: { style: "solid", fill: C.canvas, width: 0 },
    plotAreaFill: { type: "none" },
  });
  addCard(slide, 790, 190, 436, 150, "Illustrative expected loss", `₺${(executive.expected_loss_total / 1_000_000).toFixed(1)}m\nPD × 45% LGD × requested amount`, "amber");
  addCard(slide, 790, 362, 436, 206, "Interpret carefully", "The EL bridge is a transparent scenario aid. It is not an IFRS 9 impairment engine: no staging, lifetime PD, discounting, recoveries or forward-looking macro scenarios are claimed.", "red");
  addFooter(slide, 12);
  addNotes(slide, ["artifacts/metrics/policy_scenarios.csv", "https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/", "reports/workbook/credit_risk_decision_workbench.xlsx"]);
}

// 13 — SHAP
{
  const slide = newSlide();
  addTitle(slide, "Exact additive Linear SHAP makes the champion auditable", 13);
  await addImage(slide, "artifacts/plots/global_linear_shap.png", M, 178, 700, 420, "Global Linear SHAP importance");
  addCard(slide, 790, 180, 436, 120, "Global view", "Mean absolute contribution ranks the drivers of model output.", "teal");
  addCard(slide, 790, 320, 436, 120, "Local view", "Top risk-increasing contributions become reviewer reason codes.", "blue");
  addCard(slide, 790, 460, 436, 138, "Mathematical check", `Maximum additivity error\n${executive.linear_shap_max_additivity_error.toExponential(2)} log-odds`, "green");
  addFooter(slide, 13);
  addNotes(slide, ["artifacts/explanations/global_linear_shap_importance.csv", "artifacts/plots/global_linear_shap.png", "https://shap.readthedocs.io/en/latest/", "src/credit_risk/explainability.py"]);
}

// 14 — local explanation
{
  const slide = newSlide();
  addTitle(slide, "A reason code is evidence for review — not the final notice", 14);
  addCard(slide, M, 188, 506, 404, "Example reviewer output", "PD 14.7% • Score 604 • Band D\nRecommendation: REFER\n\n1  RISK_UP_DEBT_TO_INCOME\n2  RISK_UP_REVOLVING_UTILIZATION\n3  RISK_UP_BUREAU_SCORE\n4  RISK_UP_DELINQUENCIES_36M", "blue");
  addText(slide, "Required interpretation contract", 620, 190, 606, 40, { size: 25, bold: true });
  addBulletList(slide, [
    "Contribution is expressed in model log-odds, not causality.",
    "Only top risk-increasing drivers are shown to the reviewer.",
    "Protected attributes never appear in model reason codes.",
    "Operational notices require policy, legal and data-quality checks.",
    "Override and final rationale belong in a separate audit record.",
  ], 620, 252, 606, 330, { gap: 66, size: 17 });
  addFooter(slide, 14);
  addNotes(slide, ["docs/governance/explainability-standard.md", "src/credit_risk/service.py", "artifacts/explanations/oot_local_reason_codes.csv.gz"]);
}

// 15 — fairness
{
  const slide = newSlide();
  addTitle(slide, "The fairness review surfaces a real governance blocker", 15);
  await addImage(slide, "artifacts/plots/fairness_diagnostics.png", M, 182, 650, 390, "Approval rate by gender and age band");
  const gender = fairnessSummary.find((row) => row.protected_attribute === "gender");
  const age = fairnessSummary.find((row) => row.protected_attribute === "age_band");
  addKpi(slide, 750, 184, 224, "Gender DP gap", `${(Number(gender.demographic_parity_difference) * 100).toFixed(1)} pp`, "Diagnostic", "teal");
  addKpi(slide, 996, 184, 230, "Age-band DP gap", `${(Number(age.demographic_parity_difference) * 100).toFixed(1)} pp`, "Escalate", "red");
  addCard(slide, 750, 354, 476, 218, "Governance disposition", "GOVERNANCE REVIEW REQUIRED\n\nInvestigate legitimate feature pathways, sample composition, policy thresholds, proxy effects and jurisdiction-specific obligations before any external use.", "red");
  addFooter(slide, 15, "SYNTHETIC • FAIRNESS METRICS ARE DIAGNOSTIC");
  addNotes(slide, ["artifacts/metrics/fairness_summary.csv", "artifacts/plots/fairness_diagnostics.png", "https://fairlearn.org/main/user_guide/assessment/index.html", "docs/governance/fairness-assessment.md"]);
}

// 16 — monitoring
{
  const slide = newSlide();
  addTitle(slide, "Monitoring combines performance, drift and allocation signals", 16);
  await addImage(slide, "artifacts/plots/model_monitoring.png", M, 178, 720, 426, "Monthly model performance and PSI");
  addCard(slide, 810, 180, 416, 116, "Performance", "ROC AUC • Brier • observed default rate", "teal");
  addCard(slide, 810, 316, 416, 116, "Stability", "Score PSI • bureau-score PSI • DTI PSI", "blue");
  addCard(slide, 810, 452, 416, 152, "Action", "Green = observe\nAmber = investigate\nRed = restrict / rollback review", "amber");
  addFooter(slide, 16);
  addNotes(slide, ["artifacts/monitoring/monthly_monitoring.csv", "artifacts/plots/model_monitoring.png", "https://docs.evidentlyai.com/metrics/preset_data_drift", "docs/operations/monitoring-runbook.md"]);
}

// 17 — human oversight
{
  const slide = newSlide();
  addTitle(slide, "Human oversight is designed as an operating process", 17);
  const steps = [
    ["1", "Receive", "Application and validation evidence"],
    ["2", "Recommend", "PD, score, band and reason codes"],
    ["3", "Review", "Credit officer evaluates context"],
    ["4", "Decide", "Authorized action outside model"],
    ["5", "Record", "Rationale, override and notice"],
    ["6", "Learn", "Outcome, incident and monitoring feedback"],
  ];
  steps.forEach(([number, title, body], index) => {
    const row = Math.floor(index / 3);
    const col = index % 3;
    const x = M + col * 390;
    const y = 188 + row * 214;
    addCard(slide, x, y, 350, 176, `${number}  ${title}`, body, index === 2 || index === 3 ? "amber" : "neutral");
  });
  addFooter(slide, 17);
  addNotes(slide, ["docs/governance/human-oversight.md", "docs/governance/decision-policy.md", "https://www.nist.gov/itl/ai-risk-management-framework"]);
}

// 18 — operations/security
{
  const slide = newSlide();
  addTitle(slide, "Operational controls make the demo deployable without overstating readiness", 18);
  addCard(slide, M, 188, 350, 174, "API boundary", "Pydantic validation\nAPI-key option\nNo protected fields\nRecommendation-only response", "blue");
  addCard(slide, 465, 188, 350, 174, "Runtime hardening", "Non-root container\nRead-only filesystem\nDropped Linux capabilities\nHealth and readiness probes", "green");
  addCard(slide, 838, 188, 388, 174, "Observability", "Prometheus metrics\nGrafana dashboard\nAvailability / latency / error alerts", "teal");
  addCard(slide, M, 390, 350, 174, "Data controls", "Separate governance schema\nNo credentials committed\nSynthetic datasets only", "amber");
  addCard(slide, 465, 390, 350, 174, "CI security", "Ruff • tests • coverage\nCodeQL • pip-audit • Trivy\nDependabot", "blue");
  addCard(slide, 838, 390, 388, 174, "Model controls", "Versioned artifacts\nReproducible data hash\nSHAP identity gate\nMonitoring runbook", "green");
  addFooter(slide, 18);
  addNotes(slide, ["Dockerfile", "docker-compose.yml", "infra/kubernetes/deployment.yaml", ".github/workflows/ci.yml", ".github/workflows/security.yml", "https://prometheus.io/docs/practices/instrumentation/"]);
}

// 19 — roadmap
{
  const slide = newSlide();
  addTitle(slide, "A disciplined roadmap leads from portfolio demo to controlled pilot", 19);
  const phases = [
    ["Now", "Portfolio evidence", "Synthetic data\nTemporal validation\nGovernance pack"],
    ["Gate 1", "Independent review", "Reproduce metrics\nChallenge assumptions\nFairness investigation"],
    ["Gate 2", "Legal & policy", "Jurisdiction mapping\nDisclosure design\nOverride authority"],
    ["Gate 3", "Shadow pilot", "No-action scoring\nDrift baselines\nIncident testing"],
    ["Only then", "Controlled use", "Approval committee\nRestricted scope\nOngoing validation"],
  ];
  phases.forEach(([phase, title, body], index) => {
    const x = M + index * 236;
    addText(slide, phase, x, 190, 204, 28, { size: 15, bold: true, color: index === 4 ? C.red : C.teal });
    addRule(slide, x, 230, 204, index === 4 ? C.red : C.teal, 6);
    addText(slide, title, x, 258, 204, 54, { size: 21, bold: true });
    addText(slide, body, x, 336, 204, 96, { size: 16, color: C.slate });
    if (index < 4) addRule(slide, x + 204, 230, 32, C.rule, 3);
  });
  addBox(slide, M, 500, 1148, 96, C.redLight, "none");
  addText(slide, "CURRENT DISPOSITION", M + 22, 520, 230, 28, { size: 15, bold: true, color: C.red });
  addText(slide, "Portfolio-complete; not approved for real lending use because fairness and external-validity work remain open.", M + 270, 516, 920, 52, { size: 20, bold: true });
  addFooter(slide, 19);
  addNotes(slide, ["docs/governance/model-validation-report.md", "docs/governance/fairness-assessment.md", "docs/operations/production-readiness-checklist.md"]);
}

// 20 — Turkish summary / close, adapted from Codex Grid closing layout.
{
  const slide = newSlide();
  addRule(slide, 0, 0, 1280, C.teal, 12);
  addText(slide, "TÜRKÇE YÖNETİCİ ÖZETİ", M, 46, 500, 30, { size: 16, bold: true, color: C.teal });
  addText(slide, "Şeffaf model.\nKontrollü politika.\nİnsan kararı.", M, 152, 620, 220, { size: 48, bold: true });
  addText(
    slide,
    `48.000 sentetik başvuru üzerinde OOT AUC ${executive.oot_roc_auc.toFixed(3)} ve Gini ${executive.oot_gini.toFixed(3)} elde edildi. PD, risk bandı, SHAP neden kodları ve aylık izleme tek bir yönetişim zincirinde birleştirildi.`,
    M,
    420,
    660,
    122,
    { size: 21, color: C.slate },
  );
  addCard(slide, 770, 150, 456, 182, "Güçlü taraf", "Tekrarlanabilir analitik, kalibrasyon, açıklanabilirlik ve operasyonel kontroller.", "green");
  addCard(slide, 770, 354, 456, 182, "Açık bulgu", "Yaş gruplarında belirgin tahsis farkı: gerçek kullanım öncesi yönetişim incelemesi zorunlu.", "red");
  addText(slide, "github.com/muratmiracg-dev", 770, 590, 456, 30, { size: 18, bold: true, color: C.teal });
  addText(slide, "Thank you • Teşekkürler", M, 630, 500, 34, { size: 18, bold: true, color: C.ink });
  addNotes(slide, ["artifacts/metrics/executive_summary.json", "artifacts/metrics/fairness_summary.csv"], "Close on credibility: the project is strong because it reports the blocker instead of hiding it.");
}

await fs.mkdir(RENDERED, { recursive: true });
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(RENDERED, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(RENDERED, `${stem}.layout.json`), await layout.text(), "utf8");
}

const montage = await presentation.export({ format: "webp", montage: true, scale: 0.35 });
await fs.writeFile(path.join(OUTPUT, "credit_risk_deck_montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(path.join(OUTPUT, "credit_risk_executive_deck.pptx"));

const inspection = await presentation.inspect({
  kind: "slide,textbox,shape,image,chart,notes,layout",
  maxChars: 20000,
});
await fs.writeFile(path.join(OUTPUT, "presentation-inspect.ndjson"), inspection.ndjson, "utf8");
console.log(`Presentation written to ${path.join(OUTPUT, "credit_risk_executive_deck.pptx")}`);
