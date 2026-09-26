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
    """Rebuild clean data from the trusted raw snapshot."""
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(
        raw_records,
        run_date=datetime.now(timezone.utc),
    )

    for path in (
        settings.paths.repaired_clean_csv,
        settings.paths.clean_csv,
    ):
        ensure_parent(path)
        repaired_df.to_csv(path, index=False)

    for path in (
        settings.paths.repaired_clean_json,
        settings.paths.clean_json,
    ):
        ensure_parent(path)
        repaired_df.to_json(
            path,
            orient="records",
            indent=2,
            force_ascii=False,
        )

    return repaired_df


def run_corruption_flow_pipeline(
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Run corruption, evaluate degradation, repair, and evaluate recovery."""
    if settings is None:
        settings = load_settings()

    if not settings.paths.baseline_metrics.exists():
        raise FileNotFoundError(
            f"Baseline metrics not found at "
            f"{settings.paths.baseline_metrics}. Run Phase 1 first."
        )

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    clean_df = pd.read_json(settings.paths.clean_json)

    # Corrupt the clean data and save artifacts.
    corrupted_df = corrupt_clean_dataframe(
        clean_df,
        output_log_path=settings.paths.corruption_log,
    )

    ensure_parent(settings.paths.corrupted_clean_csv)
    corrupted_df.to_csv(settings.paths.corrupted_clean_csv, index=False)

    ensure_parent(settings.paths.corrupted_clean_json)
    corrupted_df.to_json(
        settings.paths.corrupted_clean_json,
        orient="records",
        indent=2,
        force_ascii=False,
    )

    # Build and evaluate the corrupted index.
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

    corrupted_quality = run_data_quality_checks(
        corrupted_df,
        settings=settings,
        report_name="corrupted",
    )
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings=settings,
        report_path=(
            settings.paths.quality_dir
            / "corrupted_freshness_report.json"
        ),
    )

    # Repair from the raw snapshot, then evaluate the repaired index.
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

    repaired_quality = run_data_quality_checks(
        repaired_df,
        settings=settings,
        report_name="repaired",
    )
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings=settings,
        report_path=(
            settings.paths.quality_dir
            / "repaired_freshness_report.json"
        ),
    )

    # Generate the comparison report.
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

    print(f"Comparison report written to: {settings.paths.comparison_report}")

    return {
        "baseline_metrics": baseline_metrics,
        "corrupted_metrics": corrupted_bundle.summary,
        "repaired_metrics": repaired_bundle.summary,
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
        "corrupted_freshness": corrupted_freshness,
        "repaired_freshness": repaired_freshness,
        "comparison_report": str(settings.paths.comparison_report),
    }


def main() -> None:
    settings = load_settings()
    run_corruption_flow_pipeline(settings)


if __name__ == "__main__":
    main()