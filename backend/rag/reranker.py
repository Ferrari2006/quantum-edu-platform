from __future__ import annotations

import re

from backend.rag.schema import RetrievedChunk


TOKEN_PATTERN = re.compile(r"[a-z0-9_+#.-]+|[\u4e00-\u9fff]{2,}", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in TOKEN_PATTERN.findall((text or "").lower()):
        tokens.add(token)
        if token and "\u4e00" <= token[0] <= "\u9fff":
            tokens.update(token[index : index + 2] for index in range(max(len(token) - 1, 0)))
    return tokens


def source_authority(item: RetrievedChunk) -> float:
    metadata = item.chunk.metadata or {}
    explicit = metadata.get("authority_score")
    if isinstance(explicit, (int, float)):
        return max(0.0, min(float(explicit), 1.0))

    source_text = " ".join(
        str(value)
        for value in (
            item.chunk.source,
            item.chunk.doc_id,
            item.chunk.title,
            metadata.get("publisher", ""),
            metadata.get("source_type", ""),
        )
    ).lower()
    if any(token in source_text for token in ("qiskit", "ibm quantum", "official")):
        return 1.0
    if any(token in source_text for token in ("textbook", "教材", "course", "课程")):
        return 0.9
    if any(token in source_text for token in ("doi", "journal", "openalex", "semantic scholar")):
        return 0.88
    if "arxiv" in source_text:
        return 0.8
    return 0.65


def rerank(query: str, candidates: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
    if not candidates or top_k <= 0:
        return []

    query_terms = _tokens(query)
    max_score = max((max(item.score, 0.0) for item in candidates), default=1.0) or 1.0
    seen_content: set[str] = set()
    ranked: list[RetrievedChunk] = []

    for item in candidates:
        content_key = " ".join(item.chunk.text.lower().split())[:500]
        if content_key in seen_content:
            continue
        seen_content.add(content_key)

        document_terms = _tokens(
            f"{item.chunk.title} {item.chunk.doc_id} {item.chunk.text}"
        )
        overlap = (
            len(query_terms & document_terms) / len(query_terms)
            if query_terms
            else 0.0
        )
        retrieval_score = max(item.score, 0.0) / max_score
        authority = source_authority(item)
        final_score = 0.55 * retrieval_score + 0.30 * overlap + 0.15 * authority
        ranked.append(
            RetrievedChunk(
                chunk=item.chunk,
                score=round(final_score, 4),
                retrieval_method=f"{item.retrieval_method}+validated",
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:top_k]
