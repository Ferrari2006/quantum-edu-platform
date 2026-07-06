from backend.rag.schema import RetrievedChunk


def rerank(query: str, candidates: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
    return candidates[:top_k]
