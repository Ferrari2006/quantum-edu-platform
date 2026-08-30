from __future__ import annotations

from typing import Any

from backend.db import (
    list_concept_mastery,
    list_learning_events,
    record_learning_event,
)
from backend.learning.catalog import CONCEPT_BY_ID, CONCEPT_CATALOG


EVENT_WEIGHTS = {
    "article_completed": 0.8,
    "lab_completed": 1.0,
    "quiz_attempt": 1.2,
    "game_result": 0.7,
    "question_asked": 0.25,
}


def _clamp_score(score: float) -> float:
    return max(0.0, min(1.0, float(score)))


def submit_learning_event(
    user_id: str,
    concept_id: str,
    event_type: str,
    source: str,
    score: float,
    *,
    metadata: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    if event_type not in EVENT_WEIGHTS:
        raise ValueError(f"Unsupported learning event type: {event_type}")
    normalized_concept = concept_id.strip().lower()
    if not normalized_concept:
        raise ValueError("concept_id cannot be empty")
    event = record_learning_event(
        user_id,
        normalized_concept,
        event_type,
        source.strip() or "unknown",
        _clamp_score(score),
        EVENT_WEIGHTS[event_type],
        metadata=metadata,
        idempotency_key=idempotency_key,
    )
    profile = build_learning_profile(user_id)
    event["mastery"] = next(
        (
            item
            for item in profile["concepts"]
            if item["concept_id"] == normalized_concept
        ),
        None,
    )
    return event


def build_learning_profile(user_id: str) -> dict[str, Any]:
    mastery_items = list_concept_mastery(user_id)
    enriched: list[dict[str, Any]] = []
    for item in mastery_items:
        concept = CONCEPT_BY_ID.get(item["concept_id"])
        enriched.append(
            {
                **item,
                "title": concept["title"] if concept else item["concept_id"],
                "module": concept["module"] if concept else "扩展学习",
                "difficulty": concept["difficulty"] if concept else "自定义",
            }
        )
    catalog_items = [item for item in enriched if item["concept_id"] in CONCEPT_BY_ID]
    average = (
        sum(float(item["mastery_score"]) for item in catalog_items) / len(catalog_items)
        if catalog_items
        else 0.0
    )
    return {
        "summary": {
            "average_mastery": round(average, 4),
            "covered_concepts": len(catalog_items),
            "total_concepts": len(CONCEPT_CATALOG),
            "mastered_concepts": sum(
                1 for item in catalog_items if float(item["mastery_score"]) >= 0.75
            ),
        },
        "concepts": enriched,
    }


def get_recommendations(user_id: str, limit: int = 4) -> dict[str, Any]:
    profile = build_learning_profile(user_id)
    mastery_by_id = {
        item["concept_id"]: float(item["mastery_score"])
        for item in profile["concepts"]
    }
    weak = [
        concept
        for concept in CONCEPT_CATALOG
        if concept["id"] in mastery_by_id and mastery_by_id[concept["id"]] < 0.72
    ]
    unseen = [
        concept for concept in CONCEPT_CATALOG if concept["id"] not in mastery_by_id
    ]
    candidates = weak + unseen
    recommendations: list[dict[str, Any]] = []
    used: set[str] = set()
    for concept in candidates:
        if concept["id"] in used:
            continue
        used.add(concept["id"])
        mastery = mastery_by_id.get(concept["id"])
        if mastery is None:
            reason = "尚未留下学习证据，建议按知识路径继续探索"
        else:
            reason = f"当前掌握度约 {round(mastery * 100)}%，建议结合资料与实验巩固"
        recommendations.append(
            {
                "concept_id": concept["id"],
                "article_id": concept["id"],
                "title": concept["title"],
                "module": concept["module"],
                "difficulty": concept["difficulty"],
                "mastery_score": mastery,
                "reason": reason,
            }
        )
        if len(recommendations) >= max(1, min(limit, 8)):
            break
    return {"items": recommendations, "summary": profile["summary"]}


def get_learning_timeline(user_id: str, limit: int = 50) -> dict[str, Any]:
    return {"items": list_learning_events(user_id, max(1, min(limit, 100)))}
