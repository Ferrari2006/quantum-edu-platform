from backend.rag.config import settings
from backend.rag.schema import QueryRoute


def route_query(query: str) -> QueryRoute:
    text = (query or "").lower()
    if any(token in text for token in ("qiskit", "pennylane", "qutip", "q#", "code", "代码")):
        return "code"
    if any(token in text for token in ("derive", "proof", "公式", "推导", "证明")):
        return "derivation"
    if any(token in text for token in ("paper", "论文", "摘要", "arxiv")):
        return "paper"
    return settings.default_route  # type: ignore[return-value]
