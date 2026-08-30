import secrets
from time import perf_counter
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.api.auth_routes import get_optional_user
from backend.db import clear_qa_history, list_memories, list_qa_history, record_qa
from backend.rag.chain import answer, serialize_context
from backend.rag.domain_tools import analyze_qiskit_code
from backend.rag.ingest import ingest_docs, ingest_texts
from backend.rag.llm import LLMConfigurationError, LLMServiceError
from backend.rag.reranker import rerank
from backend.rag.retriever import retrieve
from backend.rag.router import route_query
from backend.rag.schema import QueryRoute
from backend.quantum.service import (
    QuantumCircuitValidationError,
    calculate_fidelity,
    execute_circuit,
)

router = APIRouter()


class IngestRequest(BaseModel):
    texts: list[str] = Field(default_factory=list)
    from_docs: bool = False


class QueryRequest(BaseModel):
    query: str = Field(default="", max_length=4000)
    question: str | None = Field(default=None, max_length=4000)
    session_id: str | None = Field(default=None, min_length=8, max_length=128)
    top_k: int = Field(default=5, ge=1, le=10)
    mode: QueryRoute | None = None
    code: str | None = Field(default=None, max_length=20000)
    game_state: dict[str, Any] | None = None
    task_context: dict[str, Any] = Field(default_factory=dict)
    include_trace: bool = True

    def resolved_query(self) -> str:
        return (self.question or self.query).strip()

    def resolved_context(self) -> dict[str, Any]:
        context = dict(self.task_context)
        if self.code:
            context["code"] = self.code
            context["static_code_analysis"] = analyze_qiskit_code(self.code)
        if self.game_state:
            context["game_state"] = self.game_state
        return context

class QuantumGateOp(BaseModel):
    gate: str = Field(min_length=1, max_length=16)
    targets: list[int] = Field(default_factory=list)
    theta: float | None = None


class QuantumRunRequest(BaseModel):
    num_qubits: int = Field(default=2, ge=1, le=5)
    ops: list[QuantumGateOp] = Field(default_factory=list, max_length=40)


class FidelityRequest(BaseModel):
    num_qubits: int = Field(default=2, ge=1, le=5)
    ops: list[QuantumGateOp] = Field(default_factory=list, max_length=40)
    target_statevector: list[Any] = Field(default_factory=list)
    target_basis_state: str | None = Field(default=None, max_length=5)
    target_probabilities: dict[str, float] = Field(default_factory=dict)

class GameInfo(BaseModel):
    id: str
    name: str
    type: str
    path: str
    entry: str
    run: list[str]


@router.get("/health")
def api_health():
    return {"ok": True}

@router.get("/v1/health-data")
def health_data():
    return {"service": "quantum-edu-platform", "status": "ok"}


@router.post("/rag/ingest")
def rag_ingest(payload: IngestRequest):
    if payload.from_docs:
        return ingest_docs()
    return ingest_texts(payload.texts)

@router.post("/rag/query")
def rag_query(payload: QueryRequest):
    query = payload.resolved_query()
    if not query:
        raise HTTPException(status_code=422, detail="query must not be empty")
    candidates = retrieve(query, max(payload.top_k * 3, 10))
    contexts = rerank(query, candidates, payload.top_k)
    return {
        "query": query,
        "route": route_query(query, payload.mode),
        "contexts": [serialize_context(item) for item in contexts],
        "candidate_count": len(candidates),
    }


@router.post("/rag/ask")
def rag_ask(
    payload: QueryRequest,
    user: Annotated[dict | None, Depends(get_optional_user)] = None,
):
    query = payload.resolved_query()
    if not query:
        raise HTTPException(status_code=422, detail="query must not be empty")
    memories = list_memories(user["id"]) if user else []
    session_id = payload.session_id or secrets.token_urlsafe(16)
    started_at = perf_counter()
    try:
        result = answer(
            query,
            memories=memories,
            top_k=payload.top_k,
            route_hint=payload.mode,
            task_context=payload.resolved_context(),
            include_trace=payload.include_trace,
        )
        response_time_ms = max(0, round((perf_counter() - started_at) * 1000))
        result["session_id"] = session_id
        result["response_time_ms"] = response_time_ms
        record_qa(
            user["id"] if user else None,
            result["query"],
            result["answer"],
            result["route"],
            session_id=session_id,
            review_status=result["review"]["status"],
            metadata={
                "confidence": result["confidence"],
                "response_time_ms": response_time_ms,
                "citation_count": len(result["citations"]),
            },
        )
        return result
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/rag/history/{session_id}")
def rag_history(
    session_id: str,
    user: Annotated[dict | None, Depends(get_optional_user)] = None,
):
    items = list_qa_history(session_id, user["id"] if user else None)
    return {"session_id": session_id, "items": items, "count": len(items)}


@router.delete("/rag/history/{session_id}")
def rag_history_delete(
    session_id: str,
    user: Annotated[dict | None, Depends(get_optional_user)] = None,
):
    deleted = clear_qa_history(session_id, user["id"] if user else None)
    return {"session_id": session_id, "deleted": deleted}


@router.post("/quantum/run")
def quantum_run(payload: QuantumRunRequest):
    try:
        return execute_circuit(payload.num_qubits, payload.ops)
    except QuantumCircuitValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/quantum/fidelity")
def quantum_fidelity(payload: FidelityRequest):
    try:
        return calculate_fidelity(
            payload.num_qubits,
            payload.ops,
            target_statevector=payload.target_statevector,
            target_basis_state=payload.target_basis_state,
            target_probabilities=payload.target_probabilities,
        )
    except QuantumCircuitValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/games", response_model=list[GameInfo])
def list_games():
    return [
        GameInfo(
            id="game1",
            name="Quantum Balatro (2-qubit demo)",
            type="pygame",
            path="games/game1/quantum_balatro",
            entry="main.py",
            run=[
                "cd games/game1/quantum_balatro",
                "pip install -r requirements.txt",
                "python main.py",
            ],
        ),
        GameInfo(
            id="game2",
            name="Quantum Balatro Original (easyver)",
            type="pygame",
            path="games/game2/quantum_balatro_original",
            entry="display_engine.py",
            run=[
                "cd games/game2/quantum_balatro_original",
                "pip install -r requirements.txt",
                "python display_engine.py",
            ],
        ),
    ]
