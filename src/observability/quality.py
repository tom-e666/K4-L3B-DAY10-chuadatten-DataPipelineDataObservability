from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd
import great_expectations as gx

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run data quality checks using Great Expectations 1.x ephemeral context."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
    data_asset = data_source.add_dataframe_asset(name=f"papers_asset_{report_name}")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(gx.ExpectationSuite(name=f"papers_suite_{report_name}"))
    suite.add_expectation(gx.expectations.ExpectTableRowCountToBeBetween(min_value=20, max_value=30))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToBeBetween(column="title", min_value=8))

    validation_result = batch.validate(suite)
    result_dict = validation_result.to_json_dict()

    success = result_dict.get("success", False)
    summary = {
        "report_name": report_name,
        "success": success,
        "evaluated_expectations": len(result_dict.get("results", [])),
        "successful_expectations": sum(1 for r in result_dict.get("results", []) if r.get("success")),
        "results": [
            {
                "expectation_type": r.get("expectation_config", {}).get("type"),
                "kwargs": r.get("expectation_config", {}).get("kwargs"),
                "success": r.get("success"),
            }
            for r in result_dict.get("results", [])
        ],
    }

    report_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(report_path, summary)
    return summary


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path) -> dict[str, Any]:
    """Compute data freshness report and SLA compliance."""
    if df.empty:
        summary = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "is_fresh": False,
        }
        write_json(report_path, summary)
        return summary

    latest_pub = str(df["published"].max())
    oldest_pub = str(df["published"].min())
    total_rows = len(df)
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows if total_rows > 0 else 0.0
    is_fresh = stale_ratio <= 0.25

    summary = {
        "latest_published": latest_pub,
        "oldest_published": oldest_pub,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": round(stale_ratio, 4),
        "is_fresh": is_fresh,
    }
    write_json(report_path, summary)
    return summary
