from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import great_expectations as gx
from great_expectations.expectations import (
    ExpectTableRowCountToBeBetween,
    ExpectColumnValuesToNotBeNull,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValueLengthsToBeBetween,
)

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(
    df: pd.DataFrame,
    settings: Settings,
    report_name: str,
) -> dict[str, Any]:
    """Run data quality checks using Great Expectations."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(
        name=f"papers_source_{report_name}"
    )
    data_asset = data_source.add_dataframe_asset(
        name=f"papers_asset_{report_name}"
    )
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(
        gx.ExpectationSuite(name=f"papers_suite_{report_name}")
    )
    suite.add_expectation(
        ExpectTableRowCountToBeBetween(min_value=5, max_value=5000)
    )
    suite.add_expectation(
        ExpectColumnValuesToNotBeNull(column="paper_id")
    )
    suite.add_expectation(
        ExpectColumnValuesToBeUnique(column="paper_id")
    )
    suite.add_expectation(
        ExpectColumnValuesToNotBeNull(column="title")
    )
    suite.add_expectation(
        ExpectColumnValueLengthsToBeBetween(column="title", min_value=8)
    )
    suite.add_expectation(
        ExpectColumnValuesToNotBeNull(column="text_for_embedding")
    )
    suite.add_expectation(
        ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30)
    )

    result_dict = batch.validate(suite).to_json_dict()
    results = result_dict.get("results", [])

    summary = {
        "report_name": report_name,
        "success": result_dict.get("success", False),
        "evaluated_expectations": len(results),
        "successful_expectations": sum(
            1 for result in results if result.get("success")
        ),
        "results": [
            {
                "expectation_type": result.get("expectation_config", {}).get("type"),
                "kwargs": result.get("expectation_config", {}).get("kwargs"),
                "success": result.get("success"),
            }
            for result in results
        ],
    }

    if report_name == "baseline":
        report_path = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        report_path = settings.paths.corrupted_quality_report
    else:
        report_path = (
            settings.paths.quality_dir
            / f"{report_name}_quality_report.json"
        )

    write_json(report_path, summary)
    return summary


def build_freshness_report(
    df: pd.DataFrame,
    settings: Settings,
    report_path: Path,
) -> dict[str, Any]:
    """Compute freshness statistics and SLA compliance."""
    if df.empty or "age_days" not in df.columns:
        summary = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": len(df),
            "total_rows": len(df),
            "stale_ratio": 1.0 if len(df) else 0.0,
            "is_fresh": False,
        }
    else:
        total_rows = len(df)
        stale_rows = int(
            (df["age_days"] > settings.freshness_threshold_days).sum()
        )
        stale_ratio = stale_rows / total_rows if total_rows else 0.0

        summary = {
            "latest_published": str(df["published"].max()),
            "oldest_published": str(df["published"].min()),
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "stale_ratio": round(stale_ratio, 4),
            "is_fresh": stale_ratio <= 0.25,
        }

    write_json(report_path, summary)
    return summary