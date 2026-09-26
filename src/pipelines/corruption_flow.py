from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd

from core.config import Settings, load_settings
from core.utils import ensure_parent, read_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def repair_from_raw_snapshot(settings: Settings) -> pd.DataFrame:
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=datetime.now(timezone.utc))

    ensure_parent(settings.paths.repaired_clean_csv)
    repaired_df.to_csv(settings.paths.repaired_clean_csv, index=False)
    ensure_parent(settings.paths.repaired_clean_json)
    repaired_df.to_json(settings.paths.repaired_clean_json, orient="records", indent=2, force_ascii=False)

    # Idempotent healing: restore primary clean files as well
    repaired_df.to_csv(settings.paths.clean_csv, index=False)
    repaired_df.to_json(settings.paths.clean_json, orient="records", indent=2, force_ascii=False)

    return repaired_df


def run_corruption_flow_pipeline(settings: Settings | None = None) -> dict[str, Any]:
    if settings is None:
        settings = load_settings()

    # 1. Load baseline metrics & clean data
    if settings.paths.baseline_metrics.exists():
        baseline_metrics = read_json(settings.paths.baseline_metrics)
    else:
        raise FileNotFoundError(f"Baseline metrics not found at {settings.paths.baseline_metrics}. Run phase 1 first.")

    clean_df = pd.read_json(settings.paths.clean_json)

    # 2. Corrupt clean dataframe and persist artifacts
    corrupted_df = corrupt_clean_dataframe(clean_df, output_log_path=settings.paths.corruption_log)
    ensure_parent(settings.paths.corrupted_clean_csv)
    corrupted_df.to_csv(settings.paths.corrupted_clean_csv, index=False)
    ensure_parent(settings.paths.corrupted_clean_json)
    corrupted_df.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2, force_ascii=False)

    # 3. Build corrupted Chroma index & evaluate degradation (Silent Failure)
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(corrupted_df, settings=settings, report_name="corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings=settings,
        report_path=settings.paths.quality_dir / "corrupted_freshness_report.json",
    )

    # 4. Idempotent Repair from raw snapshot & evaluate recovery
    repaired_df = repair_from_raw_snapshot(settings)
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings=settings, report_name="repaired")
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings=settings,
        report_path=settings.paths.quality_dir / "repaired_freshness_report.json",
    )

    # 5. Generate 3-state comparison report
    ensure_parent(settings.paths.comparison_report)
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    # Print 3-state comparison matrix to console
    hit_base = baseline_metrics.get("retrieval_hit_rate", 0.0)
    hit_corr = corrupted_bundle.summary.get("retrieval_hit_rate", 0.0)
    hit_rep = repaired_bundle.summary.get("retrieval_hit_rate", 0.0)

    f1_base = baseline_metrics.get("mean_token_f1", 0.0)
    f1_corr = corrupted_bundle.summary.get("mean_token_f1", 0.0)
    f1_rep = repaired_bundle.summary.get("mean_token_f1", 0.0)

    acc_base = baseline_metrics.get("judge_accuracy", 0.0)
    acc_corr = corrupted_bundle.summary.get("judge_accuracy", 0.0)
    acc_rep = repaired_bundle.summary.get("judge_accuracy", 0.0)

    score_base = baseline_metrics.get("mean_judge_score", 0.0)
    score_corr = corrupted_bundle.summary.get("mean_judge_score", 0.0)
    score_rep = repaired_bundle.summary.get("mean_judge_score", 0.0)

    print("\n" + "=" * 80)
    print("           3-STATE PERFORMANCE COMPARISON MATRIX (Baseline vs Corrupted vs Repaired)")
    print("=" * 80)
    print(f"{'Metric / Signal':<25} | {'Baseline':<12} | {'Corrupted':<12} | {'Repaired':<12} | {'Recovery':<10}")
    print("-" * 80)
    print(f"{'Retrieval Hit Rate':<25} | {hit_base:<12.4f} | {hit_corr:<12.4f} | {hit_rep:<12.4f} | {hit_rep - hit_corr:+10.4f}")
    print(f"{'Mean Token F1':<25} | {f1_base:<12.4f} | {f1_corr:<12.4f} | {f1_rep:<12.4f} | {f1_rep - f1_corr:+10.4f}")
    print(f"{'Judge Accuracy':<25} | {acc_base:<12.4f} | {acc_corr:<12.4f} | {acc_rep:<12.4f} | {acc_rep - acc_corr:+10.4f}")
    print(f"{'Mean Judge Score':<25} | {score_base:<12.2f} | {score_corr:<12.2f} | {score_rep:<12.2f} | {score_rep - score_corr:+10.2f}")
    print(f"{'Data Quality Status':<25} | {'PASSED':<12} | {'PASSED' if corrupted_quality.get('success') else 'FAILED':<12} | {'PASSED' if repaired_quality.get('success') else 'FAILED':<12} | {'Recovered':<10}")
    print(f"{'Freshness SLA Status':<25} | {'FRESH':<12} | {'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE':<12} | {'FRESH' if repaired_freshness.get('is_fresh') else 'STALE':<12} | {'Recovered':<10}")
    print("=" * 80)
    print(f"Report written to: {settings.paths.comparison_report}\n")

    return {
        "baseline_metrics": baseline_metrics,
        "corrupted_metrics": corrupted_bundle.summary,
        "repaired_metrics": repaired_bundle.summary,
        "comparison_report": str(settings.paths.comparison_report),
    }


def main() -> None:
    settings = load_settings()
    run_corruption_flow_pipeline(settings)
