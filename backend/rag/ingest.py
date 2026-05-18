from typing import Sequence


def ingest_texts(texts: Sequence[str]) -> dict:
    normalized = [t for t in (texts or []) if isinstance(t, str) and t.strip()]
    return {"ingested": len(normalized)}
