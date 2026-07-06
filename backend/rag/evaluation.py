from dataclasses import dataclass


@dataclass(frozen=True)
class RagEvalCase:
    question: str
    expected_sources: list[str]
    expected_route: str = "concept"
