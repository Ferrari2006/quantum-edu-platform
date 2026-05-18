def retrieve(query: str) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []
    return [{"source": "placeholder", "content": "retriever not implemented"}]
