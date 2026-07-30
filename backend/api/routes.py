from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.api.auth_routes import get_optional_user
from backend.db import list_memories, record_qa
from backend.rag.chain import answer, serialize_context
from backend.rag.ingest import ingest_docs, ingest_texts
from backend.rag.llm import LLMConfigurationError, LLMServiceError
from backend.rag.retriever import retrieve
from backend.rag.router import route_query

router = APIRouter()


class IngestRequest(BaseModel):
    texts: list[str] = Field(default_factory=list)
    from_docs: bool = False


class QueryRequest(BaseModel):
    query: str = ""

class QuantumGateOp(BaseModel):
    gate: str
    targets: list[int] = Field(default_factory=list)
    theta: float | None = None


class QuantumRunRequest(BaseModel):
    num_qubits: int = 2
    ops: list[QuantumGateOp] = Field(default_factory=list)


class FidelityRequest(BaseModel):
    num_qubits: int = 2
    ops: list[QuantumGateOp] = Field(default_factory=list)
    target_statevector: list[float] = Field(default_factory=list)

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
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="query must not be empty")
    contexts = retrieve(query)
    return {
        "query": query,
        "route": route_query(query),
        "contexts": [serialize_context(item) for item in contexts],
    }


@router.post("/rag/ask")
def rag_ask(
    payload: QueryRequest,
    user: Annotated[dict | None, Depends(get_optional_user)] = None,
):
    if not payload.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    memories = list_memories(user["id"]) if user else []
    try:
        result = answer(payload.query, memories=memories)
        record_qa(
            user["id"] if user else None,
            result["query"],
            result["answer"],
            result["route"],
        )
        return result
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/quantum/run")
def quantum_run(payload: QuantumRunRequest):
    raise HTTPException(status_code=501, detail="not implemented")


@router.post("/quantum/fidelity")
def quantum_fidelity(payload: FidelityRequest):
    raise HTTPException(status_code=501, detail="not implemented")


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
