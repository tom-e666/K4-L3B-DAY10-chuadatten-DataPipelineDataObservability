from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import ensure_parent, first_sentence, normalize_whitespace


def build_test_set(
    df: pd.DataFrame,
    output_path: str | Path,
) -> list[dict[str, Any]]:
    """Build a deterministic 10-question evaluation set."""
    if len(df) < 5:
        raise ValueError(
            f"DataFrame must contain at least 5 rows, got {len(df)}."
        )

    target_path = Path(output_path)
    ensure_parent(target_path)

    rows = df.to_dict(orient="records")
    test_set: list[dict[str, Any]] = []

    # 3 summary questions
    for i in range(3):
        row = rows[i % len(rows)]
        title = normalize_whitespace(row.get("title", ""))
        summary = normalize_whitespace(row.get("summary", ""))

        test_set.append({
            "id": f"test-{len(test_set) + 1:03d}",
            "question_type": "summary",
            "question": f"What is the main contribution of the paper '{title}'?",
            "ground_truth": first_sentence(summary) or summary,
            "ground_truth_doc_ids": [str(row.get("paper_id", ""))],
        })

    # 3 author questions
    for i in range(3, 6):
        row = rows[i % len(rows)]
        title = normalize_whitespace(row.get("title", ""))
        authors = normalize_whitespace(row.get("authors_joined", ""))

        test_set.append({
            "id": f"test-{len(test_set) + 1:03d}",
            "question_type": "authors",
            "question": f"Who authored the paper '{title}'?",
            "ground_truth": authors,
            "ground_truth_doc_ids": [str(row.get("paper_id", ""))],
        })

    # 2 publication date questions
    for i in range(6, 8):
        row = rows[i % len(rows)]
        title = normalize_whitespace(row.get("title", ""))

        test_set.append({
            "id": f"test-{len(test_set) + 1:03d}",
            "question_type": "date",
            "question": f"When was the paper '{title}' published?",
            "ground_truth": str(row.get("published", "")).strip(),
            "ground_truth_doc_ids": [str(row.get("paper_id", ""))],
        })

    # 2 category questions
    for i in range(8, 10):
        row = rows[i % len(rows)]
        title = normalize_whitespace(row.get("title", ""))
        categories = normalize_whitespace(
            row.get("categories_joined", "")
            or row.get("primary_category", "")
        )

        test_set.append({
            "id": f"test-{len(test_set) + 1:03d}",
            "question_type": "categories",
            "question": f"What categories does the paper '{title}' belong to?",
            "ground_truth": categories,
            "ground_truth_doc_ids": [str(row.get("paper_id", ""))],
        })

    with target_path.open("w", encoding="utf-8") as file:
        json.dump(test_set, file, ensure_ascii=False, indent=2)

    return test_set