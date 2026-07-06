from backend.rag.schema import Chunk, SourceDocument


def chunk_document(document: SourceDocument, text: str) -> list[Chunk]:
    # Placeholder: the real implementation should preserve Markdown headings,
    # LaTeX blocks, fenced code blocks, theorem statements, and circuit notes.
    normalized = text.strip()
    if not normalized:
        return []

    return [
        Chunk(
            chunk_id=f"{document.doc_id}#chunk-0",
            doc_id=document.doc_id,
            text=normalized,
            source=document.path,
            title=document.title,
            metadata=document.metadata,
        )
    ]
