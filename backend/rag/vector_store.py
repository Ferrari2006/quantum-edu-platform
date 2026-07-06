from backend.rag.schema import Chunk, RetrievedChunk


class VectorStore:
    def build(self, chunks: list[Chunk]) -> None:
        raise NotImplementedError("Vector index is not implemented yet.")

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        raise NotImplementedError("Vector search is not implemented yet.")
