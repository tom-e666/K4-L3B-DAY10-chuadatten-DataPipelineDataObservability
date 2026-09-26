from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone
import re
import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _parse_date(date_str: str, default_date: date) -> date:
    if not date_str:
        return default_date
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except Exception:
        return default_date


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a dataframe ready to embed and observe."""
    if isinstance(run_date, datetime):
        run_date_val = run_date.date()
    elif isinstance(run_date, date):
        run_date_val = run_date
    else:
        run_date_val = datetime.now(timezone.utc).date()

    rows = []
    for r in records:
        paper_id = normalize_whitespace(r.paper_id)
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)

        # Strip HTML/JATS tags if any remain
        summary = re.sub(r"<[^>]+>", "", summary).strip()

        authors = [normalize_whitespace(a) for a in r.authors if a]
        categories = [normalize_whitespace(c) for c in r.categories if c]
        authors_joined = compact_join(authors, ", ")
        categories_joined = compact_join(categories, ", ")
        primary_category = normalize_whitespace(r.primary_category) or (categories[0] if categories else "General")

        pub_date = _parse_date(r.published, run_date_val)
        published_str = pub_date.isoformat()
        upd_date = _parse_date(r.updated, pub_date)
        updated_str = upd_date.isoformat()

        age_days = int((run_date_val - pub_date).days)
        summary_chars = len(summary)

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published_str}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published_str,
                "updated": updated_str,
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": r.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Filter out empty paper_id or title
    df = df[df["paper_id"].str.strip().ne("") & df["title"].str.strip().ne("")]

    # Drop duplicate paper_ids
    df = df.drop_duplicates(subset=["paper_id"], keep="first").reset_index(drop=True)

    # Sort by published descending
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)

    return df
