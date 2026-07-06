from backend.rag.schema import RetrievedChunk


class LLMClient:
    def generate(self, query: str, contexts: list[RetrievedChunk]) -> str:
        raise NotImplementedError("LLM backend is not configured yet.")
