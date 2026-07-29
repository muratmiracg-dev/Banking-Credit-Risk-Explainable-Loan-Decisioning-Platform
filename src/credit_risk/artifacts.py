"""Artifact serialization and publication-quality analytical plots."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "credit-risk-matplotlib"),
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import roc_curve

NAVY = "#0B1F3A"
TEAL = "#0F766E"
BLUE = "#2563EB"
AMBER = "#D97706"
RED = "#B42318"
SLATE = "#64748B"
PALE = "#E8EEF6"


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value)!r}")


def write_json(payload: Any, path: str | Path) -> None:
    """Write stable, readable JSON."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelcolor": NAVY,
            "axes.edgecolor": "#CBD5E1",
            "xtick.color": SLATE,
            "ytick.color": SLATE,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": True,
            "grid.color": "#E2E8F0",
            "grid.linewidth": 0.6,
        }
    )


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_model_comparison(comparison: pd.DataFrame, path: Path) -> None:
    _style()
    ordered = comparison.sort_values("roc_auc")
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    colors = [TEAL if status == "CHAMPION" else BLUE for status in ordered["deployment_status"]]
    bars = ax.barh(ordered["model"], ordered["roc_auc"], color=colors)
    ax.set_xlim(max(0.5, ordered["roc_auc"].min() - 0.03), min(1, ordered["roc_auc"].max() + 0.03))
    ax.set_title("Validation ROC AUC — governed champion and challengers", loc="left")
    ax.set_xlabel("ROC AUC")
    ax.bar_label(bars, labels=[f"{value:.3f}" for value in ordered["roc_auc"]], padding=4)
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    _save(fig, path)


def plot_roc(y_true: pd.Series, probability: np.ndarray, path: Path) -> None:
    _style()
    fpr, tpr, _ = roc_curve(y_true, probability)
    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    ax.plot(fpr, tpr, color=TEAL, linewidth=2.6, label="Champion")
    ax.plot([0, 1], [0, 1], color=SLATE, linestyle="--", linewidth=1, label="Random")
    ax.set_title("Out-of-time discrimination", loc="left")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.legend(frameon=False, loc="lower right")
    ax.set_aspect("equal", adjustable="box")
    _save(fig, path)


def plot_calibration(y_true: pd.Series, probability: np.ndarray, path: Path) -> None:
    _style()
    observed, predicted = calibration_curve(y_true, probability, n_bins=10, strategy="quantile")
    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    ax.plot(predicted, observed, marker="o", color=BLUE, linewidth=2.2, label="Champion")
    ax.plot([0, 1], [0, 1], color=SLATE, linestyle="--", linewidth=1, label="Perfect")
    ax.set_xlim(0, max(0.35, float(predicted.max()) + 0.03))
    ax.set_ylim(0, max(0.35, float(observed.max()) + 0.03))
    ax.set_title("Out-of-time calibration", loc="left")
    ax.set_xlabel("Mean predicted PD")
    ax.set_ylabel("Observed default rate")
    ax.legend(frameon=False)
    _save(fig, path)


def plot_deciles(deciles: pd.DataFrame, path: Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    bars = ax.bar(
        deciles["risk_decile"].astype(str),
        deciles["observed_default_rate"],
        color=[RED if value <= 3 else BLUE for value in deciles["risk_decile"]],
    )
    ax.plot(
        deciles["risk_decile"].astype(str),
        deciles["average_predicted_pd"],
        color=NAVY,
        marker="o",
        linewidth=2,
        label="Average predicted PD",
    )
    ax.set_title("Risk deciles separate default outcomes", loc="left")
    ax.set_xlabel("Risk decile (1 = highest risk)")
    ax.set_ylabel("Rate")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.legend(frameon=False)
    ax.bar_label(
        bars, labels=[f"{value:.1%}" for value in deciles["observed_default_rate"]], padding=2
    )
    _save(fig, path)


def plot_shap(global_importance: pd.DataFrame, path: Path, top_n: int = 12) -> None:
    _style()
    top = global_importance.head(top_n).sort_values("mean_abs_shap_log_odds")
    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    bars = ax.barh(top["feature"], top["mean_abs_shap_log_odds"], color=TEAL)
    ax.set_title("Global Linear SHAP importance", loc="left")
    ax.set_xlabel("Mean |SHAP| contribution in log-odds")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.bar_label(
        bars, labels=[f"{value:.3f}" for value in top["mean_abs_shap_log_odds"]], padding=3
    )
    _save(fig, path)


def plot_fairness(details: pd.DataFrame, path: Path) -> None:
    _style()
    pivot = details.pivot(index="group", columns="protected_attribute", values="approval_rate")
    fig, axes = plt.subplots(1, len(pivot.columns), figsize=(10.5, 4.4), squeeze=False)
    for index, attribute in enumerate(pivot.columns):
        values = pivot[attribute].dropna().sort_values()
        ax = axes[0, index]
        ax.barh(values.index, values.values, color=BLUE)
        ax.set_title(f"Approval rate by {attribute}", loc="left")
        ax.set_xlim(0, max(0.75, float(values.max()) + 0.08))
        ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
        ax.grid(axis="x")
        ax.grid(axis="y", visible=False)
    fig.suptitle(
        "Disaggregated fairness diagnostics — interpretation requires governance",
        x=0.01,
        ha="left",
        fontweight="bold",
    )
    fig.tight_layout()
    _save(fig, path)


def plot_monitoring(monitoring: pd.DataFrame, path: Path) -> None:
    _style()
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 6.7), sharex=True)
    axes[0].plot(monitoring["monitoring_month"], monitoring["roc_auc"], color=TEAL, marker="o")
    axes[0].set_ylabel("ROC AUC")
    axes[0].set_title("Monthly out-of-time performance and score stability", loc="left")
    axes[1].plot(monitoring["monitoring_month"], monitoring["score_psi"], color=AMBER, marker="o")
    axes[1].axhline(0.10, color=AMBER, linestyle="--", linewidth=1, label="Warning 0.10")
    axes[1].axhline(0.25, color=RED, linestyle="--", linewidth=1, label="Critical 0.25")
    axes[1].set_ylabel("Score PSI")
    axes[1].legend(frameon=False, ncol=2)
    axes[1].tick_params(axis="x", rotation=45)
    fig.tight_layout()
    _save(fig, path)


def plot_dashboard(
    executive: dict[str, Any],
    risk_summary: pd.DataFrame,
    monitoring: pd.DataFrame,
    shap: pd.DataFrame,
    path: Path,
) -> None:
    _style()
    fig = plt.figure(figsize=(16, 9))
    grid = fig.add_gridspec(3, 4, height_ratios=[0.75, 1.5, 1.5], hspace=0.52, wspace=0.36)
    fig.suptitle(
        "Aurelia Bank | Credit Risk Decision-Support Control Tower",
        x=0.04,
        y=0.98,
        ha="left",
        fontsize=20,
        fontweight="bold",
        color=NAVY,
    )
    cards = [
        ("OOT AUC", f"{executive['oot_roc_auc']:.3f}"),
        ("OOT Gini", f"{executive['oot_gini']:.3f}"),
        ("Approval recommendation", f"{executive['approval_rate']:.1%}"),
        ("Illustrative expected loss", f"₺{executive['expected_loss_total'] / 1_000_000:.1f}m"),
    ]
    for idx, (label, value) in enumerate(cards):
        ax = fig.add_subplot(grid[0, idx])
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, color=PALE, transform=ax.transAxes))
        ax.text(0.06, 0.66, label, transform=ax.transAxes, color=SLATE, fontsize=11)
        ax.text(
            0.06, 0.20, value, transform=ax.transAxes, color=NAVY, fontsize=24, fontweight="bold"
        )

    ax_risk = fig.add_subplot(grid[1:, :2])
    colors = [TEAL, "#14B8A6", BLUE, AMBER, "#F59E0B", RED]
    ax_risk.bar(risk_summary["risk_band"], risk_summary["applications"], color=colors)
    ax_risk.set_title("OOT applications by governed risk band", loc="left")
    ax_risk.set_ylabel("Applications")
    ax_risk.grid(axis="y")
    ax_risk.grid(axis="x", visible=False)

    ax_monitor = fig.add_subplot(grid[1, 2:])
    ax_monitor.plot(monitoring["monitoring_month"], monitoring["roc_auc"], color=TEAL, marker="o")
    ax_monitor.set_title("Monthly OOT ROC AUC", loc="left")
    ax_monitor.tick_params(axis="x", rotation=45)
    ax_monitor.grid(axis="y")

    ax_shap = fig.add_subplot(grid[2, 2:])
    top = shap.head(8).sort_values("mean_abs_shap_log_odds")
    ax_shap.barh(top["feature"], top["mean_abs_shap_log_odds"], color=BLUE)
    ax_shap.set_title("Top model drivers | mean absolute Linear SHAP", loc="left")
    ax_shap.grid(axis="x")
    ax_shap.grid(axis="y", visible=False)
    fig.text(
        0.04,
        0.015,
        "Synthetic portfolio • Recommendations are decision support only • Human review and jurisdiction-specific legal validation required",
        color=SLATE,
        fontsize=10,
    )
    _save(fig, path)
