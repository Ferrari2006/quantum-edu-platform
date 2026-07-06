from __future__ import annotations

import ssl
from urllib.parse import urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from backend.rag.sources.paper_metadata import PaperMetadata


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def build_arxiv_url(query: str, max_results: int = 10) -> str:
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    return f"{ARXIV_API_URL}?{urlencode(params)}"


def build_arxiv_id_url(arxiv_ids: list[str]) -> str:
    params = {
        "id_list": ",".join(normalize_arxiv_id(item) for item in arxiv_ids if item.strip()),
        "start": 0,
        "max_results": len(arxiv_ids),
    }
    return f"{ARXIV_API_URL}?{urlencode(params)}"


def fetch_arxiv_metadata(
    query: str,
    max_results: int = 10,
    timeout: int = 30,
    ca_bundle: str | None = None,
) -> list[PaperMetadata]:
    url = build_arxiv_url(query, max_results=max_results)
    context = ssl.create_default_context(cafile=ca_bundle) if ca_bundle else None
    with urlopen(url, timeout=timeout, context=context) as response:
        payload = response.read()
    return parse_arxiv_feed(payload)


def fetch_arxiv_metadata_by_ids(
    arxiv_ids: list[str],
    timeout: int = 30,
    ca_bundle: str | None = None,
) -> list[PaperMetadata]:
    if not arxiv_ids:
        return []
    url = build_arxiv_id_url(arxiv_ids)
    context = ssl.create_default_context(cafile=ca_bundle) if ca_bundle else None
    with urlopen(url, timeout=timeout, context=context) as response:
        payload = response.read()
    return parse_arxiv_feed(payload)


def parse_arxiv_feed(payload: bytes | str) -> list[PaperMetadata]:
    root = ET.fromstring(payload)
    papers: list[PaperMetadata] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = _text(entry, "atom:title")
        abstract = _text(entry, "atom:summary")
        url = _text(entry, "atom:id")
        arxiv_id = _arxiv_id_from_url(url)
        authors = [
            _text(author, "atom:name")
            for author in entry.findall("atom:author", ATOM_NS)
            if _text(author, "atom:name")
        ]
        primary = entry.find("arxiv:primary_category", ATOM_NS)
        primary_category = primary.attrib.get("term") if primary is not None else None
        categories = [
            category.attrib.get("term", "")
            for category in entry.findall("atom:category", ATOM_NS)
            if category.attrib.get("term")
        ]
        doi = _text(entry, "arxiv:doi") or None
        license_url = _text(entry, "arxiv:license") or None
        papers.append(
            PaperMetadata(
                title=" ".join(title.split()),
                abstract=" ".join(abstract.split()),
                authors=authors,
                source="arXiv",
                source_url=url or None,
                arxiv_id=arxiv_id,
                doi=doi,
                published=_text(entry, "atom:published") or None,
                updated=_text(entry, "atom:updated") or None,
                primary_category=primary_category,
                categories=categories,
                license=license_url,
            )
        )
    return papers


def _text(node: ET.Element, path: str) -> str:
    found = node.find(path, ATOM_NS)
    return found.text.strip() if found is not None and found.text else ""


def _arxiv_id_from_url(url: str) -> str | None:
    if not url:
        return None
    marker = "/abs/"
    if marker in url:
        return url.split(marker, 1)[1]
    return url.rsplit("/", 1)[-1]


def normalize_arxiv_id(value: str) -> str:
    item = value.strip()
    for marker in ("/abs/", "/pdf/"):
        if marker in item:
            item = item.split(marker, 1)[1]
    if item.startswith("arXiv:"):
        item = item.removeprefix("arXiv:")
    if item.endswith(".pdf"):
        item = item.removesuffix(".pdf")
    return item.strip()
