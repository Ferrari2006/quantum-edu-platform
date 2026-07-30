from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.db import (
    create_session,
    create_user,
    delete_memory,
    get_user_by_token,
    get_user_by_username,
    list_memories,
    upsert_memory,
    verify_password,
)

router = APIRouter(tags=["Auth and Memory"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class MemoryRequest(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=2000)
    source: str = Field(default="manual", max_length=40)


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user.get("email"),
        "created_at": user.get("created_at"),
    }


def auth_payload(token: str, user: dict) -> dict:
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": public_user(user),
    }


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use Bearer token authentication",
        )
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user


def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return get_user_by_token(token)


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    try:
        user = create_user(payload.username.strip(), payload.password, payload.email)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists",
        ) from exc
    token, _session = create_session(user["id"])
    return auth_payload(token, user)


@router.post("/auth/login")
def login(payload: LoginRequest):
    user = get_user_by_username(payload.username.strip())
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token, _session = create_session(user["id"])
    return auth_payload(token, user)


@router.get("/auth/me")
def me(user: Annotated[dict, Depends(get_current_user)]):
    return public_user(user)


@router.get("/memories")
def memories(user: Annotated[dict, Depends(get_current_user)]):
    return {"items": list_memories(user["id"])}


@router.post("/memories")
def save_memory(
    payload: MemoryRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    return upsert_memory(
        user["id"],
        payload.key.strip(),
        payload.value.strip(),
        payload.source.strip() or "manual",
    )


@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_memory(
    memory_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    if not delete_memory(user["id"], memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    return None
