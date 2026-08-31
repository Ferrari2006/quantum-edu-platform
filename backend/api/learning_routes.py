from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.auth_routes import get_current_user
from backend.learning.service import (
    build_learning_profile,
    get_learning_timeline,
    get_recommendations,
    submit_learning_event,
)


router = APIRouter(prefix="/learning", tags=["Learning Progress"])


class LearningEventRequest(BaseModel):
    concept_id: str = Field(min_length=1, max_length=100)
    event_type: Literal[
        "article_completed",
        "lab_attempt",
        "lab_completed",
        "quiz_attempt",
        "game_result",
        "question_asked",
    ]
    source: str = Field(min_length=1, max_length=80)
    score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=160)


@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_learning_event(
    payload: LearningEventRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    try:
        return submit_learning_event(
            user["id"],
            payload.concept_id,
            payload.event_type,
            payload.source,
            payload.score,
            metadata=payload.metadata,
            idempotency_key=payload.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/events")
def learning_events(
    user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(default=50, ge=1, le=100),
):
    return get_learning_timeline(user["id"], limit)


@router.get("/mastery")
def mastery(user: Annotated[dict, Depends(get_current_user)]):
    return build_learning_profile(user["id"])


@router.get("/recommendations")
def recommendations(
    user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(default=4, ge=1, le=8),
):
    return get_recommendations(user["id"], limit)
