from __future__ import annotations

from pathlib import Path

from backend.rag.schema import SourceDocument


SUPPORTED_EXTENSIONS = {".md", ".txt"}
EXCLUDED_DIRECTORIES = {"sources", "templates"}
EXCLUDED_FILENAMES = {"README.md", "manifest.md"}


def discover_documents(root: Path) -> list[SourceDocument]:
    if not root.exists():
        return []

    documents: list[SourceDocument] = []
    for path in sorted(root.rglob("*")):
        relative_path = path.relative_to(root)
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
            and path.name not in EXCLUDED_FILENAMES
            and not EXCLUDED_DIRECTORIES.intersection(relative_path.parts)
        ):
            documents.append(
                SourceDocument(
                    doc_id=str(relative_path).replace("\\", "/"),
                    path=str(path),
                    title=path.stem,
                    metadata={"extension": path.suffix.lower()},
                )
            )
    return documents


def load_text(document: SourceDocument) -> str:
    return Path(document.path).read_text(encoding="utf-8")
