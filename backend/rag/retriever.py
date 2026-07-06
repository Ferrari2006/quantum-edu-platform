from backend.rag.config import settings
from backend.rag.router import route_query


def retrieve(query: str) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    route = route_query(q)
    return [
        {
            "source": "placeholder",
            "content": "retriever not implemented",
            "route": route,
            "score": 0.0,
            "top_k": settings.default_top_k,
        }
    ]
