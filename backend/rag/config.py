from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    # Environment variables still work without python-dotenv; it is installed
    # through backend/requirements.txt for convenient local development.
    pass


@dataclass(frozen=True)
class RagSettings:
    docs_dir: Path = PROJECT_ROOT / "docs" / "quantum"
    index_dir: Path = PROJECT_ROOT / "backend" / ".rag_index"
    default_top_k: int = 5
    default_route: str = "concept"
    embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "placeholder")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    llm_api_key: str = os.getenv("DEEPSEEK_API_KEY", os.getenv("LLM_API_KEY", ""))
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_context_chars: int = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "12000"))


settings = RagSettings()
