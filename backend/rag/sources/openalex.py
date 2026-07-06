from __future__ import annotations

import ssl
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from backend.rag.sources.paper_metadata import PaperMetadata


OPENALEX_API_URL = "https://api.openalex.org/works"


def build_openalex_url(query: str, max_results: int = 10) -> str:
    params = {
        "search": query,
        "per-page": max_results,
        "filter": "concepts.display_name.search:quantum",
    }
    return f"{OPENALEX_API_URL}?{urlencode(params)}"


def fetch_openalex_metadata(
    query: str,
    max_results: int = 10,
    timeout: int = 30,
    ca_bundle: str | None = None,
) -> list[PaperMetadata]:
    url = build_openalex_url(query, max_results=max_results)
    context = ssl.create_default_context(cafile=ca_bundle) if ca_bundle else None
    with urlopen(url, timeout=timeout, context=context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return parse_openalex_response(payload)


def parse_openalex_response(payload: dict) -> list[PaperMetadata]:
    papers: list[PaperMetadata] = []
    for item in payload.get("results", []):
        authors = [
            authorship.get("author", {}).get("display_name", "")
            for authorship in item.get("authorships", [])
            if authorship.get("author", {}).get("display_name")
        ]
        abstract = _abstract_from_inverted_index(item.get("abstract_inverted_index"))
        ids = item.get("ids", {})
        papers.append(
            PaperMetadata(
                title=item.get("title") or "Untitled",
                abstract=abstract,
                authors=authors,
                source="OpenAlex",
                source_url=item.get("id") or ids.get("openalex"),
                doi=ids.get("doi"),
                published=str(item.get("publication_year")) if item.get("publication_year") else None,
                license=item.get("best_oa_location", {}).get("license"),
                extra={
                    "openalex_id": ids.get("openalex"),
                    "cited_by_count": item.get("cited_by_count"),
                    "is_oa": item.get("open_access", {}).get("is_oa"),
                },
            )
        )
    return papers


def _abstract_from_inverted_index(index: dict | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, offsets in index.items():
        for offset in offsets:
            positions.append((offset, word))
    return " ".join(word for _, word in sorted(positions))
