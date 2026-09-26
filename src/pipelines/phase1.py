from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import Settings, load_settings
from core.utils import ensure_parent
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def run_phase1_pipeline(settings: Settings | None = None) -> dict[str, Any]:
    if settings is None:
        settings = load_settings()

    # 1. Thu thập dữ liệu
    records = fetch_source_records(settings)

    # 2. Làm sạch và lưu dữ liệu
    clean_df = build_clean_dataframe(
        records,
        run_date=datetime.now(timezone.utc),
    )

    ensure_parent(settings.paths.clean_csv)
    clean_df.to_csv(settings.paths.clean_csv, index=False)

    ensure_parent(settings.paths.clean_json)
    clean_df.to_json(
        settings.paths.clean_json,
        orient="records",
        indent=2,
        force_ascii=False,
    )

    # 3. Tạo vector index
    index = LocalEmbeddingIndex.build(
        clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )

    # 4. Tạo evaluation test set
    test_set = build_test_set(clean_df, settings.paths.eval_testset)

    # 5. Đánh giá baseline
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # 6. Kiểm tra chất lượng và freshness
    quality = run_data_quality_checks(
        clean_df,
        settings=settings,
        report_name="baseline",
    )
    freshness = build_freshness_report(
        clean_df,
        settings=settings,
        report_path=settings.paths.freshness_report,
    )

    # 7. Tạo báo cáo
    source_summary = {
        "source_api": settings.source_api,
        "total_records": len(records),
        "freshness_threshold_days": settings.freshness_threshold_days,
    }

    ensure_parent(settings.paths.baseline_report)
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )

    print(f"[Phase 1] Ingested: {len(records)} records")
    print(f"[Phase 1] Cleaned: {len(clean_df)} records")
    print(f"[Phase 1] Test questions: {len(test_set)}")
    print(
        f"[Phase 1] Baseline Hit Rate: "
        f"{bundle.summary.get('retrieval_hit_rate', 0.0):.4f}"
    )
    print(
        f"[Phase 1] Baseline Token F1: "
        f"{bundle.summary.get('mean_token_f1', 0.0):.4f}"
    )
    print(f"[Phase 1] Quality Gate: {quality.get('success')}")
    print(f"[Phase 1] Freshness: {freshness.get('is_fresh')}")
    print(f"[Phase 1] Report: {settings.paths.baseline_report}")

    return {
        "metrics": bundle.summary,
        "quality": quality,
        "freshness": freshness,
        "cleaned_records": len(clean_df),
        "test_questions": len(test_set),
        "report_path": str(settings.paths.baseline_report),
    }


def main() -> None:
    run_phase1_pipeline(load_settings())


if __name__ == "__main__":
    main()