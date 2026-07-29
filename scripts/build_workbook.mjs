#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const artifactModule = path.join(
  process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,
  "@oai/artifact-tool/dist/artifact_tool.mjs",
);
const { SpreadsheetFile, Workbook } = await import(`file://${artifactModule}`);

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUTPUT = path.join(ROOT, "reports/workbook");
const RENDERED = path.join(OUTPUT, "rendered");
const COLORS = {
  navy: "#0B1F3A",
  teal: "#0F766E",
  blue: "#2563EB",
  pale: "#E8EEF6",
  amber: "#D97706",
  red: "#B42318",
  green: "#15803D",
  slate: "#64748B",
  line: "#CBD5E1",
  white: "#FFFFFF",
  input: "#FFF7CC",
};

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  const headers = rows[0];
  return rows.slice(1).filter((values) => values.length > 1).map((values) =>
    Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])),
  );
}

async function readCsv(relativePath) {
  return parseCsv(await fs.readFile(path.join(ROOT, relativePath), "utf8"));
}

async function readJson(relativePath) {
  return JSON.parse(await fs.readFile(path.join(ROOT, relativePath), "utf8"));
}

function addTitle(sheet, title, subtitle, endColumn = "H") {
  sheet.mergeCells(`A1:${endColumn}1`);
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${endColumn}1`).format = {
    fill: COLORS.navy,
    font: { bold: true, color: COLORS.white, size: 20 },
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${endColumn}1`).format.rowHeight = 34;
  sheet.mergeCells(`A2:${endColumn}2`);
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${endColumn}2`).format = {
    fill: COLORS.pale,
    font: { color: COLORS.slate, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange(`A2:${endColumn}2`).format.rowHeight = 34;
}

function styleHeader(range) {
  range.format = {
    fill: COLORS.teal,
    font: { bold: true, color: COLORS.white },
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: COLORS.teal },
  };
  range.format.rowHeight = 28;
}

function styleTable(range) {
  range.format = {
    font: { color: "#111827", size: 10 },
    borders: {
      insideHorizontal: { style: "thin", color: "#E2E8F0" },
      bottom: { style: "thin", color: COLORS.line },
    },
    verticalAlignment: "center",
  };
}

function addSection(sheet, row, title, endColumn = "H") {
  sheet.mergeCells(`A${row}:${endColumn}${row}`);
  sheet.getRange(`A${row}`).values = [[title]];
  sheet.getRange(`A${row}:${endColumn}${row}`).format = {
    fill: COLORS.navy,
    font: { bold: true, color: COLORS.white, size: 11 },
  };
}

function addKpi(sheet, range, label, formula, numberFormat) {
  const [start, end] = range.split(":");
  const startCol = start.match(/[A-Z]+/)[0];
  const startRow = Number(start.match(/\d+/)[0]);
  const endCol = end.match(/[A-Z]+/)[0];
  const endRow = Number(end.match(/\d+/)[0]);
  sheet.mergeCells(`${startCol}${startRow}:${endCol}${startRow}`);
  sheet.mergeCells(`${startCol}${startRow + 1}:${endCol}${endRow}`);
  sheet.getRange(`${startCol}${startRow}`).values = [[label]];
  if (typeof formula === "string" && formula.startsWith("=")) {
    sheet.getRange(`${startCol}${startRow + 1}`).formulas = [[formula]];
  } else {
    sheet.getRange(`${startCol}${startRow + 1}`).values = [[Number(formula)]];
  }
  sheet.getRange(range).format = {
    fill: COLORS.pale,
    borders: { preset: "outside", style: "thin", color: COLORS.line },
  };
  sheet.getRange(`${startCol}${startRow}`).format = {
    font: { bold: true, color: COLORS.slate, size: 10 },
    fill: COLORS.pale,
  };
  sheet.getRange(`${startCol}${startRow + 1}`).format = {
    font: { bold: true, color: COLORS.navy, size: 20 },
    fill: COLORS.pale,
    numberFormat,
    verticalAlignment: "center",
  };
}

function addSourceComment(workbook, sheet, cell, text) {
  workbook.comments.addThread({ cell: sheet.getRange(cell) }, text);
}

const executive = await readJson("artifacts/metrics/executive_summary.json");
const comparison = await readCsv("artifacts/metrics/model_comparison.csv");
const riskBands = await readCsv("artifacts/metrics/risk_band_summary.csv");
const deciles = await readCsv("artifacts/metrics/risk_deciles.csv");
const monitoring = await readCsv("artifacts/monitoring/monthly_monitoring.csv");
const fairness = await readCsv("artifacts/metrics/fairness_by_group.csv");
const fairnessSummary = await readCsv("artifacts/metrics/fairness_summary.csv");
const shap = await readCsv("artifacts/explanations/global_linear_shap_importance.csv");
const scored = await readCsv("data/samples/scored_applications_sample.csv");
const quality = await readCsv("artifacts/metrics/data_quality_checks.csv");
const scenarios = await readCsv("artifacts/metrics/policy_scenarios.csv");

const workbook = Workbook.create();
workbook.comments.setSelf({ displayName: "Aurelia Model Risk Analytics" });

const sheetNames = [
  "Cover",
  "Executive Summary",
  "Policy Simulator",
  "Model Comparison",
  "Risk Bands",
  "Risk Deciles",
  "Monthly Monitoring",
  "Fairness Review",
  "SHAP Drivers",
  "Scored Sample",
  "Data Quality",
  "Assumptions",
  "Sources & Audit",
  "Checks",
];
for (const name of sheetNames) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
}

// Cover
{
  const sheet = workbook.worksheets.getItem("Cover");
  sheet.mergeCells("A1:H3");
  sheet.getRange("A1").values = [["Banking Credit Risk & Explainable\nLoan Decisioning Platform"]];
  sheet.getRange("A1:H3").format = {
    fill: COLORS.navy,
    font: { bold: true, color: COLORS.white, size: 24 },
    verticalAlignment: "center",
    wrapText: true,
  };
  sheet.mergeCells("A5:H6");
  sheet.getRange("A5").values = [[
    "A formula-driven decision workbench for a deterministic synthetic retail lending portfolio. "
    + "All outputs are recommendations for authorized human review; no automated production decision is permitted.",
  ]];
  sheet.getRange("A5:H6").format = {
    fill: COLORS.pale,
    font: { color: COLORS.navy, size: 12 },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange("A8:B15").values = [
    ["Workbook version", "1.0.0"],
    ["Portfolio", "Aurelia Bank (fictional)"],
    ["Applications", executive.synthetic_applications],
    ["Development / validation / OOT", `${executive.development_applications} / ${executive.validation_applications} / ${executive.out_of_time_applications}`],
    ["Champion", "Logistic regression"],
    ["Protected attributes", "Excluded from model; fairness audit only"],
    ["Model scope", "Decision support only"],
    ["Model status", "Governance review required before any real use"],
  ];
  styleTable(sheet.getRange("A8:B15"));
  sheet.getRange("A8:A15").format.font = { bold: true, color: COLORS.slate };
  addSection(sheet, 17, "How to use this workbook", "H");
  sheet.getRange("A18:H22").values = [
    ["1", "Change policy assumptions in yellow cells on the Assumptions sheet.", null, null, null, null, null, null],
    ["2", "Review formula-driven decisions and expected loss in Policy Simulator.", null, null, null, null, null, null],
    ["3", "Use Model Comparison, Risk Deciles, SHAP and Monitoring as validation evidence.", null, null, null, null, null, null],
    ["4", "Treat Fairness Review signals as mandatory governance inputs, not legal conclusions.", null, null, null, null, null, null],
    ["5", "Confirm every check is PASS before circulating the workbook.", null, null, null, null, null, null],
  ];
  for (let row = 18; row <= 22; row += 1) sheet.mergeCells(`B${row}:H${row}`);
  styleTable(sheet.getRange("A18:H22"));
  sheet.getRange("A1:H24").format.columnWidth = 16;
  sheet.getRange("A1").format.columnWidth = 14;
  sheet.getRange("B1:H24").format.columnWidth = 18;
  sheet.getRange("A24:H24").merge();
  sheet.getRange("A24").values = [["Synthetic data • Educational portfolio project • Not financial, legal, accounting or lending advice"]];
  sheet.getRange("A24:H24").format = { font: { italic: true, color: COLORS.red, size: 9 } };
}

// Assumptions first so all cross-sheet formulas resolve.
{
  const sheet = workbook.worksheets.getItem("Assumptions");
  addTitle(sheet, "Governed assumptions", "Blue text / yellow fill = editable input. All scenario formulas reference this sheet.", "F");
  addSection(sheet, 4, "Decision policy", "F");
  sheet.getRange("A5:C12").values = [
    ["Input", "Value", "Control / interpretation"],
    ["Approve maximum PD", 0.10, "Below this boundary = approve recommendation"],
    ["Refer maximum PD", 0.22, "At or above approve boundary and below this boundary = refer"],
    ["LGD assumption", 0.45, "Illustrative unsecured loss-given-default"],
    ["Score anchor", 650, "Score at anchor PD"],
    ["Anchor PD", 0.10, "PD corresponding to score anchor"],
    ["Points to double odds", 50, "Score scaling convention"],
    ["Currency", "TRY", "Display and scenario reporting only"],
  ];
  styleHeader(sheet.getRange("A5:C5"));
  styleTable(sheet.getRange("A6:C12"));
  sheet.getRange("B6:B12").format = {
    fill: COLORS.input,
    font: { color: "#0000FF" },
    borders: { preset: "outside", style: "thin", color: COLORS.amber },
  };
  sheet.getRange("B6:B8").format.numberFormat = "0.0%";
  sheet.getRange("B9:B11").format.numberFormat = "0";
  sheet.getRange("B6:B8").dataValidation = {
    rule: { type: "decimal", operator: "between", formula1: 0, formula2: 1 },
  };
  addSection(sheet, 14, "Monitoring triage levels", "F");
  sheet.getRange("A15:C20").values = [
    ["Input", "Value", "Interpretation"],
    ["Score PSI warning", 0.10, "Internal triage level; not a regulatory threshold"],
    ["Score PSI critical", 0.25, "Escalate and investigate"],
    ["AUC drop warning", 0.03, "Versus validation baseline"],
    ["AUC drop critical", 0.05, "Escalate and consider rollback"],
    ["Fairness difference triage", 0.10, "Internal signal only; not a legal standard"],
  ];
  styleHeader(sheet.getRange("A15:C15"));
  styleTable(sheet.getRange("A16:C20"));
  sheet.getRange("B16:B20").format = {
    fill: COLORS.input,
    font: { color: "#0000FF" },
    numberFormat: "0.0%",
  };
  sheet.freezePanes.freezeRows(2);
  sheet.getRange("A1:A20").format.columnWidth = 28;
  sheet.getRange("B1:B20").format.columnWidth = 18;
  sheet.getRange("C1:C20").format.columnWidth = 55;
}

// Policy Simulator
{
  const sheet = workbook.worksheets.getItem("Policy Simulator");
  addTitle(sheet, "Policy simulator", "Edit policy thresholds on Assumptions. Decisions and expected loss below recalculate with formulas.", "I");
  addKpi(sheet, "A4:B6", "Approve recommendation rate", '=COUNTIF($E$11:$E$260,"APPROVE_RECOMMENDATION")/COUNTA($A$11:$A$260)', "0.0%");
  addKpi(sheet, "C4:D6", "Human review rate", '=COUNTIF($F$11:$F$260,"YES")/COUNTA($A$11:$A$260)', "0.0%");
  addKpi(sheet, "E4:F6", "Approved observed DR", '=IFERROR(AVERAGEIF($E$11:$E$260,"APPROVE_RECOMMENDATION",$D$11:$D$260),0)', "0.0%");
  addKpi(sheet, "G4:I6", "Illustrative expected loss", "=SUM($G$11:$G$260)", '₺#,##0;[Red](₺#,##0);-');
  const headers = ["Application ID", "Predicted PD", "Requested Amount", "Actual Default", "Formula Decision", "Human Review", "Expected Loss", "Risk Band", "Credit Score"];
  sheet.getRange("A10:I10").values = [headers];
  styleHeader(sheet.getRange("A10:I10"));
  const sourceRows = scored.slice(0, 250).map((row) => [
    row.application_id,
    Number(row.predicted_pd),
    Number(row.requested_amount),
    Number(row.default_12m),
    null,
    null,
    null,
    row.risk_band,
    Number(row.credit_score),
  ]);
  sheet.getRange("A11:I260").values = sourceRows;
  sheet.getRange("E11").formulas = [['=IF(B11<Assumptions!$B$6,"APPROVE_RECOMMENDATION",IF(B11<Assumptions!$B$7,"REFER","DECLINE_RECOMMENDATION"))']];
  sheet.getRange("E11:E260").fillDown();
  sheet.getRange("F11").formulas = [['=IF(E11="APPROVE_RECOMMENDATION","NO","YES")']];
  sheet.getRange("F11:F260").fillDown();
  sheet.getRange("G11").formulas = [["=B11*Assumptions!$B$8*C11"]];
  sheet.getRange("G11:G260").fillDown();
  styleTable(sheet.getRange("A11:I260"));
  sheet.getRange("B11:B260").format.numberFormat = "0.0%";
  sheet.getRange("C11:C260").format.numberFormat = '₺#,##0;[Red](₺#,##0);-';
  sheet.getRange("D11:D260").format.numberFormat = "0";
  sheet.getRange("G11:G260").format.numberFormat = '₺#,##0;[Red](₺#,##0);-';
  sheet.getRange("I11:I260").format.numberFormat = "0";
  sheet.getRange("E11:G260").format.font = { color: "#000000" };
  sheet.getRange("E11:E260").conditionalFormats.add("containsText", { text: "DECLINE", format: { fill: "#FEE2E2", font: { color: COLORS.red } } });
  sheet.getRange("E11:E260").conditionalFormats.add("containsText", { text: "REFER", format: { fill: "#FEF3C7", font: { color: COLORS.amber } } });
  sheet.getRange("E11:E260").conditionalFormats.add("containsText", { text: "APPROVE", format: { fill: "#DCFCE7", font: { color: COLORS.green } } });
  sheet.freezePanes.freezeRows(10);
  sheet.freezePanes.freezeColumns(1);
  const widths = [20, 14, 18, 14, 28, 15, 18, 11, 12];
  widths.forEach((width, index) => { sheet.getRangeByIndexes(0, index, 260, 1).format.columnWidth = width; });
}

// Executive Summary
{
  const sheet = workbook.worksheets.getItem("Executive Summary");
  addTitle(sheet, "Executive credit risk control tower", "Actual metrics from the deterministic OOT portfolio; policy KPIs link to the formula-driven simulator.", "L");
  addKpi(sheet, "A4:C6", "OOT ROC AUC", "='Model Comparison'!B9", "0.000");
  addKpi(sheet, "D4:F6", "OOT Gini", "='Model Comparison'!C9", "0.000");
  addKpi(sheet, "G4:I6", "Approval recommendation", "='Policy Simulator'!A5", "0.0%");
  addKpi(sheet, "J4:L6", "Human review", "='Policy Simulator'!C5", "0.0%");
  addKpi(sheet, "A8:C10", "OOT default rate", executive.oot_default_rate.toString(), "0.0%");
  addKpi(sheet, "D8:F10", "OOT Brier", executive.oot_brier.toString(), "0.000");
  addKpi(sheet, "G8:I10", "Max monthly PSI", executive.maximum_monthly_score_psi.toString(), "0.000");
  addKpi(sheet, "J8:L10", "SHAP additivity error", executive.linear_shap_max_additivity_error.toString(), "0.0E+00");
  addSection(sheet, 12, "Executive interpretation", "L");
  sheet.getRange("A13:L17").values = [
    ["Finding", "Evidence", "Management implication", null, null, null, null, null, null, null, null, null],
    ["Discrimination", `OOT AUC ${executive.oot_roc_auc.toFixed(3)}; Gini ${executive.oot_gini.toFixed(3)}`, "Meets the project gate; independent validation remains required.", null, null, null, null, null, null, null, null, null],
    ["Calibration", `Slope ${executive.oot_calibration_slope.toFixed(3)}; Brier ${executive.oot_brier.toFixed(3)}`, "PDs are fit for this synthetic sample; monitor drift before policy use.", null, null, null, null, null, null, null, null, null],
    ["Fairness", `Maximum DP difference ${executive.fairness_max_demographic_parity_difference.toFixed(1)}%`, "Age-band allocation signal requires investigation and governance review.", null, null, null, null, null, null, null, null, null],
    ["Scope", "Synthetic, recommendation-only", "No production decision, pricing, limit assignment or adverse action.", null, null, null, null, null, null, null, null, null],
  ];
  for (let row = 13; row <= 17; row += 1) {
    if (row === 13) {
      sheet.mergeCells(`C${row}:L${row}`);
    } else {
      sheet.mergeCells(`C${row}:L${row}`);
    }
  }
  styleHeader(sheet.getRange("A13:L13"));
  styleTable(sheet.getRange("A14:L17"));
  sheet.getRange("A14:L17").format.wrapText = true;
  sheet.getRange("A14:L17").format.rowHeight = 34;
  sheet.getRange("A1:A20").format.columnWidth = 23;
  sheet.getRange("B1:B20").format.columnWidth = 25;
  sheet.getRange("C1:L20").format.columnWidth = 14;
  addSourceComment(workbook, sheet, "A4", "Source: artifacts/metrics/executive_summary.json; generated by scripts/run_pipeline.py");
}

function populateDataSheet(name, title, subtitle, rows, columns, formats = {}) {
  const sheet = workbook.worksheets.getItem(name);
  const endColumn = String.fromCharCode(64 + Math.min(columns.length, 26));
  addTitle(sheet, title, subtitle, endColumn);
  sheet.getRange(`A4:${endColumn}4`).values = [columns.map((column) => column.label)];
  styleHeader(sheet.getRange(`A4:${endColumn}4`));
  const values = rows.map((row) => columns.map((column) => {
    const raw = row[column.key];
    if (column.type === "number") return Number(raw);
    return raw;
  }));
  if (values.length) sheet.getRange(`A5:${endColumn}${4 + values.length}`).values = values;
  styleTable(sheet.getRange(`A5:${endColumn}${4 + values.length}`));
  columns.forEach((column, index) => {
    const letter = String.fromCharCode(65 + index);
    sheet.getRange(`${letter}5:${letter}${4 + values.length}`).format.numberFormat = formats[column.key] || (column.type === "number" ? "0.000" : "@");
    sheet.getRangeByIndexes(0, index, Math.max(8, 4 + values.length), 1).format.columnWidth = column.width || 18;
  });
  sheet.freezePanes.freezeRows(4);
  return sheet;
}

const modelSheet = populateDataSheet(
  "Model Comparison",
  "Champion and challenger comparison",
  "Temporal validation window: 2024-H2. Champion selection combines performance, calibration and auditability.",
  comparison,
  [
    { key: "model", label: "Model", width: 31 },
    { key: "roc_auc", label: "ROC AUC", type: "number", width: 13 },
    { key: "gini", label: "Gini", type: "number", width: 13 },
    { key: "pr_auc", label: "PR AUC", type: "number", width: 13 },
    { key: "ks", label: "KS", type: "number", width: 13 },
    { key: "brier", label: "Brier", type: "number", width: 13 },
    { key: "calibration_slope", label: "Calibration slope", type: "number", width: 18 },
    { key: "deployment_status", label: "Status", width: 16 },
    { key: "explainability", label: "Explainability", width: 32 },
  ],
);
modelSheet.getRange("B5:G7").format.numberFormat = "0.000";
modelSheet.getRange("A9:I9").values = [[
  "logistic_regression",
  executive.oot_roc_auc,
  executive.oot_gini,
  executive.oot_pr_auc,
  executive.oot_ks,
  executive.oot_brier,
  executive.oot_calibration_slope,
  "OOT CHAMPION",
  "Exact additive Linear SHAP",
]];
styleTable(modelSheet.getRange("A9:I9"));
modelSheet.getRange("B9:G9").format.numberFormat = "0.000";
modelSheet.getRange("H5:H9").conditionalFormats.add("containsText", { text: "CHAMPION", format: { fill: "#DCFCE7", font: { color: COLORS.green, bold: true } } });
const modelChart = modelSheet.charts.add("bar", modelSheet.getRange("A4:B7"));
modelChart.title = "Validation ROC AUC";
modelChart.hasLegend = false;
modelChart.yAxis = { numberFormatCode: "0.000", min: 0.65, max: 0.76 };
modelChart.setPosition("K4", "R17");

const riskSheet = populateDataSheet(
  "Risk Bands",
  "Risk band performance",
  "A-F bands are policy communication layers over continuous PD; they are not regulatory grades.",
  riskBands,
  [
    { key: "risk_band", label: "Risk Band", width: 12 },
    { key: "applications", label: "Applications", type: "number", width: 16 },
    { key: "exposure", label: "Exposure", type: "number", width: 18 },
    { key: "average_pd", label: "Average PD", type: "number", width: 15 },
    { key: "observed_default_rate", label: "Observed DR", type: "number", width: 15 },
    { key: "expected_loss", label: "Expected Loss", type: "number", width: 18 },
  ],
  { applications: "#,##0", exposure: '₺#,##0', average_pd: "0.0%", observed_default_rate: "0.0%", expected_loss: '₺#,##0' },
);
const riskChart = riskSheet.charts.add("bar", riskSheet.getRange("A4:B10"));
riskChart.title = "OOT applications by risk band";
riskChart.hasLegend = false;
riskChart.setPosition("H4", "O18");

const decileSheet = populateDataSheet(
  "Risk Deciles",
  "Risk decile validation",
  "Decile 1 contains the highest predicted risk. Observed and predicted rates support rank ordering and calibration review.",
  deciles,
  [
    { key: "risk_decile", label: "Risk Decile", type: "number", width: 13 },
    { key: "applications", label: "Applications", type: "number", width: 15 },
    { key: "defaults", label: "Defaults", type: "number", width: 12 },
    { key: "observed_default_rate", label: "Observed DR", type: "number", width: 15 },
    { key: "average_predicted_pd", label: "Predicted PD", type: "number", width: 15 },
    { key: "cumulative_default_capture", label: "Cumulative Capture", type: "number", width: 20 },
    { key: "lift_vs_portfolio", label: "Lift", type: "number", width: 12 },
  ],
  { risk_decile: "0", applications: "#,##0", defaults: "#,##0", observed_default_rate: "0.0%", average_predicted_pd: "0.0%", cumulative_default_capture: "0.0%", lift_vs_portfolio: "0.00x" },
);
const decileChart = decileSheet.charts.add("line", decileSheet.getRange("A4:E14"));
decileChart.title = "Observed and predicted default rate by decile";
decileChart.yAxis = { numberFormatCode: "0.0%" };
decileChart.setPosition("I4", "Q19");

const monitorSheet = populateDataSheet(
  "Monthly Monitoring",
  "Monthly model monitoring",
  "OOT 2025 monitoring: discrimination, calibration, approval allocation and distribution stability.",
  monitoring,
  [
    { key: "monitoring_month", label: "Month", width: 13 },
    { key: "applications", label: "Applications", type: "number", width: 14 },
    { key: "observed_default_rate", label: "Observed DR", type: "number", width: 14 },
    { key: "average_predicted_pd", label: "Average PD", type: "number", width: 14 },
    { key: "roc_auc", label: "ROC AUC", type: "number", width: 12 },
    { key: "brier", label: "Brier", type: "number", width: 12 },
    { key: "approval_rate", label: "Approval Rate", type: "number", width: 15 },
    { key: "score_psi", label: "Score PSI", type: "number", width: 12 },
    { key: "alert_status", label: "Alert", width: 12 },
  ],
  { applications: "#,##0", observed_default_rate: "0.0%", average_predicted_pd: "0.0%", roc_auc: "0.000", brier: "0.000", approval_rate: "0.0%", score_psi: "0.000" },
);
monitorSheet.getRange("I5:I16").conditionalFormats.add("containsText", { text: "RED", format: { fill: "#FEE2E2", font: { color: COLORS.red, bold: true } } });
monitorSheet.getRange("I5:I16").conditionalFormats.add("containsText", { text: "AMBER", format: { fill: "#FEF3C7", font: { color: COLORS.amber, bold: true } } });
monitorSheet.getRange("I5:I16").conditionalFormats.add("containsText", { text: "GREEN", format: { fill: "#DCFCE7", font: { color: COLORS.green, bold: true } } });
const monitorChart = monitorSheet.charts.add("line", monitorSheet.getRange("A4:A16").offset(0, 0).resize(13, 8));
monitorChart.setData(monitorSheet.getRange("A4:A16").offset(0, 0).resize(13, 8));
monitorChart.title = "Monthly OOT metrics";
monitorChart.setPosition("K4", "S19");

const fairnessSheet = populateDataSheet(
  "Fairness Review",
  "Fairness and allocation review",
  "Protected attributes are excluded from training and scoring. Metrics are diagnostic and do not establish legal fairness.",
  fairness,
  [
    { key: "protected_attribute", label: "Attribute", width: 18 },
    { key: "group", label: "Group", width: 16 },
    { key: "applications", label: "Applications", type: "number", width: 14 },
    { key: "observed_default_rate", label: "Observed DR", type: "number", width: 14 },
    { key: "average_predicted_pd", label: "Average PD", type: "number", width: 14 },
    { key: "approval_rate", label: "Approval Rate", type: "number", width: 15 },
    { key: "good_applicant_approval_rate", label: "Good Applicant Approval", type: "number", width: 22 },
    { key: "roc_auc", label: "ROC AUC", type: "number", width: 13 },
    { key: "brier", label: "Brier", type: "number", width: 13 },
  ],
  { applications: "#,##0", observed_default_rate: "0.0%", average_predicted_pd: "0.0%", approval_rate: "0.0%", good_applicant_approval_rate: "0.0%", roc_auc: "0.000", brier: "0.000" },
);
const fairnessStart = 7 + fairness.length;
addSection(fairnessSheet, fairnessStart, "Disparity summary and governance disposition", "I");
fairnessSheet.getRange(`A${fairnessStart + 1}:E${fairnessStart + 1}`).values = [[
  "Attribute", "DP Difference", "EO Difference", "Diagnostic Status", "Interpretation",
]];
styleHeader(fairnessSheet.getRange(`A${fairnessStart + 1}:E${fairnessStart + 1}`));
fairnessSheet.getRange(`A${fairnessStart + 2}:E${fairnessStart + 1 + fairnessSummary.length}`).values = fairnessSummary.map((row) => [
  row.protected_attribute,
  Number(row.demographic_parity_difference),
  Number(row.equal_opportunity_difference),
  row.diagnostic_status,
  row.interpretation,
]);
styleTable(fairnessSheet.getRange(`A${fairnessStart + 2}:E${fairnessStart + 1 + fairnessSummary.length}`));
fairnessSheet.getRange(`B${fairnessStart + 2}:C${fairnessStart + 1 + fairnessSummary.length}`).format.numberFormat = "0.0%";
fairnessSheet.getRange(`E${fairnessStart + 2}:E${fairnessStart + 1 + fairnessSummary.length}`).format.wrapText = true;
fairnessSheet.getRange(`D${fairnessStart + 2}:D${fairnessStart + 1 + fairnessSummary.length}`).conditionalFormats.add("containsText", { text: "REVIEW", format: { fill: "#FEE2E2", font: { color: COLORS.red, bold: true } } });

const shapSheet = populateDataSheet(
  "SHAP Drivers",
  "Global Linear SHAP drivers",
  "Exact additive contributions in log-odds under the feature-independence assumption. Explanations are non-causal.",
  shap.slice(0, 20),
  [
    { key: "feature", label: "Feature", width: 34 },
    { key: "mean_abs_shap_log_odds", label: "Mean |SHAP|", type: "number", width: 16 },
    { key: "mean_shap_log_odds", label: "Mean SHAP", type: "number", width: 15 },
    { key: "coefficient", label: "Coefficient", type: "number", width: 14 },
  ],
  { mean_abs_shap_log_odds: "0.000", mean_shap_log_odds: "0.000", coefficient: "0.000" },
);
const shapChart = shapSheet.charts.add("bar", shapSheet.getRange("A4:B16"));
shapChart.title = "Top global model drivers";
shapChart.hasLegend = false;
shapChart.setPosition("F4", "N20");

const sampleColumns = [
  "application_id", "application_date", "channel", "region", "employment_type",
  "monthly_income", "requested_amount", "debt_to_income", "bureau_score",
  "predicted_pd", "credit_score", "risk_band", "recommendation", "expected_loss",
  "default_12m",
].map((key) => ({
  key,
  label: key.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase()),
  type: ["monthly_income", "requested_amount", "debt_to_income", "bureau_score", "predicted_pd", "credit_score", "expected_loss", "default_12m"].includes(key) ? "number" : "text",
  width: key === "recommendation" ? 27 : key === "application_id" ? 18 : 16,
}));
const scoredSheet = populateDataSheet(
  "Scored Sample",
  "Scored application sample",
  "Reviewer-friendly 250-row sample. Full synthetic and scored portfolios are committed as compressed CSV files.",
  scored,
  sampleColumns,
  { monthly_income: '₺#,##0', requested_amount: '₺#,##0', debt_to_income: "0.0%", bureau_score: "0", predicted_pd: "0.0%", credit_score: "0", expected_loss: '₺#,##0', default_12m: "0" },
);
scoredSheet.freezePanes.freezeColumns(2);

const qualitySheet = populateDataSheet(
  "Data Quality",
  "Critical data-quality and safety controls",
  "Every control must pass before the analytical package can be circulated.",
  quality,
  [
    { key: "check_id", label: "Check ID", width: 13 },
    { key: "control", label: "Control", width: 35 },
    { key: "actual", label: "Actual", width: 18 },
    { key: "expected", label: "Expected", width: 18 },
    { key: "status", label: "Status", width: 13 },
  ],
);
qualitySheet.getRange(`E5:E${4 + quality.length}`).conditionalFormats.add("containsText", { text: "PASS", format: { fill: "#DCFCE7", font: { color: COLORS.green, bold: true } } });

// Sources & Audit
{
  const sheet = workbook.worksheets.getItem("Sources & Audit");
  addTitle(sheet, "Sources, lineage and limitations", "Primary references support the control design; they do not certify compliance.", "F");
  sheet.getRange("A4:F4").values = [["ID", "Source / artifact", "URL or path", "Used for", "As of", "Limitation"]];
  styleHeader(sheet.getRange("A4:F4"));
  const sources = [
    ["SRC-01", "Basel Committee — Principles for management of credit risk", "https://www.bis.org/bcbs/publ/d595.pdf", "Credit granting, monitoring, controls", "2025", "Reference mapping only"],
    ["SRC-02", "EBA Guidelines on loan origination and monitoring", "https://www.eba.europa.eu/sites/default/files/document_library/Publications/Guidelines/2020/Guidelines%20on%20loan%20origination%20and%20monitoring/884283/EBA%20GL%202020%2006%20Final%20Report%20on%20GL%20on%20loan%20origination%20and%20monitoring.pdf", "Creditworthiness governance", "2020", "Jurisdiction-specific applicability required"],
    ["SRC-03", "NIST AI RMF 1.0", "https://www.nist.gov/itl/ai-risk-management-framework", "Govern, Map, Measure, Manage", "2023", "Voluntary framework"],
    ["SRC-04", "EU AI Act", "https://eur-lex.europa.eu/eli/reg/2024/1689/oj", "High-risk context and human oversight", "2024", "Legal advice required"],
    ["SRC-05", "IFRS 9 Financial Instruments", "https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/", "Expected credit loss terminology", "Current page", "Workbook EL is illustrative, not IFRS 9 compliant"],
    ["SRC-06", "SHAP documentation", "https://shap.readthedocs.io/en/latest/", "Linear SHAP interpretation", "Current docs", "Non-causal explanation"],
    ["SRC-07", "scikit-learn probability calibration", "https://scikit-learn.org/stable/modules/calibration.html", "Calibration diagnostics", "Current docs", "Implementation reference"],
    ["SRC-08", "Fairlearn assessment documentation", "https://fairlearn.org/main/user_guide/assessment/index.html", "Disaggregated fairness metrics", "Current docs", "Metrics do not define legal fairness"],
    ["ART-01", "Executive metrics", "artifacts/metrics/executive_summary.json", "Workbook KPI source", "Generated", "Synthetic"],
    ["ART-02", "Model comparison", "artifacts/metrics/model_comparison.csv", "Validation evidence", "Generated", "Synthetic"],
    ["ART-03", "Monthly monitoring", "artifacts/monitoring/monthly_monitoring.csv", "Drift and performance", "Generated", "Synthetic"],
    ["ART-04", "Fairness audit", "artifacts/metrics/fairness_summary.csv", "Governance signal", "Generated", "Synthetic"],
  ];
  sheet.getRange(`A5:F${4 + sources.length}`).values = sources;
  styleTable(sheet.getRange(`A5:F${4 + sources.length}`));
  sheet.getRange(`C5:C${4 + sources.length}`).format.font = { color: "#008000" };
  sheet.getRange(`A5:F${4 + sources.length}`).format.wrapText = true;
  sheet.getRange(`A5:F${4 + sources.length}`).format.rowHeight = 42;
  [14, 38, 62, 30, 16, 38].forEach((width, index) => { sheet.getRangeByIndexes(0, index, 20, 1).format.columnWidth = width; });
  sheet.freezePanes.freezeRows(4);
}

// Checks
{
  const sheet = workbook.worksheets.getItem("Checks");
  addTitle(sheet, "Workbook control checks", "Formula-driven assertions across assumptions, outputs and generated evidence.", "G");
  sheet.getRange("A4:G4").values = [["Check", "Actual", "Expected", "Difference", "Tolerance", "Status", "Fix hint"]];
  styleHeader(sheet.getRange("A4:G4"));
  sheet.getRange("A5:A12").values = [
    ["Approve threshold below refer threshold"],
    ["LGD within 0-100%"],
    ["Policy simulator row count"],
    ["Risk band applications equal OOT total"],
    ["Monitoring contains 12 months"],
    ["SHAP additivity error"],
    ["OOT AUC minimum gate"],
    ["Fairness review disposition surfaced"],
  ];
  sheet.getRange("B5:B12").formulas = [
    ["=Assumptions!B6"],
    ["=Assumptions!B8"],
    ["=COUNTA('Policy Simulator'!A11:A260)"],
    ["=SUM('Risk Bands'!B5:B10)"],
    ["=COUNTA('Monthly Monitoring'!A5:A16)"],
    [`=${executive.linear_shap_max_additivity_error}`],
    [`=${executive.oot_roc_auc}`],
    ['=COUNTIF(\'Fairness Review\'!D16:D17,"GOVERNANCE_REVIEW_REQUIRED")'],
  ];
  sheet.getRange("C5:C12").values = [[0.22], [1], [250], [executive.out_of_time_applications], [12], [0], [0.70], [1]];
  sheet.getRange("D5:D12").formulas = [
    ["=MAX(0,B5-C5)"],
    ["=MAX(0,B6-C6)"],
    ["=ABS(B7-C7)"],
    ["=ABS(B8-C8)"],
    ["=ABS(B9-C9)"],
    ["=ABS(B10-C10)"],
    ["=MAX(0,C11-B11)"],
    ["=MAX(0,C12-B12)"],
  ];
  sheet.getRange("E5:E12").values = [[0], [0], [0], [0], [0], [1e-10], [0], [0]];
  sheet.getRange("F5").formulas = [['=IF(Assumptions!B6<Assumptions!B7,"PASS","FAIL")']];
  sheet.getRange("F6").formulas = [['=IF(AND(B6>=0,B6<=C6),"PASS","FAIL")']];
  sheet.getRange("F7").formulas = [['=IF(D7<=E7,"PASS","FAIL")']];
  sheet.getRange("F8").formulas = [['=IF(D8<=E8,"PASS","FAIL")']];
  sheet.getRange("F9").formulas = [['=IF(D9<=E9,"PASS","FAIL")']];
  sheet.getRange("F10").formulas = [['=IF(B10<=E10,"PASS","FAIL")']];
  sheet.getRange("F11").formulas = [['=IF(B11>=C11,"PASS","FAIL")']];
  sheet.getRange("F12").formulas = [['=IF(B12>=C12,"PASS","FAIL")']];
  sheet.getRange("G5:G12").values = [
    ["Lower approve threshold or raise refer threshold"],
    ["Set LGD between 0% and 100%"],
    ["Restore 250 formula-driven sample rows"],
    ["Refresh the risk-band source table"],
    ["Refresh the monitoring source"],
    ["Rebuild explanations and validate additivity"],
    ["Redevelop or reject champion"],
    ["Keep governance-review finding visible"],
  ];
  styleTable(sheet.getRange("A5:G12"));
  sheet.getRange("B5:E12").format.numberFormat = "0.000";
  sheet.getRange("F5:F12").conditionalFormats.add("containsText", { text: "PASS", format: { fill: "#DCFCE7", font: { color: COLORS.green, bold: true } } });
  sheet.getRange("F5:F12").conditionalFormats.add("containsText", { text: "FAIL", format: { fill: "#FEE2E2", font: { color: COLORS.red, bold: true } } });
  addSection(sheet, 14, "Overall status", "G");
  sheet.mergeCells("A15:E16");
  sheet.mergeCells("F15:G16");
  sheet.getRange("A15").values = [["All workbook checks"]];
  sheet.getRange("F15").formulas = [['=IF(COUNTIF(F5:F12,"FAIL")=0,"PASS","FAIL")']];
  sheet.getRange("A15:G16").format = {
    fill: COLORS.pale,
    font: { bold: true, size: 18, color: COLORS.navy },
    verticalAlignment: "center",
  };
  sheet.getRange("F15:G16").conditionalFormats.add("containsText", { text: "PASS", format: { fill: "#DCFCE7", font: { color: COLORS.green, bold: true } } });
  [34, 16, 16, 16, 14, 14, 45].forEach((width, index) => { sheet.getRangeByIndexes(0, index, 18, 1).format.columnWidth = width; });
}

await fs.mkdir(RENDERED, { recursive: true });
const summary = await workbook.inspect({
  kind: "workbook,sheet,table,drawing",
  maxChars: 8000,
  tableMaxRows: 5,
  tableMaxCols: 8,
});
await fs.writeFile(path.join(OUTPUT, "workbook-inspect.ndjson"), summary.ndjson, "utf8");

for (const name of sheetNames) {
  const preview = await workbook.render({
    sheetName: name,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  const safe = name.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-");
  await fs.writeFile(
    path.join(RENDERED, `${safe}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(OUTPUT, "credit_risk_decision_workbench.xlsx"));
console.log(`Workbook written to ${path.join(OUTPUT, "credit_risk_decision_workbench.xlsx")}`);
