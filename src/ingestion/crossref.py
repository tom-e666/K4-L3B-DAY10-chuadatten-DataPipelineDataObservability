from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_abstract(raw_abstract: str) -> str:
    if not raw_abstract:
        return ""
    text = re.sub(r"<[^>]+>", "", raw_abstract)
    return normalize_whitespace(text)


def _parse_date(item: dict) -> tuple[str, str]:
    pub_str = ""
    upd_str = ""

    published_obj = item.get("published") or item.get("issued") or {}
    if isinstance(published_obj, dict):
        date_parts = published_obj.get("date-parts", [])
        if date_parts and isinstance(date_parts[0], list):
            parts = date_parts[0]
            if len(parts) >= 3:
                pub_str = f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
            elif len(parts) == 2:
                pub_str = f"{parts[0]:04d}-{parts[1]:02d}-01"
            elif len(parts) == 1:
                pub_str = f"{parts[0]:04d}-01-01"

    if not pub_str and item.get("published"):
        pub_str = str(item["published"])[:10]

    created_obj = item.get("created") or {}
    if isinstance(created_obj, dict) and "date-time" in created_obj:
        upd_str = str(created_obj["date-time"])[:10]
    elif not upd_str and item.get("updated"):
        upd_str = str(item["updated"])[:10]

    if not pub_str:
        pub_str = upd_str or "2026-01-01"
    if not upd_str:
        upd_str = pub_str

    return pub_str, upd_str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref API payload into a list of PaperRecord objects."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        paper_id = item.get("DOI") or item.get("paper_id") or ""

        raw_title = item.get("title", "")
        if isinstance(raw_title, list):
            title = raw_title[0] if raw_title else ""
        else:
            title = str(raw_title)
        title = normalize_whitespace(title)

        summary = _clean_abstract(item.get("abstract") or item.get("summary") or "")

        raw_authors = item.get("author") or item.get("authors") or []
        authors: list[str] = []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, dict):
                    given = a.get("given", "").strip()
                    family = a.get("family", "").strip()
                    name = f"{given} {family}".strip()
                    if name:
                        authors.append(name)
                elif isinstance(a, str):
                    authors.append(a.strip())

        raw_cats = item.get("subject") or item.get("categories") or []
        categories: list[str] = []
        if isinstance(raw_cats, list):
            categories = [str(c).strip() for c in raw_cats if c]
        elif isinstance(raw_cats, str):
            categories = [raw_cats.strip()]

        primary_category = item.get("primary_category") or (categories[0] if categories else "General")

        pub_date, upd_date = _parse_date(item)
        abs_url = item.get("URL") or item.get("abs_url") or (f"https://doi.org/{paper_id}" if paper_id else "")
        pdf_url = item.get("pdf_url") or ""
        comment = item.get("comment") or ""

        record = PaperRecord(
            paper_id=paper_id,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=pub_date,
            updated=upd_date,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=comment,
        )
        records.append(record)

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch source records from Crossref API or fallback to local snapshot, saving raw artifacts."""
    raw_api_path = settings.paths.raw_api_response
    raw_records_path = settings.paths.raw_records_json

    payload = None
    if settings.refresh_source:
        try:
            query_params = {
                "query": settings.source_query,
                "filter": settings.source_filter,
                "rows": str(settings.max_results),
            }
            url = f"https://api.crossref.org/works?{urllib.parse.urlencode(query_params)}"
            req = urllib.request.Request(
                url, headers={"User-Agent": "DataObservabilityLab/1.0 (mailto:lab@example.com)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            payload = None

    if payload is None:
        if raw_api_path.exists():
            payload = read_json(raw_api_path)
        else:
            raise FileNotFoundError(f"Raw API response file not found at {raw_api_path}")

    write_json(raw_api_path, payload)
    records = parse_crossref_payload(payload)
    write_json(raw_records_path, [asdict(r) for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load JSON snapshot and map into PaperRecord instances."""
    if not path.exists():
        raise FileNotFoundError(f"Raw records file not found at {path}")
    raw_data = read_json(path)
    return [PaperRecord(**item) for item in raw_data]
