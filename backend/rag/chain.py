from backend.rag.llm import LLMClient
from backend.rag.retriever import retrieve
from backend.rag.router import route_query
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


def answer(query: str, llm_client: LLMClient | None = None) -> dict:
    normalized_query = (query or "").strip()
    contexts = retrieve(normalized_query)
    route = route_query(normalized_query)
    serialized_contexts = [serialize_context(item) for item in contexts]

    if not contexts:
        return {
            "query": normalized_query,
            "route": route,
            "answer": "现有知识库中没有检索到足够相关的内容，暂时无法基于文档回答。",
            "citations": [],
            "contexts": [],
            "confidence": "low",
        }

    client = llm_client or LLMClient()
    generated_answer = client.generate(normalized_query, contexts)
    citations = [
        {
            "source": item.chunk.source,
            "doc_id": item.chunk.doc_id,
            "chunk_id": item.chunk.chunk_id,
            "title": item.chunk.title,
        }
        for item in contexts
    ]
    return {
        "query": normalized_query,
        "route": route,
        "answer": generated_answer,
        "citations": citations,
        "contexts": serialized_contexts,
        "confidence": "medium",
    }
