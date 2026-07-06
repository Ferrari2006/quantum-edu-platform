from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PaperMetadata:
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    source: str = "unknown"
    source_url: str | None = None
    arxiv_id: str | None = None
    doi: str | None = None
    published: str | None = None
    updated: str | None = None
    primary_category: str | None = None
    categories: list[str] = field(default_factory=list)
    license: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:120] or "untitled"


def paper_to_markdown(paper: PaperMetadata, decision: str = "approved_api_metadata") -> str:
    tags = ["paper-metadata"]
    if paper.primary_category:
        tags.append(paper.primary_category)
    tags.extend(paper.categories[:5])
    tags = sorted(set(tags))

    front_matter = {
        "title": paper.title,
        "doc_type": "paper",
        "topic": "quantum-computing",
        "framework": None,
        "algorithm": None,
        "difficulty": "advanced",
        "version": None,
        "source": paper.source,
        "source_url": paper.source_url,
        "license": paper.license,
        "retrieved_at": date.today().isoformat(),
        "decision": decision,
        "arxiv_id": paper.arxiv_id,
        "doi": paper.doi,
        "published": paper.published,
        "updated": paper.updated,
        "primary_category": paper.primary_category,
        "categories": paper.categories,
        "authors": paper.authors,
        "tags": tags,
    }

    lines = ["---"]
    for key, value in front_matter.items():
        lines.append(f"{key}: {_yaml_value(value)}")
    lines.extend(
        [
            "---",
            "",
            f"# {paper.title}",
            "",
            "## Import Policy",
            "",
            "This record contains metadata and abstract text only. Full-text PDF storage is not enabled by default.",
            "",
            "## Authors",
            "",
            ", ".join(paper.authors) if paper.authors else "Unknown",
            "",
            "## Abstract",
            "",
            paper.abstract.strip() or "No abstract available.",
            "",
            "## Source",
            "",
            f"- Source: {paper.source}",
            f"- URL: {paper.source_url or 'Unknown'}",
            f"- DOI: {paper.doi or 'Unknown'}",
            f"- arXiv ID: {paper.arxiv_id or 'Unknown'}",
            f"- License: {paper.license or 'Unknown'}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_paper_markdown(paper: PaperMetadata, output_dir: Path, decision: str = "approved_api_metadata") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    identifier = paper.arxiv_id or paper.doi or paper.title
    path = output_dir / f"{slugify(identifier)}.md"
    path.write_text(paper_to_markdown(paper, decision=decision), encoding="utf-8")
    return path


def _yaml_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, list):
        return "[" + ", ".join(_yaml_value(item) for item in value) + "]"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)
