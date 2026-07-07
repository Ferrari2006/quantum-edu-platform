from __future__ import annotations

import hashlib
import math
import re

from backend.rag.config import settings
from backend.rag.schema import Chunk


TOKEN_PATTERN = re.compile(r"[a-z0-9_+#.-]+|[\u4e00-\u9fff]+", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN_PATTERN.findall((text or "").lower()):
        tokens.append(token)
        if token and "\u4e00" <= token[0] <= "\u9fff":
            tokens.extend(token[index : index + 2] for index in range(max(len(token) - 1, 0)))
            tokens.extend(token[index : index + 3] for index in range(max(len(token) - 2, 0)))
    return tokens


def _stable_bucket(token: str, dim: int) -> tuple[int, float]:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    sign = 1.0 if value & 1 else -1.0
    return value % dim, sign


class EmbeddingModel:
    """Small embedding adapter with a dependency-free default backend.

    The default `hashing` backend is not a neural semantic embedding model, but
    it creates stable normalized vectors and a persistent vector index without
    requiring model downloads. Set RAG_EMBEDDING_MODEL to a sentence-transformers
    model name to use a stronger local/remote model when that package is
    installed.
    """

    def __init__(self, model_name: str | None = None, dim: int | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self.dim = dim or settings.embedding_dim
        self._sentence_model = None

        if self.model_name not in {"hashing", "placeholder"}:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required for neural embeddings. "
                    "Install it or set RAG_EMBEDDING_MODEL=hashing."
                ) from exc
            self._sentence_model = SentenceTransformer(self.model_name)

    @property
    def backend_name(self) -> str:
        return self.model_name if self._sentence_model is not None else "hashing"

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0] if query else [0.0] * self.dim

    def embed_chunks(self, chunks: list[Chunk]) -> list[list[float]]:
        texts = [
            "\n".join(part for part in (chunk.title, chunk.doc_id, chunk.text) if part)
            for chunk in chunks
        ]
        return self.embed_texts(texts)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._sentence_model is not None:
            vectors = self._sentence_model.encode(texts, normalize_embeddings=True)
            return [vector.tolist() for vector in vectors]
        return [self._hashing_embedding(text) for text in texts]

    def _hashing_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = _tokens(text)
        if not tokens:
            return vector

        for token in tokens:
            bucket, sign = _stable_bucket(token, self.dim)
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            return vector
        return [value / norm for value in vector]
