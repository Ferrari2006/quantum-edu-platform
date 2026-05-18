from __future__ import annotations

from pathlib import Path
from typing import Any

import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
GAME1_PATH = ROOT / "games" / "game1" / "quantum_balatro"
if str(GAME1_PATH) not in sys.path:
    sys.path.append(str(GAME1_PATH))

from games.game1.quantum_balatro.quantum_core import (  # noqa: E402
    LEVELS,
    calculate_score,
    check_boss_constraints,
    get_quantum_probs,
)
from games.game2.quantum_balatro_original.game_state import (  # noqa: E402
    Card,
    GameState,
    SchrodingerCatJoker,
)
from games.game2.quantum_balatro_original.quantum_backend import QuantumBackend  # noqa: E402

router = APIRouter()
games_instances: dict[str, Any] = {}


class GatePlacement(BaseModel):
    gate: str
    qubit: int
    slot: int


class CircuitStageRequest(BaseModel):
    gates: list[GatePlacement]


class CardPlayRequest(BaseModel):
    selected_indices: list[int]
    targets: list[list[int]]


class CircuitGameSession:
    def __init__(self) -> None:
        self.game_id = "game1"
        self.level_idx = 0
        self.hands_left = 4
        self.score = 0
        self.money = 3
        self.stored_mult = 1.0
        self.last_chips = 0
        self.last_mult = 1.0
        self.phase = "PLAYING"
        self.warning = ""
        self.gates: list[GatePlacement] = []
        self.active_jokers: list[str] = []

    def gate_sequence(self) -> list[tuple[str, int]]:
        ordered = sorted(self.gates, key=lambda item: (item.slot, item.qubit))
        return [(item.gate, item.qubit) for item in ordered]

    def level(self) -> dict[str, Any]:
        return LEVELS[self.level_idx]

    def probabilities(self) -> dict[str, float]:
        probs = get_quantum_probs(self.gate_sequence())
        return {str(state): float(value) for state, value in probs.items()}

    def serialize(self) -> dict[str, Any]:
        level = self.level()
        probs = self.probabilities()
        chips, mult = calculate_score(
            probs,
            level["target_probs"],
            self.gate_sequence(),
            self.active_jokers,
        )
        return {
            "active": True,
            "kind": "circuit",
            "game_id": self.game_id,
            "phase": self.phase,
            "level_index": self.level_idx,
            "level_count": len(LEVELS),
            "level": level,
            "hands_left": self.hands_left,
            "score": self.score,
            "money": self.money,
            "stored_mult": round(self.stored_mult, 2),
            "last_chips": self.last_chips,
            "last_mult": round(self.last_mult, 2),
            "warning": self.warning,
            "gates": [item.model_dump() for item in self.gates],
            "probabilities": probs,
            "preview": {
                "chips": chips,
                "mult": mult,
                "total": int(chips * mult * self.stored_mult),
            },
        }

    def set_gates(self, gates: list[GatePlacement]) -> None:
        valid_gates = {"H", "X", "Z", "CNOT"}
        seen_slots: set[tuple[int, int]] = set()
        clean: list[GatePlacement] = []
        for item in gates:
            if item.gate not in valid_gates:
                raise HTTPException(status_code=400, detail=f"Unsupported gate: {item.gate}")
            if item.qubit not in (0, 1) or item.slot not in range(4):
                raise HTTPException(status_code=400, detail="Gate placement is outside the circuit")
            key = (item.qubit, item.slot)
            if key in seen_slots:
                raise HTTPException(status_code=400, detail="Two gates cannot occupy one slot")
            seen_slots.add(key)
            clean.append(item)
        self.gates = clean
        self.warning = ""

    def clear(self) -> None:
        self.gates = []
        self.warning = ""

    def observe(self) -> None:
        valid, message = check_boss_constraints(
            self.gate_sequence(),
            self.level()["boss_type"],
            self.active_jokers,
        )
        if not valid:
            self.warning = message
            return

        _, mult = calculate_score(
            self.probabilities(),
            self.level()["target_probs"],
            self.gate_sequence(),
            self.active_jokers,
        )
        self.stored_mult *= mult
        self.clear()

    def play(self) -> None:
        if self.phase != "PLAYING":
            return
        valid, message = check_boss_constraints(
            self.gate_sequence(),
            self.level()["boss_type"],
            self.active_jokers,
        )
        if not valid:
            self.warning = message
            return

        chips, mult = calculate_score(
            self.probabilities(),
            self.level()["target_probs"],
            self.gate_sequence(),
            self.active_jokers,
        )
        final_mult = mult * self.stored_mult
        self.score += int(chips * final_mult)
        self.last_chips = chips
        self.last_mult = final_mult
        self.hands_left -= 1
        self.stored_mult = 1.0
        self.clear()

        if self.score >= self.level()["target"]:
            reward = self.level().get("reward", 4)
            self.money += reward + max(self.hands_left, 0)
            self.phase = "WIN" if self.level_idx == len(LEVELS) - 1 else "NEXT_BLIND"
        elif self.hands_left <= 0:
            self.phase = "GAME_OVER"

    def next_level(self) -> None:
        if self.phase != "NEXT_BLIND":
            return
        self.level_idx += 1
        self.hands_left = 4
        self.score = 0
        self.stored_mult = 1.0
        self.last_chips = 0
        self.last_mult = 1.0
        self.phase = "PLAYING"
        self.clear()


@router.get("/list")
def list_games() -> list[dict[str, str]]:
    return [
        {
            "id": "game1",
            "name": "Quantum Hacker",
            "dir": "games/game1/quantum_balatro",
            "desc": "2-qubit circuit puzzle with target probabilities and boss constraints.",
            "kind": "circuit",
        },
        {
            "id": "game2",
            "name": "Quantum Balatro Original",
            "dir": "games/game2/quantum_balatro_original",
            "desc": "Card-driven quantum roguelike with jokers, blinds, and scoring.",
            "kind": "cards",
        },
    ]


@router.post("/start/clear")
@router.post("/clear")
def clear_game() -> dict[str, str]:
    games_instances.pop("active", None)
    return {"status": "cleared"}


@router.post("/start/{game_id}")
def start_game(game_id: str) -> dict[str, str]:
    if game_id == "game1":
        games_instances["active"] = CircuitGameSession()
    elif game_id == "game2":
        backend = QuantumBackend(num_qubits=3)
        game = GameState(backend=backend)
        game.jokers.append(SchrodingerCatJoker())
        games_instances["active"] = {"id": "game2", "kind": "cards", "instance": game}
    else:
        raise HTTPException(status_code=400, detail="Unknown game id")
    return {"status": "success", "game_id": game_id}


@router.get("/state")
def get_game_state() -> dict[str, Any]:
    active = games_instances.get("active")
    if not active:
        return {"active": False}
    if isinstance(active, CircuitGameSession):
        return active.serialize()

    game = active["instance"]
    return {
        "active": True,
        "kind": "cards",
        "game_id": active["id"],
        "phase": game.phase,
        "chips": game.chips,
        "ante": game.ante,
        "blind_index": game.blind_index,
        "plays_left": game.plays_left,
        "discards_left": game.discards_left,
        "current_score": game.current_score,
        "target_score": game.target_score,
        "num_qubits": game.num_qubits,
        "last_hand_played": getattr(game, "last_hand_played", "None"),
        "last_fidelity": getattr(game, "last_fidelity", 0.0),
        "last_payout": getattr(game, "last_payout", {"base": 0, "plays": 0, "total": 0}),
        "hand_cards": [
            {
                "id": index,
                "name": card.name,
                "gate": card.gate_type,
                "rarity": card.rarity,
                "durability": card.durability,
            }
            for index, card in enumerate(game.hand)
        ],
        "jokers": [{"name": joker.name, "desc": joker.description} for joker in game.jokers],
        "shop_jokers": [
            {
                "index": index,
                "name": item["item"].name,
                "desc": item["item"].description,
                "cost": item["cost"],
            }
            for index, item in enumerate(getattr(game, "shop_jokers", []))
        ],
        "shop_pack": getattr(game, "shop_pack", False),
        "opened_card": (
            {
                "name": game.opened_card.name,
                "gate": game.opened_card.gate_type,
                "rarity": game.opened_card.rarity,
                "durability": game.opened_card.durability,
            }
            if getattr(game, "opened_card", None)
            else None
        ),
    }


def active_circuit_session() -> CircuitGameSession:
    active = games_instances.get("active")
    if not isinstance(active, CircuitGameSession):
        raise HTTPException(status_code=400, detail="The active game is not Quantum Hacker")
    return active


def active_card_game() -> GameState:
    active = games_instances.get("active")
    if not active or isinstance(active, CircuitGameSession):
        raise HTTPException(status_code=400, detail="The active game is not Quantum Balatro Original")
    return active["instance"]


def advance_card_blind(game: GameState) -> None:
    if game.phase != "REWARD":
        return

    game.blind_index += 1
    if game.blind_index >= len(game.blind_sequence):
        game.blind_index = 0
        game.ante += 1

    if game.ante > 3:
        game.phase = "VICTORY"
    else:
        game.start_new_blind()


@router.post("/circuit/stage")
def stage_circuit(req: CircuitStageRequest) -> dict[str, Any]:
    session = active_circuit_session()
    session.set_gates(req.gates)
    return session.serialize()


@router.post("/circuit/clear")
def clear_circuit() -> dict[str, Any]:
    session = active_circuit_session()
    session.clear()
    return session.serialize()


@router.post("/circuit/observe")
def observe_circuit() -> dict[str, Any]:
    session = active_circuit_session()
    session.observe()
    return session.serialize()


@router.post("/circuit/play")
def play_circuit() -> dict[str, Any]:
    session = active_circuit_session()
    session.play()
    return session.serialize()


@router.post("/circuit/next")
def next_circuit_level() -> dict[str, Any]:
    session = active_circuit_session()
    session.next_level()
    return session.serialize()


@router.post("/play")
def play_hand(req: CardPlayRequest) -> dict[str, Any]:
    game = active_card_game()
    success = game.play_hand(req.selected_indices, req.targets)
    return {"success": success, "new_score": game.current_score, "phase": game.phase}


@router.post("/discard")
def discard_hand(indices: list[int]) -> dict[str, bool]:
    game = active_card_game()
    success = game.discard_hand(indices)
    return {"success": success}


@router.post("/cards/next")
def next_card_blind() -> dict[str, str]:
    game = active_card_game()
    if game.phase == "SHOP":
        game.next_blind_from_shop()
    return {"phase": game.phase}


@router.post("/cards/shop")
def enter_card_shop() -> dict[str, str]:
    game = active_card_game()
    if game.phase == "REWARD":
        game.phase = "SHOP"
    return {"phase": game.phase}


@router.post("/cards/buy-joker/{item_index}")
def buy_card_joker(item_index: int) -> dict[str, Any]:
    game = active_card_game()
    if game.phase != "SHOP":
        raise HTTPException(status_code=400, detail="Jokers can only be bought in the shop")
    if item_index < 0 or item_index >= len(game.shop_jokers):
        raise HTTPException(status_code=404, detail="Shop joker not found")

    item = game.shop_jokers[item_index]
    if len(game.jokers) >= 5:
        raise HTTPException(status_code=400, detail="Joker limit reached")
    if game.chips < item["cost"]:
        raise HTTPException(status_code=400, detail="Not enough chips")

    game.chips -= item["cost"]
    game.jokers.append(item["item"])
    game.shop_jokers.pop(item_index)
    return {"chips": game.chips, "jokers": len(game.jokers)}


@router.post("/cards/buy-pack")
def buy_card_pack() -> dict[str, Any]:
    game = active_card_game()
    if game.phase != "SHOP":
        raise HTTPException(status_code=400, detail="Packs can only be bought in the shop")
    if not game.shop_pack:
        raise HTTPException(status_code=404, detail="No pack available")
    if game.chips < game.shop_pack["cost"]:
        raise HTTPException(status_code=400, detail="Not enough chips")

    game.chips -= game.shop_pack["cost"]
    game.opened_card = Card("Phase (RX)", "RX", "purple")
    game.shop_pack = False
    game.phase = "OPENING_PACK"
    return {"phase": game.phase, "chips": game.chips}


@router.post("/cards/collect-pack")
def collect_card_pack() -> dict[str, str]:
    game = active_card_game()
    if game.phase == "OPENING_PACK" and getattr(game, "opened_card", None):
        game.deck.append(game.opened_card)
        game.opened_card = None
        game.phase = "SHOP"
    return {"phase": game.phase}
