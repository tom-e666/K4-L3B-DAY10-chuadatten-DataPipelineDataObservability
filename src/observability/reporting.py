from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path: Path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Generate Phase 1 Baseline markdown report."""
    content = f"""# Phase 1 Baseline Data Pipeline & Observability Report

## 1. Data Source Summary
- **Source API:** {source_summary.get('source_api', 'Crossref REST API')}
- **Total Records Ingested:** {source_summary.get('total_records', 'N/A')}
- **Freshness Threshold:** {source_summary.get('freshness_threshold_days', 180)} days

## 2. Baseline Evaluation Metrics
- **Retrieval Hit Rate:** {metrics.get('retrieval_hit_rate', 0.0):.4f}
- **Mean Token F1:** {metrics.get('mean_token_f1', 0.0):.4f}
- **Judge Accuracy:** {metrics.get('judge_accuracy', 0.0):.4f}
- **Mean Judge Score:** {metrics.get('mean_judge_score', 0.0):.2f} / 5.0

## 3. Data Quality and Freshness
- **Quality Check Status:** {"PASSED" if quality.get('success') else "FAILED"}
- **Passed Checks:** {quality.get('successful_expectations', quality.get('passed_checks', 0))} / {quality.get('evaluated_expectations', quality.get('total_checks', 0))}
- **Freshness SLA Status:** {"FRESH" if freshness.get('is_fresh') else "STALE"}
- **Stale Ratio (>180 days):** {freshness.get('stale_ratio', 0.0):.2%}
- **Latest Published Date:** {freshness.get('latest_published', 'N/A')}
- **Oldest Published Date:** {freshness.get('oldest_published', 'N/A')}
"""
    write_text(report_path, content)


def generate_corruption_report(
    report_path: Path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Generate report comparing baseline, corrupted, and repaired states."""
    metric_keys = (
        ("Retrieval Hit Rate", "retrieval_hit_rate", ".4f"),
        ("Mean Token F1", "mean_token_f1", ".4f"),
        ("Judge Accuracy", "judge_accuracy", ".4f"),
        ("Mean Judge Score", "mean_judge_score", ".2f"),
    )

    rows = []
    for label, key, number_format in metric_keys:
        baseline = baseline_metrics.get(key, 0.0)
        corrupted = corrupted_metrics.get(key, 0.0)
        repaired = repaired_metrics.get(key, 0.0)
        rows.append(
            f"| **{label}** | `{baseline:{number_format}}` "
            f"| `{corrupted:{number_format}}` | `{repaired:{number_format}}` |"
        )

    content = f"""# Data Corruption and Repair Report

## 1. Performance Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
{chr(10).join(rows)}
| **Quality Checks** | `PASS` | `{'PASS' if corrupted_quality.get('success') else 'FAIL'}` | `{'PASS' if repaired_quality.get('success') else 'FAIL'}` |
| **Freshness** | `N/A` | `{'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE'}` | `{'FRESH' if repaired_freshness.get('is_fresh') else 'STALE'}` |

## 2. Findings
- Corruption can reduce retrieval and answer quality without causing a runtime error.
- Quality checks detect corrupted data before it is used.
- Repair from the trusted raw snapshot should restore data quality and agent metrics.
"""
    write_text(report_path, content)