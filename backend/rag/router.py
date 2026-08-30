from __future__ import annotations

from backend.rag.config import settings
from backend.rag.schema import QueryRoute


SUPPORTED_ROUTES: set[str] = {
    "concept",
    "derivation",
    "code",
    "paper",
    "comparison",
    "troubleshooting",
    "game_strategy",
    "learning_path",
}


def route_query(query: str, route_hint: str | None = None) -> QueryRoute:
    if route_hint in SUPPORTED_ROUTES:
        return route_hint  # type: ignore[return-value]

    text = (query or "").lower()
    if any(
        token in text
        for token in (
            "量子小丑牌",
            "量子魔法师",
            "关卡",
            "通关",
            "攻略",
            "game strategy",
            "level strategy",
        )
    ):
        return "game_strategy"
    if any(
        token in text
        for token in (
            "学习路径",
            "学习计划",
            "怎么学",
            "课程推荐",
            "learning path",
            "study plan",
        )
    ):
        return "learning_path"
    if any(token in text for token in ("qiskit", "pennylane", "qutip", "q#", "code", "代码", "报错")):
        return "code"
    if any(token in text for token in ("derive", "proof", "公式", "推导", "证明")):
        return "derivation"
    if any(token in text for token in ("paper", "论文", "摘要", "arxiv")):
        return "paper"
    if any(token in text for token in ("比较", "区别", "对比", "compare", "difference")):
        return "comparison"
    if any(token in text for token in ("错误", "失败", "为什么不", "troubleshoot", "debug")):
        return "troubleshooting"
    return settings.default_route  # type: ignore[return-value]
