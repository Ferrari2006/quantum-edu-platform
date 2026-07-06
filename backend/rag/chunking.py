import re

from backend.rag.schema import Chunk, SourceDocument


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    match = re.match(r"^---\s*\n.*?\n---\s*\n", text, flags=re.DOTALL)
    return text[match.end() :] if match else text


def _markdown_blocks(text: str) -> list[str]:
    """Split at headings/blank lines while keeping fenced code blocks intact."""
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False

    def flush() -> None:
        block = "\n".join(current).strip()
        if block:
            blocks.append(block)
        current.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
        if not in_fence and (stripped.startswith("#") or not stripped):
            flush()
            if stripped.startswith("#"):
                current.append(line)
            continue
        current.append(line)
    flush()
    return blocks


def _split_oversized_block(block: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    remaining = block.strip()
    while len(remaining) > max_chars:
        split_at = max(
            remaining.rfind("\n", 0, max_chars + 1),
            remaining.rfind(" ", 0, max_chars + 1),
        )
        if split_at < max_chars // 2:
            split_at = max_chars
        pieces.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def chunk_document(
    document: SourceDocument,
    text: str,
    max_chars: int = 1200,
) -> list[Chunk]:
    normalized = _strip_frontmatter(text).strip()
    if not normalized:
        return []

    packed: list[str] = []
    current = ""
    for block in _markdown_blocks(normalized):
        for piece in _split_oversized_block(block, max_chars):
            candidate = f"{current}\n\n{piece}".strip() if current else piece
            if current and len(candidate) > max_chars:
                packed.append(current)
                current = piece
            else:
                current = candidate
    if current:
        packed.append(current)

    chunks: list[Chunk] = []
    for index, chunk_text in enumerate(packed):
        chunks.append(
            Chunk(
                chunk_id=f"{document.doc_id}#chunk-{index}",
                doc_id=document.doc_id,
                text=chunk_text,
                source=document.path,
                title=document.title,
                metadata=document.metadata,
            )
        )
    return chunks
