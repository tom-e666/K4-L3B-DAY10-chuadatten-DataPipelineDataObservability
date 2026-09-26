from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import pandas as pd

from core.utils import ensure_parent, write_json


def corrupt_clean_dataframe(clean_df: pd.DataFrame, output_log_path: str | Path) -> pd.DataFrame:
    df = clean_df.copy()
    if df.empty:
        return df

    # 1. Drop latest records (20% newest)
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    drop_count = max(1, int(round(len(df) * 0.2)))
    dropped_records = df.iloc[:drop_count][["paper_id", "title", "published"]].to_dict(orient="records")
    df = df.iloc[drop_count:].reset_index(drop=True)

    # 2. Blank summary (2 records)
    blank_indices = [0, 1]
    blank_records = []
    for idx in blank_indices:
        if idx < len(df):
            blank_records.append({
                "paper_id": df.loc[idx, "paper_id"],
                "title": df.loc[idx, "title"],
            })
            df.loc[idx, "summary"] = ""

    # 3. Inject noise into summary (2 records)
    noise_indices = [2, 3]
    noise_records = []
    for idx in noise_indices:
        if idx < len(df):
            noise_records.append({
                "paper_id": df.loc[idx, "paper_id"],
                "title": df.loc[idx, "title"],
            })
            df.loc[idx, "summary"] = "### NOISE_CORRUPTION_@#$%^&* ### " + str(df.loc[idx, "summary"])

    # 4. Truncate title to < 8 chars (2 records)
    truncate_indices = [4, 5]
    truncate_records = []
    for idx in truncate_indices:
        if idx < len(df):
            orig_title = str(df.loc[idx, "title"])
            truncated_title = orig_title[:7] if len(orig_title) >= 7 else "Corrupt"
            truncate_records.append({
                "paper_id": df.loc[idx, "paper_id"],
                "original_title": orig_title,
                "corrupted_title": truncated_title,
            })
            df.loc[idx, "title"] = truncated_title

    # 5. Stale date: Push publication date back by 365 days (8 records)
    stale_indices = list(range(6, min(14, len(df))))
    stale_records = []
    for idx in stale_indices:
        orig_pub = str(df.loc[idx, "published"])[:10]
        try:
            dt = datetime.strptime(orig_pub, "%Y-%m-%d")
            new_pub = (dt - timedelta(days=365)).strftime("%Y-%m-%d")
        except Exception:
            new_pub = "2024-01-01"

        stale_records.append({
            "paper_id": df.loc[idx, "paper_id"],
            "original_published": orig_pub,
            "corrupted_published": new_pub,
        })
        df.loc[idx, "published"] = new_pub
        if "age_days" in df.columns:
            df.loc[idx, "age_days"] = int(df.loc[idx, "age_days"]) + 365

    # 6. Duplicate rows (2 records)
    dup_indices = [14, 15] if len(df) > 15 else [0, 1]
    dup_rows = df.iloc[dup_indices].copy()
    duplicate_records = dup_rows[["paper_id", "title"]].to_dict(orient="records")
    df = pd.concat([df, dup_rows], ignore_index=True)

    # 7. Rebuild text_for_embedding & summary_chars
    df["summary_chars"] = df["summary"].astype(str).str.len()
    df["text_for_embedding"] = (
        "Title: " + df["title"].astype(str) + "\n"
        "Authors: " + df["authors_joined"].astype(str) + "\n"
        "Published: " + df["published"].astype(str) + "\n"
        "Categories: " + df["categories_joined"].astype(str) + "\n"
        "Summary: " + df["summary"].astype(str)
    )

    # 8. Write corruption log
    log_data: dict[str, Any] = {
        "total_before": len(clean_df),
        "total_after": len(df),
        "scenarios": [
            {
                "type": "drop_latest",
                "description": "Drop 20% newest records",
                "affected_count": len(dropped_records),
                "affected_records": dropped_records,
            },
            {
                "type": "blank_summary",
                "description": "Blank out summary text",
                "affected_count": len(blank_records),
                "affected_records": blank_records,
            },
            {
                "type": "inject_noise",
                "description": "Inject noise characters into summary",
                "affected_count": len(noise_records),
                "affected_records": noise_records,
            },
            {
                "type": "truncate_title",
                "description": "Truncate paper title to under 8 characters",
                "affected_count": len(truncate_records),
                "affected_records": truncate_records,
            },
            {
                "type": "stale_date",
                "description": "Push published date back by 365 days",
                "affected_count": len(stale_records),
                "affected_records": stale_records,
            },
            {
                "type": "duplicate_rows",
                "description": "Duplicate rows to create duplicate paper_ids",
                "affected_count": len(duplicate_records),
                "affected_records": duplicate_records,
            },
        ],
    }

    ensure_parent(Path(output_log_path))
    write_json(output_log_path, log_data)

    return df
