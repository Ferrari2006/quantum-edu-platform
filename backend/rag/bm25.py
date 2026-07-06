from backend.rag.schema import Chunk, RetrievedChunk


class BM25Index:
    def build(self, chunks: list[Chunk]) -> None:
        raise NotImplementedError("BM25 index is not implemented yet.")

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        raise NotImplementedError("BM25 search is not implemented yet.")
