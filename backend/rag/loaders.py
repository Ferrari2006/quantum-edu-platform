from pathlib import Path

from backend.rag.schema import SourceDocument


SUPPORTED_EXTENSIONS = {".md", ".txt"}


def discover_documents(root: Path) -> list[SourceDocument]:
    if not root.exists():
        return []

    documents: list[SourceDocument] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.append(
                SourceDocument(
                    doc_id=str(path.relative_to(root)).replace("\\", "/"),
                    path=str(path),
                    title=path.stem,
                    metadata={"extension": path.suffix.lower()},
                )
            )
    return documents


def load_text(document: SourceDocument) -> str:
    return Path(document.path).read_text(encoding="utf-8")
