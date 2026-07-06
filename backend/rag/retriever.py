from collections import Counter
from functools import lru_cache
import math
import re

from backend.rag.chunking import chunk_document
from backend.rag.config import settings
from backend.rag.loaders import discover_documents, load_text
from backend.rag.schema import Chunk, RetrievedChunk


TOKEN_PATTERN = re.compile(r"[a-z0-9_+#.-]+|[\u4e00-\u9fff]", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall((text or "").lower())


@lru_cache(maxsize=1)
def load_chunks() -> tuple[Chunk, ...]:
    chunks: list[Chunk] = []
    for document in discover_documents(settings.docs_dir):
        chunks.extend(chunk_document(document, load_text(document)))
    return tuple(chunks)


def clear_retriever_cache() -> None:
    load_chunks.cache_clear()


def rank_chunks(query: str, chunks: list[Chunk], top_k: int = 5) -> list[RetrievedChunk]:
    query_terms = Counter(_tokens(query))
    if not query_terms:
        return []

    ranked: list[RetrievedChunk] = []
    for chunk in chunks:
        body_terms = Counter(_tokens(chunk.text))
        title_terms = Counter(_tokens(f"{chunk.title} {chunk.doc_id}"))
        score = 0.0
        for term, query_frequency in query_terms.items():
            body_frequency = body_terms.get(term, 0)
            title_frequency = title_terms.get(term, 0)
            if body_frequency:
                score += query_frequency * (1.0 + math.log1p(body_frequency))
            if title_frequency:
                score += query_frequency * 2.5 * (1.0 + math.log1p(title_frequency))
        if score > 0:
            ranked.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=round(score, 4),
                    retrieval_method="lexical",
                )
            )

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:top_k]


def retrieve(query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    q = (query or "").strip()
    if not q:
        return []
    return rank_chunks(q, list(load_chunks()), top_k or settings.default_top_k)
