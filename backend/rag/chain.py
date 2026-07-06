from backend.rag.retriever import retrieve
from backend.rag.router import route_query


def answer(query: str) -> dict:
    contexts = retrieve(query)
    route = route_query(query)
    return {
        "query": query,
        "route": route,
        "answer": "chain not implemented",
        "citations": [],
        "contexts": contexts,
        "confidence": "low",
    }
