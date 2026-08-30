from __future__ import annotations

from collections import Counter
from functools import lru_cache
import math
import re

from backend.rag.chunking import chunk_document
from backend.rag.config import settings
from backend.rag.loaders import discover_documents, load_text
from backend.rag.schema import Chunk, RetrievedChunk
from backend.rag.vector_store import VectorStore


TOKEN_PATTERN = re.compile(r"[a-z0-9_+#.-]+|[\u4e00-\u9fff]+", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN_PATTERN.findall((text or "").lower()):
        tokens.append(token)
        if token and "\u4e00" <= token[0] <= "\u9fff":
            tokens.extend(token[index : index + 2] for index in range(max(len(token) - 1, 0)))
            tokens.extend(token[index : index + 3] for index in range(max(len(token) - 2, 0)))
    return tokens


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
        title_text = f"{chunk.title} {chunk.doc_id}".lower()
        score = 0.0
        for term, query_frequency in query_terms.items():
            body_frequency = body_terms.get(term, 0)
            title_frequency = title_terms.get(term, 0)
            if body_frequency:
                score += query_frequency * (1.0 + math.log1p(body_frequency))
            if title_frequency:
                score += query_frequency * 2.5 * (1.0 + math.log1p(title_frequency))
            is_cjk_term = bool(term and "\u4e00" <= term[0] <= "\u9fff")
            if ((is_cjk_term and len(term) >= 2) or len(term) >= 3) and term in title_text:
                score += query_frequency * (50.0 if is_cjk_term else 200.0)
        if any(term in query_terms for term in ("安装", "配置")) and (
            "安装" in title_text or "配置" in title_text
        ):
            score += 250.0
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
    limit = top_k or settings.default_top_k
    if settings.retrieval_mode == "vector":
        store = VectorStore()
        vector_results = store.search(q, limit)
        if vector_results:
            return vector_results
    if settings.retrieval_mode == "hybrid":
        store = VectorStore()
        candidate_limit = max(limit * 5, 20)
        vector_results = store.search(q, candidate_limit)
        lexical_results = rank_chunks(q, list(load_chunks()), candidate_limit)
        hybrid_results = _merge_results(vector_results, lexical_results, limit)
        if hybrid_results:
            return hybrid_results
    return rank_chunks(q, list(load_chunks()), limit)


def _merge_results(
    vector_results: list[RetrievedChunk],
    lexical_results: list[RetrievedChunk],
    top_k: int,
) -> list[RetrievedChunk]:
    combined: dict[str, tuple[RetrievedChunk, float, set[str]]] = {}

    def add_results(items: list[RetrievedChunk], weight: float, method: str) -> None:
        if not items:
            return
        max_score = max(item.score for item in items) or 1.0
        for item in items:
            normalized_score = item.score / max_score
            existing = combined.get(item.chunk.chunk_id)
            if existing is None:
                combined[item.chunk.chunk_id] = (item, weight * normalized_score, {method})
                continue
            existing_item, existing_score, methods = existing
            methods.add(method)
            combined[item.chunk.chunk_id] = (
                existing_item,
                existing_score + weight * normalized_score,
                methods,
            )

    add_results(vector_results, 0.35, "vector")
    add_results(lexical_results, 0.65, "lexical")

    merged: list[RetrievedChunk] = []
    for item, score, methods in combined.values():
        merged.append(
            RetrievedChunk(
                chunk=item.chunk,
                score=round(score, 4),
                retrieval_method="hybrid:" + "+".join(sorted(methods)),
            )
        )

    merged.sort(key=lambda item: item.score, reverse=True)
    return merged[:top_k]
