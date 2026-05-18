from backend.rag.retriever import retrieve


def answer(query: str) -> dict:
    contexts = retrieve(query)
    return {
        "query": query,
        "answer": "chain not implemented",
        "contexts": contexts,
    }
