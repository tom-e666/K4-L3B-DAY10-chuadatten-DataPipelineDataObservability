from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    print("=== Running Data Corruption & Idempotent Repair Flow ===")
    settings = load_settings()
    run_date = datetime.now(timezone.utc)

    # Load baseline clean data
    clean_df = pd.read_json(settings.paths.clean_json)
    baseline_metrics = read_json(settings.paths.baseline_metrics)

    # 1. Corrupt Data
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    corrupted_df.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2)
    print(f"1. Corrupted dataframe created with {len(corrupted_df)} rows.")

    # 2. Build Corrupted Index & Evaluate
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    corrupted_eval = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )
    print("2. Corrupted Pipeline Metrics:", corrupted_eval.summary)

    # 3. Quality & Freshness on Corrupted Data
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(corrupted_df, settings, settings.paths.quality_dir / "corrupted_freshness_report.json")
    print(f"3. Corrupted Quality success={corrupted_quality['success']}, Freshness is_fresh={corrupted_freshness['is_fresh']}.")

    # 4. Idempotent Repair from Raw Snapshot
    print("4. Initiating Idempotent Repair from Raw Snapshot...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date)
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    repaired_df.to_json(settings.paths.repaired_clean_json, orient="records", indent=2)

    # 5. Build Repaired Index & Evaluate
    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)
    repaired_eval = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    print("5. Repaired Pipeline Metrics:", repaired_eval.summary)

    # 6. Quality & Freshness on Repaired Data
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(repaired_df, settings, settings.paths.quality_dir / "repaired_freshness_report.json")

    # 7. Generate Comparison Report
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_eval.summary,
        repaired_eval.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    print(f"7. Comparison report generated at '{settings.paths.comparison_report}'.")


if __name__ == "__main__":
    main()
