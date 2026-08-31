from __future__ import annotations

from typing import Any

from backend.db import (
    list_concept_mastery,
    list_learning_events,
    record_learning_event,
)
from backend.learning.catalog import (
    AI_PRACTICE_CONCEPTS,
    CONCEPT_BY_ID,
    CONCEPT_CATALOG,
    CONCEPT_PREREQUISITES,
    GAME_CONCEPTS,
    LAB_CONCEPTS,
    LAB_TASK_BY_CONCEPT,
)


EVENT_WEIGHTS = {
    "article_completed": 0.8,
    "lab_attempt": 0.65,
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
                "mastery_level": _mastery_level(float(item["mastery_score"])),
                "prerequisites": CONCEPT_PREREQUISITES.get(item["concept_id"], []),
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
            "needs_review_concepts": sum(
                1 for item in catalog_items if float(item["mastery_score"]) < 0.5
            ),
            "total_evidence": sum(int(item["evidence_count"]) for item in enriched),
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
    ready_unseen = [
        concept for concept in unseen if _prerequisites_ready(concept["id"], mastery_by_id)
    ]
    blocked_unseen = [
        concept for concept in unseen if concept not in ready_unseen
    ]
    candidates = weak + ready_unseen + blocked_unseen
    recommendations: list[dict[str, Any]] = []
    used: set[str] = set()
    for concept in candidates:
        if concept["id"] in used:
            continue
        used.add(concept["id"])
        mastery = mastery_by_id.get(concept["id"])
        prerequisites = CONCEPT_PREREQUISITES.get(concept["id"], [])
        missing_prerequisites = [
            item for item in prerequisites if mastery_by_id.get(item, 0.0) < 0.55
        ]
        if mastery is None and prerequisites and not missing_prerequisites:
            reason = "前置概念已经具备，可以进入这个主题"
            reason_code = "prerequisites_ready"
        elif mastery is None and missing_prerequisites:
            names = [CONCEPT_BY_ID[item]["title"] for item in missing_prerequisites[:2]]
            reason = f"建议先建立前置概念：{'、'.join(names)}"
            reason_code = "prerequisites_missing"
        elif mastery is None:
            reason = "尚未留下学习证据，建议按知识路径继续探索"
            reason_code = "new_concept"
        else:
            reason = f"当前掌握度约 {round(mastery * 100)}%，建议结合资料与实验巩固"
            reason_code = "weak_mastery"
        recommendations.append(
            {
                "concept_id": concept["id"],
                "article_id": concept["id"],
                "title": concept["title"],
                "module": concept["module"],
                "difficulty": concept["difficulty"],
                "mastery_score": mastery,
                "reason": reason,
                "reason_code": reason_code,
                "prerequisites": prerequisites,
                "missing_prerequisites": missing_prerequisites,
                "missing_prerequisite_titles": [
                    CONCEPT_BY_ID[item]["title"] for item in missing_prerequisites
                ],
                "ready": not missing_prerequisites,
                "actions": _recommendation_actions(concept["id"]),
            }
        )
        if len(recommendations) >= max(1, min(limit, 8)):
            break
    return {"items": recommendations, "summary": profile["summary"]}


def get_learning_timeline(user_id: str, limit: int = 50) -> dict[str, Any]:
    items = list_learning_events(user_id, max(1, min(limit, 100)))
    for item in items:
        concept = CONCEPT_BY_ID.get(item["concept_id"])
        item["concept_title"] = concept["title"] if concept else item["concept_id"]
    return {"items": items}


def _mastery_level(score: float) -> str:
    if score >= 0.75:
        return "mastered"
    if score >= 0.5:
        return "developing"
    return "needs_review"


def _prerequisites_ready(concept_id: str, mastery_by_id: dict[str, float]) -> bool:
    return all(
        mastery_by_id.get(prerequisite, 0.0) >= 0.55
        for prerequisite in CONCEPT_PREREQUISITES.get(concept_id, [])
    )


def _recommendation_actions(concept_id: str) -> list[dict[str, str]]:
    actions = [
        {
            "kind": "article",
            "label": "阅读或复习主题",
            "path": f"/knowledge/{concept_id}",
        }
    ]
    if concept_id in LAB_CONCEPTS:
        task_id = LAB_TASK_BY_CONCEPT.get(concept_id)
        path = f"/lab?task={task_id}" if task_id else "/lab"
        actions.append({"kind": "lab", "label": "在线路实验室验证", "path": path})
    elif concept_id in GAME_CONCEPTS:
        actions.append({"kind": "game", "label": "进入游戏实验场", "path": "/game"})
    elif concept_id in AI_PRACTICE_CONCEPTS:
        actions.append({"kind": "ai", "label": "让AI分步讲解", "path": "/oa"})
    return actions
