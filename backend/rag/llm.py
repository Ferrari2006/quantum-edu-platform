from __future__ import annotations

import json
from typing import Any

from backend.rag.config import settings
from backend.rag.prompts import GROUNDING_SYSTEM_PROMPT, ROUTE_INSTRUCTIONS
from backend.rag.schema import QueryRoute, RetrievedChunk


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

    def _memory_message(self, memories: list[dict] | None) -> str:
        if not memories:
            return ""
        lines = []
        for item in memories[:20]:
            key = str(item.get("key", "")).strip()
            value = str(item.get("value", "")).strip()
            if key and value:
                lines.append(f"- {key}: {value}")
        if not lines:
            return ""
        return "User memory:\n" + "\n".join(lines) + "\n\n"

    def _task_context_message(self, task_context: dict[str, Any] | None) -> str:
        if not task_context:
            return ""
        serialized = json.dumps(task_context, ensure_ascii=False, default=str)
        return f"Structured task context (user supplied):\n{serialized[:6000]}\n\n"

    def _complete(self, messages: list[dict[str, str]]) -> str:
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

    def generate(
        self,
        query: str,
        contexts: list[RetrievedChunk],
        memories: list[dict] | None = None,
        route: QueryRoute = "concept",
        task_context: dict[str, Any] | None = None,
    ) -> str:
        context_text = self._context_message(contexts)
        memory_text = self._memory_message(memories)
        task_context_text = self._task_context_message(task_context)
        route_instruction = ROUTE_INSTRUCTIONS.get(route, ROUTE_INSTRUCTIONS["concept"])
        messages = [
            {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{memory_text}"
                    f"{task_context_text}"
                    "Retrieved context:\n\n"
                    f"{context_text}\n\n"
                    f"Question: {query}\n\n"
                    f"Task style: {route_instruction}\n"
                    "Answer using the retrieved context. Personalize only when "
                    "the user memory is relevant, and include bracket citations "
                    "for factual claims from retrieved context."
                ),
            },
        ]
        return self._complete(messages)

    def revise(
        self,
        query: str,
        answer: str,
        contexts: list[RetrievedChunk],
        issues: list[str],
        memories: list[dict] | None = None,
        route: QueryRoute = "concept",
        task_context: dict[str, Any] | None = None,
    ) -> str:
        messages = [
            {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{self._memory_message(memories)}"
                    f"{self._task_context_message(task_context)}"
                    f"Retrieved context:\n\n{self._context_message(contexts)}\n\n"
                    f"Question: {query}\n\n"
                    f"Draft answer:\n{answer}\n\n"
                    f"Review issues: {', '.join(issues)}\n\n"
                    f"Task style: {ROUTE_INSTRUCTIONS.get(route, ROUTE_INSTRUCTIONS['concept'])}\n"
                    "Rewrite the complete answer. Resolve every review issue, retain only "
                    "claims supported by the numbered context, and use valid bracket citations."
                ),
            },
        ]
        return self._complete(messages)
