from __future__ import annotations

from pathlib import Path
import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path) -> pd.DataFrame:
    """Apply 6 synthetic data corruption scenarios and record log."""
    corrupted_df = df.copy()
    logs = []

    # Scenario 1: Drop 20% latest records
    drop_count = max(1, int(len(corrupted_df) * 0.20))
    dropped_ids = list(corrupted_df.iloc[:drop_count]["paper_id"])
    corrupted_df = corrupted_df.iloc[drop_count:].reset_index(drop=True)
    logs.append({"scenario": "drop_latest", "description": f"Dropped {drop_count} latest records", "affected_ids": dropped_ids})

    # Scenario 2: Blank summary in 2 rows
    if len(corrupted_df) >= 2:
        affected_ids = list(corrupted_df.iloc[:2]["paper_id"])
        corrupted_df.loc[corrupted_df.index[:2], "summary"] = ""
        corrupted_df.loc[corrupted_df.index[:2], "summary_chars"] = 0
        logs.append({"scenario": "blank_summary", "description": "Blanked summaries for 2 records", "affected_ids": affected_ids})

    # Scenario 3: Inject noise into 2 rows
    if len(corrupted_df) >= 4:
        affected_ids = list(corrupted_df.iloc[2:4]["paper_id"])
        corrupted_df.loc[corrupted_df.index[2:4], "summary"] += " [CORRUPTED_NOISE_GARBAGE_DATA_XYZ]"
        logs.append({"scenario": "inject_noise", "description": "Injected garbage noise into 2 summaries", "affected_ids": affected_ids})

    # Scenario 4: Truncate title to < 8 chars in 2 rows
    if len(corrupted_df) >= 6:
        affected_ids = list(corrupted_df.iloc[4:6]["paper_id"])
        corrupted_df.loc[corrupted_df.index[4:6], "title"] = "Short"
        logs.append({"scenario": "truncate_title", "description": "Truncated title to 'Short' (< 8 chars)", "affected_ids": affected_ids})

    # Scenario 5: Stale published date for 2 rows (set 10 years ago)
    if len(corrupted_df) >= 8:
        affected_ids = list(corrupted_df.iloc[6:8]["paper_id"])
        corrupted_df.loc[corrupted_df.index[6:8], "published"] = "2014-01-01"
        corrupted_df.loc[corrupted_df.index[6:8], "age_days"] = 4600
        logs.append({"scenario": "stale_date", "description": "Set published date to 2014 (stale age_days)", "affected_ids": affected_ids})

    # Scenario 6: Duplicate rows
    if len(corrupted_df) >= 2:
        dupes = corrupted_df.iloc[:2].copy()
        logs.append({"scenario": "duplicate_rows", "description": "Duplicated top 2 rows", "affected_ids": list(dupes["paper_id"])})
        corrupted_df = pd.concat([corrupted_df, dupes], ignore_index=True)

    # Rebuild text_for_embedding
    corrupted_df["text_for_embedding"] = (
        "Title: " + corrupted_df["title"] + "\n" +
        "Authors: " + corrupted_df["authors_joined"] + "\n" +
        "Published: " + corrupted_df["published"] + "\n" +
        "Categories: " + corrupted_df["categories_joined"] + "\n" +
        "Summary: " + corrupted_df["summary"]
    )

    write_json(output_log_path, logs)
    return corrupted_df
