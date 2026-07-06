from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RagSettings:
    docs_dir: Path = PROJECT_ROOT / "docs" / "quantum"
    index_dir: Path = PROJECT_ROOT / "backend" / ".rag_index"
    default_top_k: int = 5
    default_route: str = "concept"
    embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "placeholder")
    llm_model: str = os.getenv("RAG_LLM_MODEL", "placeholder")


settings = RagSettings()
