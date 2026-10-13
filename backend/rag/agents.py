from __future__ import annotations

from dataclasses import asdict
import re
from time import perf_counter
from typing import Any, Callable, List

from backend.rag.llm import LLMClient
from backend.rag.reranker import rerank, source_authority
from backend.rag.router import route_query
from backend.rag.schema import QueryRoute, RetrievedChunk, ReviewReport, ValidationReport


RetrieveFunction = Callable[[str, int], List[RetrievedChunk]]
CITATION_PATTERN = re.compile(r"\[(\d+)]")


def _elapsed_ms(started_at: float) -> int:
    return max(0, round((perf_counter() - started_at) * 1000))


class RetrievalAgent:
    """Understands the request route and recalls a broad candidate set."""

    def __init__(self, retrieve_fn: RetrieveFunction) -> None:
        self.retrieve_fn = retrieve_fn

    def run(
        self,
        query: str,
        top_k: int,
        route_hint: str | None = None,
    ) -> tuple[QueryRoute, list[RetrievedChunk], dict[str, Any]]:
        started_at = perf_counter()
        route = route_query(query, route_hint)
        candidate_limit = max(top_k * 3, 10)
        candidates = self.retrieve_fn(query, candidate_limit)
        trace = {
            "agent": "retrieval",
            "label": "检索智能体",
            "status": "completed",
            "duration_ms": _elapsed_ms(started_at),
            "details": {
                "route": route,
                "candidate_count": len(candidates),
                "candidate_limit": candidate_limit,
            },
        }
        return route, candidates, trace


class ValidationAgent:
    """Reranks, deduplicates, and reports source or version quality risks."""

    def run(
        self,
        query: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> tuple[list[RetrievedChunk], ValidationReport, dict[str, Any]]:
        started_at = perf_counter()
        ranked_contexts = rerank(query, candidates, max(top_k * 2, top_k))
        contexts = [item for item in ranked_contexts if item.score >= 0.2][:top_k]
        warnings: list[str] = []

        if not contexts:
            warnings.append("knowledge_base_no_match")
        if len(contexts) < min(len(ranked_contexts), top_k):
            warnings.append("low_relevance_candidates_removed")
        if any(source_authority(item) < 0.55 for item in contexts):
            warnings.append("low_authority_source_present")

        versions_by_title: dict[str, set[str]] = {}
        for item in contexts:
            version = str(item.chunk.metadata.get("version", "")).strip()
            title = (item.chunk.title or item.chunk.doc_id).strip().lower()
            if version and title:
                versions_by_title.setdefault(title, set()).add(version)
        if any(len(versions) > 1 for versions in versions_by_title.values()):
            warnings.append("source_version_conflict")

        report = ValidationReport(
            input_count=len(candidates),
            accepted_count=len(contexts),
            rejected_count=max(len(candidates) - len(contexts), 0),
            warnings=warnings,
        )
        trace = {
            "agent": "validation",
            "label": "校验智能体",
            "status": "completed" if contexts else "insufficient_context",
            "duration_ms": _elapsed_ms(started_at),
            "details": asdict(report),
        }
        return contexts, report, trace


class GenerationAgent:
    """Writes a route-specific answer grounded in validated contexts."""

    def run(
        self,
        client: LLMClient,
        query: str,
        contexts: list[RetrievedChunk],
        route: QueryRoute,
        memories: list[dict] | None,
        task_context: dict[str, Any] | None,
    ) -> tuple[str, dict[str, Any]]:
        started_at = perf_counter()
        answer = client.generate(
            query,
            contexts,
            memories=memories,
            route=route,
            task_context=task_context,
        )
        trace = {
            "agent": "generation",
            "label": "生成智能体",
            "status": "completed",
            "duration_ms": _elapsed_ms(started_at),
            "details": {"answer_chars": len(answer)},
        }
        return answer, trace


class ReviewAgent:
    """Checks answer completeness and citation validity before release."""

    def run(
        self,
        answer: str,
        contexts: list[RetrievedChunk],
        attempts: int = 1,
    ) -> tuple[ReviewReport, dict[str, Any]]:
        started_at = perf_counter()
        issues: list[str] = []
        citations = [int(value) for value in CITATION_PATTERN.findall(answer)]
        valid_citations = {value for value in citations if 1 <= value <= len(contexts)}
        invalid_citations = {value for value in citations if value < 1 or value > len(contexts)}

        if len(answer.strip()) < 12:
            issues.append("answer_too_short")
        if contexts and not valid_citations:
            issues.append("missing_valid_citation")
        if invalid_citations:
            issues.append("invalid_citation_index")

        coverage = len(valid_citations) / len(contexts) if contexts else 0.0
        report = ReviewReport(
            status="passed" if not issues else "needs_revision",
            issues=issues,
            citation_coverage=round(coverage, 4),
            attempts=attempts,
        )
        trace = {
            "agent": "review",
            "label": "审查智能体",
            "status": report.status,
            "duration_ms": _elapsed_ms(started_at),
            "details": asdict(report),
        }
        return report, trace


class MultiAgentRAGPipeline:
    """Orchestrates retrieve -> validate -> generate -> review -> optional repair."""

    def __init__(
        self,
        retrieve_fn: RetrieveFunction,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.retrieval_agent = RetrievalAgent(retrieve_fn)
        self.validation_agent = ValidationAgent()
        self.generation_agent = GenerationAgent()
        self.review_agent = ReviewAgent()
        self.llm_client = llm_client

    def run(
        self,
        query: str,
        *,
        top_k: int = 5,
        route_hint: str | None = None,
        memories: list[dict] | None = None,
        task_context: dict[str, Any] | None = None,
        include_trace: bool = True,
    ) -> dict[str, Any]:
        trace: list[dict[str, Any]] = []
        route, candidates, retrieval_trace = self.retrieval_agent.run(
            query, top_k, route_hint
        )
        trace.append(retrieval_trace)
        contexts, validation, validation_trace = self.validation_agent.run(
            query, candidates, top_k
        )
        trace.append(validation_trace)

        if not contexts:
            review = ReviewReport(
                status="insufficient_context",
                issues=["knowledge_base_no_match"],
                citation_coverage=0.0,
                attempts=0,
            )
            trace.extend(
                [
                    {
                        "agent": "generation",
                        "label": "生成智能体",
                        "status": "skipped",
                        "duration_ms": 0,
                        "details": {"reason": "insufficient_context"},
                    },
                    {
                        "agent": "review",
                        "label": "审查智能体",
                        "status": "insufficient_context",
                        "duration_ms": 0,
                        "details": asdict(review),
                    },
                ]
            )
            return {
                "query": query,
                "route": route,
                "answer": "现有知识库中没有检索到足够相关的内容，暂时无法基于可溯源资料回答。",
                "citations": [],
                "contexts": [],
                "confidence": "low",
                "validation": asdict(validation),
                "review": asdict(review),
                "agent_trace": trace if include_trace else [],
            }

        client = self.llm_client or LLMClient()
        generated_answer, generation_trace = self.generation_agent.run(
            client,
            query,
            contexts,
            route,
            memories,
            task_context,
        )
        trace.append(generation_trace)
        review, review_trace = self.review_agent.run(generated_answer, contexts)
        trace.append(review_trace)

        if review.status == "needs_revision" and hasattr(client, "revise"):
            started_at = perf_counter()
            generated_answer = client.revise(
                query,
                generated_answer,
                contexts,
                review.issues,
                memories=memories,
                route=route,
                task_context=task_context,
            )
            trace.append(
                {
                    "agent": "correction",
                    "label": "修正回路",
                    "status": "completed",
                    "duration_ms": _elapsed_ms(started_at),
                    "details": {"triggered_by": review.issues},
                }
            )
            review, second_review_trace = self.review_agent.run(
                generated_answer, contexts, attempts=2
            )
            trace.append(second_review_trace)

        average_score = sum(item.score for item in contexts) / len(contexts)
        if review.status != "passed":
            confidence = "low"
        elif len(contexts) >= 2 and average_score >= 0.7:
            confidence = "high"
        else:
            confidence = "medium"

        citations = [
            {
                "source": item.chunk.source,
                "doc_id": item.chunk.doc_id,
                "chunk_id": item.chunk.chunk_id,
                "title": item.chunk.title,
                "metadata": item.chunk.metadata,
            }
            for item in contexts
        ]
        return {
            "query": query,
            "route": route,
            "answer": generated_answer,
            "citations": citations,
            "contexts": contexts,
            "confidence": confidence,
            "validation": asdict(validation),
            "review": asdict(review),
            "agent_trace": trace if include_trace else [],
        }
