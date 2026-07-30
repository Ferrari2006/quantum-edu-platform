from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "platform.db"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

DB_PATH = Path(os.getenv("QUANTUM_PLATFORM_DB", str(DEFAULT_DB_PATH)))
TOKEN_TTL_DAYS = int(os.getenv("AUTH_TOKEN_TTL_DAYS", "14"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (user_id, key),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS qa_history (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                query TEXT NOT NULL,
                answer TEXT,
                route TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return hmac.compare_digest(digest.hex(), expected)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(
    username: str,
    password: str,
    email: str | None = None,
) -> dict[str, Any]:
    user_id = secrets.token_urlsafe(12)
    now = utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (id, username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username, email, hash_password(password), now),
        )
        row = conn.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return row_to_dict(row) or {}


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    return row_to_dict(row)


def create_session(user_id: str) -> tuple[str, dict[str, Any]]:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=TOKEN_TTL_DAYS)
    session_id = secrets.token_urlsafe(12)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (id, user_id, token_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                hash_token(token),
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        row = conn.execute(
            """
            SELECT sessions.id, sessions.user_id, sessions.created_at,
                   sessions.expires_at, users.username, users.email
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.id = ?
            """,
            (session_id,),
        ).fetchone()
    return token, row_to_dict(row) or {}


def get_user_by_token(token: str) -> dict[str, Any] | None:
    now = utc_now()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT users.id, users.username, users.email, users.created_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
            """,
            (hash_token(token), now),
        ).fetchone()
    return row_to_dict(row)


def list_memories(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, key, value, source, created_at, updated_at
            FROM user_memories
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_memory(
    user_id: str,
    key: str,
    value: str,
    source: str = "manual",
) -> dict[str, Any]:
    memory_id = secrets.token_urlsafe(12)
    now = utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_memories
                (id, user_id, key, value, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET
                value = excluded.value,
                source = excluded.source,
                updated_at = excluded.updated_at
            """,
            (memory_id, user_id, key, value, source, now, now),
        )
        row = conn.execute(
            """
            SELECT id, key, value, source, created_at, updated_at
            FROM user_memories
            WHERE user_id = ? AND key = ?
            """,
            (user_id, key),
        ).fetchone()
    return row_to_dict(row) or {}


def delete_memory(user_id: str, memory_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM user_memories WHERE user_id = ? AND id = ?",
            (user_id, memory_id),
        )
    return cursor.rowcount > 0


def record_qa(
    user_id: str | None,
    query: str,
    answer: str | None,
    route: str | None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO qa_history
                (id, user_id, query, answer, route, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                secrets.token_urlsafe(12),
                user_id,
                query,
                answer,
                route,
                utc_now(),
            ),
        )
