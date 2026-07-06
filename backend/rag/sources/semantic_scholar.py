from __future__ import annotations

import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from backend.rag.sources.paper_metadata import PaperMetadata


SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def build_semantic_scholar_url(query: str, max_results: int = 10) -> str:
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,authors,year,url,externalIds,openAccessPdf,isOpenAccess",
    }
    return f"{SEMANTIC_SCHOLAR_API_URL}?{urlencode(params)}"


def fetch_semantic_scholar_metadata(
    query: str,
    max_results: int = 10,
    timeout: int = 30,
    ca_bundle: str | None = None,
) -> list[PaperMetadata]:
    url = build_semantic_scholar_url(query, max_results=max_results)
    request = Request(url, headers={"User-Agent": "quantum-edu-platform-rag-metadata-only"})
    context = ssl.create_default_context(cafile=ca_bundle) if ca_bundle else None
    with urlopen(request, timeout=timeout, context=context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return parse_semantic_scholar_response(payload)


def parse_semantic_scholar_response(payload: dict) -> list[PaperMetadata]:
    papers: list[PaperMetadata] = []
    for item in payload.get("data", []):
        external = item.get("externalIds") or {}
        authors = [
            author.get("name", "")
            for author in item.get("authors", [])
            if author.get("name")
        ]
        papers.append(
            PaperMetadata(
                title=item.get("title") or "Untitled",
                abstract=item.get("abstract") or "",
                authors=authors,
                source="Semantic Scholar",
                source_url=item.get("url"),
                arxiv_id=external.get("ArXiv"),
                doi=external.get("DOI"),
                published=str(item.get("year")) if item.get("year") else None,
                license=None,
                extra={
                    "paper_id": item.get("paperId"),
                    "is_open_access": item.get("isOpenAccess"),
                    "open_access_pdf_url": (item.get("openAccessPdf") or {}).get("url"),
                },
            )
        )
    return papers
