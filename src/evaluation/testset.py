from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict[str, Any]]:
    """Build evaluation test set of 10 questions across 4 categories."""
    if len(df) < 4:
        raise ValueError("DataFrame must have at least 4 rows to generate test set.")

    test_items = []

    # Sample rows deterministically
    sample_df = df.iloc[:10] if len(df) >= 10 else df

    for i, row in sample_df.iterrows():
        idx = len(test_items) + 1
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        summary = str(row["summary"])
        authors = str(row["authors_joined"])
        date = str(row["published"])
        categories = str(row["categories_joined"])

        q_type = ["summary", "authors", "date", "categories"][idx % 4]

        if q_type == "summary":
            q_text = f"What is the core focus or contribution of paper '{title}'?"
            gt_text = summary
        elif q_type == "authors":
            q_text = f"Who authored the research paper titled '{title}'?"
            gt_text = authors
        elif q_type == "date":
            q_text = f"When was the paper '{title}' published?"
            gt_text = date
        else:
            q_text = f"What categories or subjects does the paper '{title}' belong to?"
            gt_text = categories

        test_items.append({
            "id": f"q_{idx:02d}",
            "question_type": q_type,
            "question": q_text,
            "ground_truth": gt_text,
            "ground_truth_doc_ids": [paper_id],
        })

    write_json(output_path, test_items)
    return test_items
