from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import ensure_parent, write_json


def corrupt_clean_dataframe(
    clean_df: pd.DataFrame,
    output_log_path: str | Path,
) -> pd.DataFrame:
    """Apply six synthetic corruption scenarios and save an audit log."""
    df = clean_df.copy()

    if df.empty:
        log_data: dict[str, Any] = {
            "total_before": 0,
            "total_after": 0,
            "scenarios": [],
        }
        ensure_parent(Path(output_log_path))
        write_json(Path(output_log_path), log_data)
        return df

    # 1. Drop the 20% newest records.
    df = df.sort_values(
        by="published",
        ascending=False,
        kind="stable",
    ).reset_index(drop=True)

    drop_count = max(1, int(len(df) * 0.20))
    dropped_records = df.iloc[:drop_count][
        ["paper_id", "title", "published"]
    ].to_dict(orient="records")
    df = df.iloc[drop_count:].reset_index(drop=True)

    # 2. Blank summaries in up to two rows.
    blank_records = []
    for idx in range(min(2, len(df))):
        blank_records.append({
            "paper_id": df.loc[idx, "paper_id"],
            "title": df.loc[idx, "title"],
        })
        df.loc[idx, "summary"] = ""

    # 3. Add noise to summaries in up to two rows.
    noise_records = []
    for idx in range(2, min(4, len(df))):
        noise_records.append({
            "paper_id": df.loc[idx, "paper_id"],
            "title": df.loc[idx, "title"],
        })
        df.loc[idx, "summary"] = (
            "### NOISE_CORRUPTION_@#$%^&* ### "
            + str(df.loc[idx, "summary"])
        )

    # 4. Truncate titles in up to two rows.
    truncate_records = []
    for idx in range(4, min(6, len(df))):
        original_title = str(df.loc[idx, "title"])
        corrupted_title = original_title[:7] or "Corrupt"

        truncate_records.append({
            "paper_id": df.loc[idx, "paper_id"],
            "original_title": original_title,
            "corrupted_title": corrupted_title,
        })
        df.loc[idx, "title"] = corrupted_title

    # 5. Set publication dates to 2014 to trigger stale-data checks.
    stale_records = []
    for idx in range(6, min(8, len(df))):
        stale_records.append({
            "paper_id": df.loc[idx, "paper_id"],
            "original_published": str(df.loc[idx, "published"]),
            "corrupted_published": "2014-01-01",
        })
        df.loc[idx, "published"] = "2014-01-01"

        if "age_days" in df.columns:
            df.loc[idx, "age_days"] = 4600

    # 6. Duplicate up to two rows.
    duplicate_records = []
    duplicate_count = min(2, len(df))
    if duplicate_count:
        duplicate_rows = df.iloc[:duplicate_count].copy()
        duplicate_records = duplicate_rows[
            ["paper_id", "title"]
        ].to_dict(orient="records")
        df = pd.concat([df, duplicate_rows], ignore_index=True)

    # Rebuild derived text fields.
    df["summary_chars"] = df["summary"].astype(str).str.len()
    df["text_for_embedding"] = (
        "Title: " + df["title"].astype(str) + "\n"
        "Authors: " + df["authors_joined"].astype(str) + "\n"
        "Published: " + df["published"].astype(str) + "\n"
        "Categories: " + df["categories_joined"].astype(str) + "\n"
        "Summary: " + df["summary"].astype(str)
    )

    log_data = {
        "total_before": len(clean_df),
        "total_after": len(df),
        "scenarios": [
            {
                "type": "drop_latest",
                "description": "Drop the 20% newest records",
                "affected_count": len(dropped_records),
                "affected_records": dropped_records,
            },
            {
                "type": "blank_summary",
                "description": "Blank out summaries",
                "affected_count": len(blank_records),
                "affected_records": blank_records,
            },
            {
                "type": "inject_noise",
                "description": "Inject noise into summaries",
                "affected_count": len(noise_records),
                "affected_records": noise_records,
            },
            {
                "type": "truncate_title",
                "description": "Truncate titles to fewer than 8 characters",
                "affected_count": len(truncate_records),
                "affected_records": truncate_records,
            },
            {
                "type": "stale_date",
                "description": "Set publication dates to 2014-01-01",
                "affected_count": len(stale_records),
                "affected_records": stale_records,
            },
            {
                "type": "duplicate_rows",
                "description": "Duplicate rows to create repeated paper IDs",
                "affected_count": len(duplicate_records),
                "affected_records": duplicate_records,
            },
        ],
    }

    log_path = Path(output_log_path)
    ensure_parent(log_path)
    write_json(log_path, log_data)

    return df