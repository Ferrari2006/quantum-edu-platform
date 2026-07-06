from backend.rag.schema import Chunk


class EmbeddingModel:
    def embed_query(self, query: str) -> list[float]:
        raise NotImplementedError("Embedding backend is not configured yet.")

    def embed_chunks(self, chunks: list[Chunk]) -> list[list[float]]:
        raise NotImplementedError("Embedding backend is not configured yet.")
