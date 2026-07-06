from typing import Sequence

from backend.rag.chunking import chunk_document
from backend.rag.config import settings
from backend.rag.loaders import discover_documents, load_text


def ingest_texts(texts: Sequence[str]) -> dict:
    normalized = [t for t in (texts or []) if isinstance(t, str) and t.strip()]
    return {
        "ingested": len(normalized),
        "status": "placeholder",
        "message": "Text ingestion API is reserved; persistent indexing is not implemented yet.",
    }


def ingest_docs() -> dict:
    documents = discover_documents(settings.docs_dir)
    chunks = []
    for document in documents:
        chunks.extend(chunk_document(document, load_text(document)))

    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "docs_dir": str(settings.docs_dir),
        "index_dir": str(settings.index_dir),
        "status": "placeholder",
        "message": "Documents were discovered and chunked, but no embeddings or index were built yet.",
    }
