from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd

from core.config import load_settings
from core.utils import write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    print("=== Running Phase 1 Baseline Pipeline ===")
    settings = load_settings()
    run_date = datetime.now(timezone.utc)

    # 1. Fetch source records
    records = fetch_source_records(settings)
    print(f"1. Fetched {len(records)} raw records.")

    # 2. Build clean dataframe
    clean_df = build_clean_dataframe(records, run_date)
    write_csv(clean_df, settings.paths.clean_csv)
    clean_df.to_json(settings.paths.clean_json, orient="records", indent=2)
    print(f"2. Built clean dataframe with {len(clean_df)} rows.")

    # 3. Build Chroma Index
    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
    print(f"3. Indexed documents into Chroma collection '{index.collection_name}'.")

    # 4. Build Test Set
    test_set = build_test_set(clean_df, settings.paths.eval_testset)
    print(f"4. Created test set with {len(test_set)} questions.")

    # 5. Evaluate Baseline
    eval_bundle = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    print("5. Evaluated Baseline Pipeline:")
    print("   Metrics:", eval_bundle.summary)

    # 6. Quality Checks & Freshness
    quality = run_data_quality_checks(clean_df, settings, "baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    print(f"6. Quality checks success={quality['success']}, Freshness is_fresh={freshness['is_fresh']}.")

    # 7. Generate Phase 1 Report
    source_summary = {
        "source_api": settings.source_api,
        "total_records": len(records),
        "freshness_threshold_days": settings.freshness_threshold_days,
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        eval_bundle.summary,
        quality,
        freshness,
    )
    print(f"7. Phase 1 Report generated at '{settings.paths.baseline_report}'.")


if __name__ == "__main__":
    main()
