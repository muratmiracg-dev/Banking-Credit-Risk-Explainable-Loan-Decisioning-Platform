"""End-to-end reproducible analytics pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from credit_risk.artifacts import (
    plot_calibration,
    plot_dashboard,
    plot_deciles,
    plot_fairness,
    plot_model_comparison,
    plot_monitoring,
    plot_roc,
    plot_shap,
    write_json,
)
from credit_risk.config import load_config
from credit_risk.data import (
    PROTECTED_ATTRIBUTES,
    TARGET,
    assign_split,
    frame_sha256,
    generate_portfolio,
    write_portfolio,
)
from credit_risk.explainability import explain_logistic
from credit_risk.fairness import fairness_audit
from credit_risk.metrics import build_decile_table, evaluate_binary
from credit_risk.modeling import score_model, train_and_compare
from credit_risk.monitoring import monitoring_report
from credit_risk.policy import apply_policy
from credit_risk.validation import validate_portfolio


def _scenario_table(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for threshold in np.arange(0.06, 0.161, 0.01):
        approved = scored["predicted_pd"] < threshold
        rows.append(
            {
                "approve_max_pd": round(float(threshold), 2),
                "approval_rate": float(approved.mean()),
                "approved_observed_default_rate": float(
                    scored.loc[approved, TARGET].mean() if approved.any() else 0
                ),
                "approved_average_pd": float(
                    scored.loc[approved, "predicted_pd"].mean() if approved.any() else 0
                ),
                "approved_exposure": float(scored.loc[approved, "requested_amount"].sum()),
                "approved_expected_loss": float(scored.loc[approved, "expected_loss"].sum()),
            }
        )
    return pd.DataFrame(rows)


def run_pipeline(
    root: str | Path = ".", config_path: str | Path = "config/project.yaml"
) -> dict[str, Any]:
    """Generate data, models, evidence, plots and machine-readable artifacts."""
    root_path = Path(root).resolve()
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = root_path / config_file
    config = load_config(config_file)
    frame = generate_portfolio(config)
    quality = validate_portfolio(frame, config)
    split = assign_split(frame, config)
    frame["sample_split"] = split
    write_portfolio(frame.drop(columns="sample_split"), root_path)

    bundle = train_and_compare(frame, split, config)
    probability = score_model(bundle.champion, frame)
    scored = apply_policy(frame, probability, config["policy"])
    development = split.eq("development")
    validation = split.eq("validation")
    oot = split.eq("out_of_time")

    sample_metrics = {
        name: evaluate_binary(
            scored.loc[mask, TARGET],
            scored.loc[mask, "predicted_pd"].to_numpy(),
            adverse_threshold=config["policy"]["refer_max_pd"],
        )
        for name, mask in {
            "development": development,
            "validation": validation,
            "out_of_time": oot,
        }.items()
    }
    deciles = build_decile_table(
        scored.loc[oot, "application_id"],
        scored.loc[oot, TARGET],
        scored.loc[oot, "predicted_pd"].to_numpy(),
    )
    explanations = explain_logistic(
        bundle.champion,
        scored.loc[development],
        scored.loc[oot],
        scored.loc[oot, "predicted_pd"].to_numpy(),
    )
    fairness_details, fairness_summary = fairness_audit(scored.loc[oot], PROTECTED_ATTRIBUTES)
    monitoring = monitoring_report(scored, development, validation, config)
    scenario = _scenario_table(scored.loc[oot])
    risk_summary = (
        scored.loc[oot]
        .groupby("risk_band", observed=True)
        .agg(
            applications=("application_id", "count"),
            exposure=("requested_amount", "sum"),
            average_pd=("predicted_pd", "mean"),
            observed_default_rate=(TARGET, "mean"),
            expected_loss=("expected_loss", "sum"),
        )
        .reindex(list("ABCDEF"), fill_value=0)
        .reset_index()
    )
    recommendation_summary = (
        scored.loc[oot]
        .groupby("recommendation", observed=True)
        .agg(
            applications=("application_id", "count"),
            exposure=("requested_amount", "sum"),
            average_pd=("predicted_pd", "mean"),
            observed_default_rate=(TARGET, "mean"),
            expected_loss=("expected_loss", "sum"),
        )
        .reset_index()
    )
    approval = scored.loc[oot, "recommendation"].eq("APPROVE_RECOMMENDATION")
    executive = {
        "portfolio_name": config["project"]["institution"],
        "synthetic_applications": int(len(scored)),
        "development_applications": int(development.sum()),
        "validation_applications": int(validation.sum()),
        "out_of_time_applications": int(oot.sum()),
        "overall_default_rate": float(scored[TARGET].mean()),
        "oot_default_rate": sample_metrics["out_of_time"]["default_rate"],
        "oot_roc_auc": sample_metrics["out_of_time"]["roc_auc"],
        "oot_gini": sample_metrics["out_of_time"]["gini"],
        "oot_pr_auc": sample_metrics["out_of_time"]["pr_auc"],
        "oot_ks": sample_metrics["out_of_time"]["ks"],
        "oot_brier": sample_metrics["out_of_time"]["brier"],
        "oot_calibration_slope": sample_metrics["out_of_time"]["calibration_slope"],
        "approval_rate": float(approval.mean()),
        "approved_observed_default_rate": float(scored.loc[oot & approval, TARGET].mean()),
        "human_review_rate": float(scored.loc[oot, "human_review_required"].mean()),
        "expected_loss_total": float(scored.loc[oot, "expected_loss"].sum()),
        "maximum_monthly_score_psi": float(monitoring["score_psi"].max()),
        "fairness_max_demographic_parity_difference": float(
            fairness_summary["demographic_parity_difference"].max()
        ),
        "linear_shap_max_additivity_error": explanations.max_additivity_error,
        "data_sha256": frame_sha256(frame.drop(columns="sample_split")),
        "decision_scope": "Decision support only; no automated production lending decision",
    }

    metrics_dir = root_path / "artifacts/metrics"
    monitoring_dir = root_path / "artifacts/monitoring"
    explanation_dir = root_path / "artifacts/explanations"
    model_dir = root_path / "artifacts/model"
    plot_dir = root_path / "artifacts/plots"
    for directory in [metrics_dir, monitoring_dir, explanation_dir, model_dir, plot_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    quality.to_csv(metrics_dir / "data_quality_checks.csv", index=False)
    bundle.comparison.to_csv(metrics_dir / "model_comparison.csv", index=False)
    deciles.to_csv(metrics_dir / "risk_deciles.csv", index=False)
    risk_summary.to_csv(metrics_dir / "risk_band_summary.csv", index=False)
    recommendation_summary.to_csv(metrics_dir / "recommendation_summary.csv", index=False)
    scenario.to_csv(metrics_dir / "policy_scenarios.csv", index=False)
    fairness_details.to_csv(metrics_dir / "fairness_by_group.csv", index=False)
    fairness_summary.to_csv(metrics_dir / "fairness_summary.csv", index=False)
    monitoring.to_csv(monitoring_dir / "monthly_monitoring.csv", index=False)
    explanations.global_importance.to_csv(
        explanation_dir / "global_linear_shap_importance.csv", index=False
    )
    explanations.local_reasons.to_csv(
        explanation_dir / "oot_local_reason_codes.csv.gz",
        index=False,
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    scored.to_csv(
        root_path / "artifacts/data/scored_loan_applications.csv.gz",
        index=False,
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    scored.loc[oot].head(250).to_csv(
        root_path / "data/samples/scored_applications_sample.csv", index=False
    )
    write_json(sample_metrics, metrics_dir / "sample_metrics.json")
    write_json(bundle.validation_metrics, metrics_dir / "validation_metrics.json")
    write_json(executive, metrics_dir / "executive_summary.json")
    write_json(
        {
            "model_name": bundle.champion_name,
            "version": config["project"]["version"],
            "model_features": list(bundle.champion.feature_names_in_),
            "protected_attributes_excluded": config["model"]["protected_attributes_excluded"],
            "target": config["data"]["target"],
            "development_window": [
                config["data"]["start_date"],
                config["data"]["development_end"],
            ],
            "validation_window": [
                str(pd.Timestamp(config["data"]["development_end"]) + pd.Timedelta(days=1)).split(
                    " "
                )[0],
                config["data"]["validation_end"],
            ],
            "out_of_time_window": [
                str(pd.Timestamp(config["data"]["validation_end"]) + pd.Timedelta(days=1)).split(
                    " "
                )[0],
                config["data"]["end_date"],
            ],
            "linear_shap_expected_log_odds": explanations.expected_log_odds,
            "linear_shap_additivity_max_error": explanations.max_additivity_error,
            "decision_scope": executive["decision_scope"],
        },
        model_dir / "model_metadata.json",
    )
    joblib.dump(bundle.champion, model_dir / "champion_logistic_pipeline.joblib", compress=3)
    preprocess = bundle.champion.named_steps["preprocess"]
    development_transformed = np.asarray(
        preprocess.transform(scored.loc[development, list(bundle.champion.feature_names_in_)]),
        dtype=float,
    )
    joblib.dump(
        {
            "feature_names": preprocess.get_feature_names_out(),
            "background_mean": development_transformed.mean(axis=0),
            "expected_log_odds": explanations.expected_log_odds,
        },
        model_dir / "linear_shap_state.joblib",
        compress=3,
    )

    plot_model_comparison(bundle.comparison, plot_dir / "model_comparison.png")
    plot_roc(
        scored.loc[oot, TARGET],
        scored.loc[oot, "predicted_pd"].to_numpy(),
        plot_dir / "oot_roc_curve.png",
    )
    plot_calibration(
        scored.loc[oot, TARGET],
        scored.loc[oot, "predicted_pd"].to_numpy(),
        plot_dir / "oot_calibration.png",
    )
    plot_deciles(deciles, plot_dir / "risk_deciles.png")
    plot_shap(explanations.global_importance, plot_dir / "global_linear_shap.png")
    plot_fairness(fairness_details, plot_dir / "fairness_diagnostics.png")
    plot_monitoring(monitoring, plot_dir / "model_monitoring.png")
    plot_dashboard(
        executive,
        risk_summary,
        monitoring,
        explanations.global_importance,
        plot_dir / "executive_dashboard.png",
    )

    manifest = {
        "pipeline_status": "PASS",
        "generated_artifacts": sorted(
            str(path.relative_to(root_path))
            for path in root_path.glob("artifacts/**/*")
            if path.is_file()
        ),
        "critical_controls": quality.to_dict(orient="records"),
        "executive_summary": executive,
    }
    write_json(manifest, root_path / "artifacts/manifest.json")
    return manifest


def manifest_as_json(manifest: dict[str, Any]) -> str:
    """Serialize a compact CLI result."""
    return json.dumps(
        {
            "pipeline_status": manifest["pipeline_status"],
            "generated_artifact_count": len(manifest["generated_artifacts"]),
            "executive_summary": manifest["executive_summary"],
        },
        indent=2,
    )
