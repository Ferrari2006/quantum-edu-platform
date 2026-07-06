from typing import Any

from backend.rag.config import settings
from backend.rag.prompts import GROUNDING_SYSTEM_PROMPT
from backend.rag.schema import RetrievedChunk


class LLMConfigurationError(RuntimeError):
    pass


class LLMServiceError(RuntimeError):
    pass


class LLMClient:
    """OpenAI-compatible client configured for DeepSeek by default."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model or settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_context_chars = settings.max_context_chars

        if client is not None:
            self._client = client
            return

        resolved_api_key = api_key or settings.llm_api_key
        if not resolved_api_key:
            raise LLMConfigurationError(
                "DeepSeek API key is missing. Set DEEPSEEK_API_KEY before calling /api/rag/ask."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigurationError(
                "The openai package is required. Install backend/requirements.txt."
            ) from exc

        self._client = OpenAI(
            api_key=resolved_api_key,
            base_url=base_url or settings.llm_base_url,
            timeout=settings.llm_timeout_seconds,
        )

    def _context_message(self, contexts: list[RetrievedChunk]) -> str:
        sections: list[str] = []
        used_chars = 0
        for index, item in enumerate(contexts, start=1):
            header = f"[{index}] {item.chunk.title or item.chunk.doc_id}\nSource: {item.chunk.doc_id}\n"
            remaining = self.max_context_chars - used_chars - len(header)
            if remaining <= 0:
                break
            text = item.chunk.text[:remaining]
            sections.append(f"{header}{text}")
            used_chars += len(header) + len(text)
        return "\n\n".join(sections)

    def generate(self, query: str, contexts: list[RetrievedChunk]) -> str:
        context_text = self._context_message(contexts)
        messages = [
            {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Retrieved context:\n\n"
                    f"{context_text}\n\n"
                    f"Question: {query}\n\n"
                    "Answer using only the retrieved context and include bracket citations."
                ),
            },
        ]
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )
        except Exception as exc:
            raise LLMServiceError("The configured chat model request failed.") from exc

        content = response.choices[0].message.content
        if not content or not content.strip():
            raise LLMServiceError("The configured chat model returned an empty response.")
        return content.strip()
