from __future__ import annotations

from backend.rag.agents import MultiAgentRAGPipeline
from backend.rag.llm import LLMClient
from backend.rag.retriever import retrieve
from backend.rag.schema import RetrievedChunk


def serialize_context(item: RetrievedChunk) -> dict:
    return {
        "chunk_id": item.chunk.chunk_id,
        "doc_id": item.chunk.doc_id,
        "title": item.chunk.title,
        "source": item.chunk.source,
        "content": item.chunk.text,
        "score": item.score,
        "retrieval_method": item.retrieval_method,
        "metadata": item.chunk.metadata,
    }


def answer(
    query: str,
    llm_client: LLMClient | None = None,
    memories: list[dict] | None = None,
    *,
    top_k: int = 5,
    route_hint: str | None = None,
    task_context: dict | None = None,
    include_trace: bool = True,
) -> dict:
    normalized_query = (query or "").strip()
    pipeline = MultiAgentRAGPipeline(retrieve_fn=retrieve, llm_client=llm_client)
    result = pipeline.run(
        normalized_query,
        top_k=top_k,
        route_hint=route_hint,
        memories=memories,
        task_context=task_context,
        include_trace=include_trace,
    )
    result["contexts"] = [serialize_context(item) for item in result["contexts"]]
    return result
