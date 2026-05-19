from __future__ import annotations

from pathlib import Path
from typing import Any

import random
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

CIRCUIT_ROULETTE_ITEMS = [
    {"name": "SAFE", "color": "green", "message": "Waveform Stable"},
    {"name": "-1 HAND", "color": "red", "message": "Time Dilation"},
    {"name": "RESET MULT", "color": "magenta", "message": "Multiplier Collapsed"},
    {"name": "-200 CHIPS", "color": "gold", "message": "Energy Leak"},
]

CIRCUIT_JOKERS = [
    {
        "id": "TOPOLOGY",
        "name": "Shield",
        "desc": "Boss line limit +1",
        "cost": 4,
        "color": "cyan",
    },
    {
        "id": "ENTANGLE",
        "name": "Spark",
        "desc": "+100 chips when CNOT is used",
        "cost": 5,
        "color": "red",
    },
    {
        "id": "PHASE",
        "name": "Phase",
        "desc": "Z gates grant x1.5 multiplier",
        "cost": 6,
        "color": "gold",
    },
]


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
        self.last_roulette: dict[str, str] | None = None
        self.last_roulette_chances: dict[str, int] | None = None
        self.shop_jokers: list[dict[str, Any]] = []
        self.owned_jokers: list[dict[str, Any]] = []
        self.gates: list[GatePlacement] = []
        self.active_jokers: list[str] = []
        self.observe_count = 0

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
            "observe_count": self.observe_count,
            "last_chips": self.last_chips,
            "last_mult": round(self.last_mult, 2),
            "warning": self.warning,
            "roulette_items": CIRCUIT_ROULETTE_ITEMS,
            "roulette_chances": self.last_roulette_chances or self.roulette_chances(),
            "last_roulette": self.last_roulette,
            "shop_jokers": self.shop_jokers,
            "owned_jokers": self.owned_jokers,
            "active_jokers": self.active_jokers,
            "gates": [item.model_dump() for item in self.gates],
            "probabilities": probs,
            "preview": {
                "chips": chips,
                "mult": mult,
                "total": int(chips * mult * self.stored_mult),
                "match_chips": chips,
                "gate_mult": mult,
                "stored_mult": round(self.stored_mult, 2),
            },
        }

    def roulette_chances(self) -> dict[str, int]:
        risk = min(45, int(max(0, self.stored_mult - 1) * 5) + self.observe_count * 10)
        safe = max(25, 70 - risk)
        return {
            "SAFE": safe,
            "-1 HAND": 10 + risk // 3,
            "RESET MULT": 10 + risk // 3,
            "-200 CHIPS": 10 + risk - (risk // 3) * 2,
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
        self.observe_count += 1
        self.clear()
        chances = self.roulette_chances()
        self.last_roulette_chances = chances
        self.last_roulette = random.choices(
            CIRCUIT_ROULETTE_ITEMS,
            weights=[chances[item["name"]] for item in CIRCUIT_ROULETTE_ITEMS],
            k=1,
        )[0]
        if self.last_roulette["name"] == "-1 HAND":
            self.hands_left -= 1
        elif self.last_roulette["name"] == "RESET MULT":
            self.stored_mult = 1.0
        elif self.last_roulette["name"] == "-200 CHIPS":
            self.score = max(0, self.score - 200)
        self.phase = "ROULETTE"

    def complete_roulette(self) -> None:
        if self.phase != "ROULETTE":
            return
        self.phase = "GAME_OVER" if self.hands_left <= 0 else "PLAYING"
        self.last_roulette_chances = None

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
            if self.level_idx == len(LEVELS) - 1:
                self.phase = "WIN"
            else:
                self.phase = "SHOP"
                self.generate_shop()
        elif self.hands_left <= 0:
            self.phase = "GAME_OVER"

    def generate_shop(self) -> None:
        owned_ids = {joker["id"] for joker in self.owned_jokers}
        pool = [joker for joker in CIRCUIT_JOKERS if joker["id"] not in owned_ids]
        self.shop_jokers = random.sample(pool, min(2, len(pool)))

    def buy_joker(self, joker_id: str) -> None:
        if self.phase != "SHOP":
            raise HTTPException(status_code=400, detail="Jokers can only be bought in the shop")
        for index, joker in enumerate(self.shop_jokers):
            if joker["id"] != joker_id:
                continue
            if self.money < joker["cost"]:
                raise HTTPException(status_code=400, detail="Not enough funds")
            if len(self.owned_jokers) >= 2:
                raise HTTPException(status_code=400, detail="Max jokers reached")
            self.money -= joker["cost"]
            self.owned_jokers.append(joker)
            self.active_jokers.append(joker["id"])
            self.shop_jokers.pop(index)
            return
        raise HTTPException(status_code=404, detail="Shop joker not found")

    def toggle_joker(self, joker_id: str) -> None:
        if joker_id not in {joker["id"] for joker in self.owned_jokers}:
            raise HTTPException(status_code=404, detail="Owned joker not found")
        if joker_id in self.active_jokers:
            self.active_jokers.remove(joker_id)
        else:
            self.active_jokers.append(joker_id)

    def next_level(self) -> None:
        if self.phase != "SHOP":
            return
        self.level_idx += 1
        self.hands_left = 4
        self.score = 0
        self.stored_mult = 1.0
        self.observe_count = 0
        self.last_chips = 0
        self.last_mult = 1.0
        self.phase = "PLAYING"
        self.last_roulette = None
        self.last_roulette_chances = None
        self.shop_jokers = []
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
        "last_score_breakdown": getattr(
            game,
            "last_score_breakdown",
            {
                "hand": "None",
                "base_chips": 0,
                "base_mult": 0,
                "fidelity": 0.0,
                "joker_chips_delta": 0,
                "joker_mult_delta": 0,
                "score": 0,
            },
        ),
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


@router.post("/circuit/roulette/continue")
def continue_circuit_roulette() -> dict[str, Any]:
    session = active_circuit_session()
    session.complete_roulette()
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


@router.post("/circuit/shop/buy/{joker_id}")
def buy_circuit_joker(joker_id: str) -> dict[str, Any]:
    session = active_circuit_session()
    session.buy_joker(joker_id)
    return session.serialize()


@router.post("/circuit/jokers/toggle/{joker_id}")
def toggle_circuit_joker(joker_id: str) -> dict[str, Any]:
    session = active_circuit_session()
    session.toggle_joker(joker_id)
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
