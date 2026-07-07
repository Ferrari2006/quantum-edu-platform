from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

from backend.rag.config import settings
from backend.rag.embeddings import EmbeddingModel
from backend.rag.schema import Chunk, RetrievedChunk


class VectorStore:
    def __init__(
        self,
        path: Path | None = None,
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        self.path = path or settings.vector_store_path
        self.embedding_model = embedding_model or EmbeddingModel()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    embedding_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS index_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM chunks")
            conn.execute("DELETE FROM index_metadata")

    def build(self, chunks: list[Chunk]) -> None:
        self.clear()
        if not chunks:
            return

        embeddings = self.embedding_model.embed_chunks(chunks)
        rows = [
            (
                chunk.chunk_id,
                chunk.doc_id,
                chunk.title,
                chunk.source,
                chunk.text,
                json.dumps(chunk.metadata, ensure_ascii=False),
                json.dumps(vector),
            )
            for chunk, vector in zip(chunks, embeddings)
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO chunks (
                    chunk_id,
                    doc_id,
                    title,
                    source,
                    text,
                    metadata_json,
                    embedding_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.executemany(
                "INSERT OR REPLACE INTO index_metadata (key, value) VALUES (?, ?)",
                [
                    ("embedding_backend", self.embedding_model.backend_name),
                    ("chunk_count", str(len(chunks))),
                ],
            )

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        normalized_query = (query or "").strip()
        if not normalized_query or not self.exists():
            return []

        query_embedding = self.embedding_model.embed_query(normalized_query)
        candidates: list[RetrievedChunk] = []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT chunk_id, doc_id, title, source, text, metadata_json, embedding_json
                FROM chunks
                """
            ).fetchall()

        for row in rows:
            chunk = Chunk(
                chunk_id=row[0],
                doc_id=row[1],
                title=row[2],
                source=row[3],
                text=row[4],
                metadata=json.loads(row[5]) if row[5] else {},
            )
            score = _cosine_similarity(query_embedding, json.loads(row[6]))
            if score > 0:
                candidates.append(
                    RetrievedChunk(
                        chunk=chunk,
                        score=round(score, 4),
                        retrieval_method=f"vector:{self.embedding_model.backend_name}",
                    )
                )

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates[:top_k]

    def exists(self) -> bool:
        if not self.path.exists():
            return False
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
        return bool(row and row[0])

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            metadata_rows = conn.execute("SELECT key, value FROM index_metadata").fetchall()
        return {
            "path": str(self.path),
            "chunks": count,
            "metadata": {key: value for key, value in metadata_rows},
        }


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    limit = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(limit))
    left_norm = math.sqrt(sum(value * value for value in left[:limit]))
    right_norm = math.sqrt(sum(value * value for value in right[:limit]))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)
