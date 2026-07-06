from dataclasses import dataclass, field
from typing import Any, Literal


QueryRoute = Literal[
    "concept",
    "derivation",
    "code",
    "paper",
    "comparison",
    "troubleshooting",
]


@dataclass(frozen=True)
class SourceDocument:
    doc_id: str
    path: str
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    source: str
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float = 0.0
    retrieval_method: str = "placeholder"


@dataclass(frozen=True)
class Citation:
    source: str
    chunk_id: str
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RagAnswer:
    query: str
    answer: str
    route: QueryRoute
    citations: list[Citation] = field(default_factory=list)
    contexts: list[RetrievedChunk] = field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "low"
