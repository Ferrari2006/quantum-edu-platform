from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator


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


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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
                session_id TEXT,
                query TEXT NOT NULL,
                answer TEXT,
                route TEXT,
                review_status TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS learning_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                score REAL NOT NULL,
                evidence_weight REAL NOT NULL,
                metadata_json TEXT,
                idempotency_key TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS concept_mastery (
                user_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                mastery_score REAL NOT NULL,
                evidence_count INTEGER NOT NULL,
                evidence_weight REAL NOT NULL,
                last_event_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, concept_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        _ensure_column(conn, "qa_history", "session_id", "TEXT")
        _ensure_column(conn, "qa_history", "review_status", "TEXT")
        _ensure_column(conn, "qa_history", "metadata_json", "TEXT")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_qa_history_session ON qa_history(session_id, created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_learning_events_user ON learning_events(user_id, created_at DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_learning_events_concept ON learning_events(user_id, concept_id, created_at DESC)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_events_idempotency "
            "ON learning_events(user_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
        )


def _ensure_column(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


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
    *,
    session_id: str | None = None,
    review_status: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO qa_history
                (id, user_id, session_id, query, answer, route,
                 review_status, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                secrets.token_urlsafe(12),
                user_id,
                session_id,
                query,
                answer,
                route,
                review_status,
                json.dumps(metadata or {}, ensure_ascii=False),
                utc_now(),
            ),
        )


def list_qa_history(
    session_id: str,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    ownership_clause = "user_id = ?" if user_id else "user_id IS NULL"
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, session_id, query, answer, route, review_status,
                   metadata_json, created_at
            FROM qa_history
            WHERE session_id = ? AND {ownership_clause}
            ORDER BY created_at ASC
            """,
            (session_id, user_id) if user_id else (session_id,),
        ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        raw_metadata = item.pop("metadata_json", None)
        try:
            item["metadata"] = json.loads(raw_metadata) if raw_metadata else {}
        except json.JSONDecodeError:
            item["metadata"] = {}
        items.append(item)
    return items


def clear_qa_history(session_id: str, user_id: str | None = None) -> int:
    ownership_clause = "user_id = ?" if user_id else "user_id IS NULL"
    with get_connection() as conn:
        cursor = conn.execute(
            f"DELETE FROM qa_history WHERE session_id = ? AND {ownership_clause}",
            (session_id, user_id) if user_id else (session_id,),
        )
    return cursor.rowcount


def record_learning_event(
    user_id: str,
    concept_id: str,
    event_type: str,
    source: str,
    score: float,
    evidence_weight: float,
    *,
    metadata: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Persist one piece of learning evidence and update aggregate mastery atomically."""
    event_id = secrets.token_urlsafe(12)
    now = utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO learning_events
                (id, user_id, concept_id, event_type, source, score,
                 evidence_weight, metadata_json, idempotency_key, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                user_id,
                concept_id,
                event_type,
                source,
                score,
                evidence_weight,
                json.dumps(metadata or {}, ensure_ascii=False),
                idempotency_key,
                now,
            ),
        )
        created = cursor.rowcount > 0
        if not created and idempotency_key:
            existing = conn.execute(
                """
                SELECT * FROM learning_events
                WHERE user_id = ? AND idempotency_key = ?
                """,
                (user_id, idempotency_key),
            ).fetchone()
            return _learning_event_to_dict(existing, created=False)

        current = conn.execute(
            """
            SELECT mastery_score, evidence_count, evidence_weight
            FROM concept_mastery
            WHERE user_id = ? AND concept_id = ?
            """,
            (user_id, concept_id),
        ).fetchone()
        previous_weight = float(current["evidence_weight"]) if current else 0.0
        previous_score = float(current["mastery_score"]) if current else 0.0
        total_weight = previous_weight + evidence_weight
        mastery_score = (
            (previous_score * previous_weight + score * evidence_weight) / total_weight
            if total_weight
            else score
        )
        conn.execute(
            """
            INSERT INTO concept_mastery
                (user_id, concept_id, mastery_score, evidence_count,
                 evidence_weight, last_event_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(user_id, concept_id) DO UPDATE SET
                mastery_score = excluded.mastery_score,
                evidence_count = concept_mastery.evidence_count + 1,
                evidence_weight = excluded.evidence_weight,
                last_event_at = excluded.last_event_at,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                concept_id,
                mastery_score,
                total_weight,
                now,
                now,
            ),
        )
        event = conn.execute(
            "SELECT * FROM learning_events WHERE id = ?",
            (event_id,),
        ).fetchone()
    return _learning_event_to_dict(event, created=True)


def _learning_event_to_dict(
    row: sqlite3.Row | None,
    *,
    created: bool,
) -> dict[str, Any]:
    if row is None:
        return {"created": created}
    item = dict(row)
    raw_metadata = item.pop("metadata_json", None)
    try:
        item["metadata"] = json.loads(raw_metadata) if raw_metadata else {}
    except json.JSONDecodeError:
        item["metadata"] = {}
    item["created"] = created
    return item


def list_learning_events(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM learning_events
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [_learning_event_to_dict(row, created=True) for row in rows]


def list_concept_mastery(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT concept_id, mastery_score, evidence_count, evidence_weight,
                   last_event_at, updated_at
            FROM concept_mastery
            WHERE user_id = ?
            ORDER BY mastery_score ASC, updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]
