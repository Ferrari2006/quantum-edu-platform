from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.rag.chain import answer
from backend.rag.ingest import ingest_texts

router = APIRouter()


class IngestRequest(BaseModel):
    texts: list[str] = []


class QueryRequest(BaseModel):
    query: str = ""

class QuantumGateOp(BaseModel):
    gate: str
    targets: list[int] = []
    theta: float | None = None


class QuantumRunRequest(BaseModel):
    num_qubits: int = 2
    ops: list[QuantumGateOp] = []


class FidelityRequest(BaseModel):
    num_qubits: int = 2
    ops: list[QuantumGateOp] = []
    target_statevector: list[float] = []

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
    return ingest_texts(payload.texts)

@router.post("/rag/query")
def rag_query(payload: QueryRequest):
    return answer(payload.query)


@router.post("/rag/ask")
def rag_ask(payload: QueryRequest):
    return answer(payload.query)


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
