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

CIRCUIT_BLIND_EVENTS = [
    {
        "id": "CALIBRATION_DRIFT",
        "name": "Calibration Drift",
        "desc": "The first played H this blind grants +1.5 multiplier.",
    },
    {
        "id": "NOISY_HARDWARE",
        "name": "Noisy Hardware",
        "desc": "Circuits with more than 3 gates lose 15% chips.",
    },
    {
        "id": "CHEAP_MEASUREMENT",
        "name": "Cheap Measurement",
        "desc": "Observe roulette risk is reduced this blind.",
    },
    {
        "id": "PHASE_EXPERIMENT",
        "name": "Phase Experiment",
        "desc": "Z gates grant +70 chips this blind.",
    },
    {
        "id": "ENTANGLEMENT_TAX",
        "name": "Entanglement Tax",
        "desc": "CNOT grants +160 chips, then consumes 80 score.",
    },
]

CIRCUIT_BONUS_OBJECTIVES = [
    {
        "id": "LOW_GATE_CLEAR",
        "name": "Compact Proof",
        "desc": "Clear this blind with no more than 3 gates in the scoring hand.",
        "reward": 3,
    },
    {
        "id": "NO_CNOT_CLEAR",
        "name": "Classical Route",
        "desc": "Clear this blind without using CNOT in the scoring hand.",
        "reward": 3,
    },
    {
        "id": "Z_SCORE",
        "name": "Phase Marker",
        "desc": "Use Z in a scoring hand.",
        "reward": 2,
    },
    {
        "id": "TWO_HAND_CLIMB",
        "name": "Momentum",
        "desc": "Score higher than the previous hand twice in a row.",
        "reward": 3,
    },
]

CIRCUIT_JOKERS = [
    {
        "id": "TOPOLOGY",
        "name": "Shield",
        "desc": "Boss line limit +1",
        "archetype": "Topology",
        "synergy": "Pairs with Compiler to build a low-depth constraint breaker.",
        "cost": 4,
        "color": "cyan",
    },
    {
        "id": "ENTANGLE",
        "name": "Spark",
        "desc": "+100 chips when CNOT is used",
        "archetype": "Entanglement",
        "synergy": "Stacks with Stabilizer and any CNOT-heavy route.",
        "cost": 5,
        "color": "red",
    },
    {
        "id": "PHASE",
        "name": "Phase",
        "desc": "Z gates grant x1.5 multiplier",
        "archetype": "Phase",
        "synergy": "Best when the circuit keeps Z cards in the hand pool.",
        "cost": 6,
        "color": "gold",
    },
    {
        "id": "PHASE_BYPASS",
        "name": "Phase Key",
        "desc": "Bypass Phase Lock boss requirement",
        "archetype": "Phase",
        "synergy": "Completes the Phase build by turning boss locks into free tempo.",
        "cost": 5,
        "color": "cyan",
    },
    {
        "id": "ENTANGLE_STABILIZER",
        "name": "Stabilizer",
        "desc": "Entangler accepts any CNOT count",
        "archetype": "Entanglement",
        "synergy": "Lets Spark builds play flexible CNOT counts without losing to bosses.",
        "cost": 7,
        "color": "red",
    },
    {
        "id": "COMPRESSION",
        "name": "Compiler",
        "desc": "Sparse Memory limit +1; circuits with 3 or fewer gates gain x1.8",
        "archetype": "Compiler",
        "synergy": "Rewards short circuits; Shield helps this build survive constraints.",
        "cost": 8,
        "color": "gold",
    },
    {
        "id": "MEASURE",
        "name": "Projector",
        "desc": "+80 chips on single-state target puzzles",
        "archetype": "Measurement",
        "synergy": "A precision pick for pure-state targets and clean probability overlap.",
        "cost": 5,
        "color": "cyan",
    },
    {
        "id": "BALANCER",
        "name": "Balancer",
        "desc": "+120 chips on four-state uniform target puzzles",
        "archetype": "Measurement",
        "synergy": "Pairs with H-heavy plans that spread probability evenly.",
        "cost": 6,
        "color": "red",
    },
]

CARD_JOKER_ARCHETYPES = {
    "Maxwell's Demon": {
        "archetype": "Entanglement",
        "synergy": "Plays best with Bell Pair and CNOT-heavy hands.",
    },
    "Schrodinger's Cat": {
        "archetype": "Tempo",
        "synergy": "A comeback Joker that saves close failed hands.",
    },
    "Phase Kickback": {
        "archetype": "Phase",
        "synergy": "Turns Z and CZ cards into a multiplier lane.",
    },
    "Rotation Compiler": {
        "archetype": "Rotation",
        "synergy": "Rewards RX, RY, and RZ rotation clusters.",
    },
    "Topology Bonus": {
        "archetype": "Topology",
        "synergy": "Supports CCX, SWAP, and routing-heavy advanced circuits.",
    },
}


def serialize_card_joker(joker: Any) -> dict[str, Any]:
    meta = CARD_JOKER_ARCHETYPES.get(
        joker.name,
        {"archetype": "Wildcard", "synergy": "Flexible pick for mixed quantum hands."},
    )
    return {
        "name": joker.name,
        "desc": joker.description,
        "archetype": meta["archetype"],
        "synergy": meta["synergy"],
    }


class GatePlacement(BaseModel):
    gate: str
    qubit: int
    slot: int
    card_id: int | None = None


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
        self.last_gate_sequence: list[tuple[str, int]] = []
        self.last_probabilities: dict[str, float] = {}
        self.last_target_probs: dict[str, float] = {}
        self.last_recap_note = "Play a circuit to see how gates changed the measured probabilities."
        self.blind_event = random.choice(CIRCUIT_BLIND_EVENTS)
        self.event_used = False
        self.last_event_result = ""
        self.bonus_objective = random.choice(CIRCUIT_BONUS_OBJECTIVES)
        self.bonus_complete = False
        self.bonus_reward_claimed = False
        self.last_hand_score = 0
        self.score_climb_streak = 0
        self.recommendation_used = False
        self.recommendation_text = ""
        self.recommendation_gates: list[dict[str, Any]] = []
        self.phase = "PLAYING"
        self.warning = ""
        self.last_roulette: dict[str, str] | None = None
        self.last_roulette_chances: dict[str, int] | None = None
        self.shop_jokers: list[dict[str, Any]] = []
        self.owned_jokers: list[dict[str, Any]] = []
        self.gates: list[GatePlacement] = []
        self.next_card_id = 1
        self.deck: list[dict[str, Any]] = []
        self.hand: list[dict[str, Any]] = []
        self.discard_pile: list[dict[str, Any]] = []
        self.staged_cards: dict[int, dict[str, Any]] = {}
        self.active_jokers: list[str] = []
        self.observe_count = 0
        self.build_starting_deck()
        self.draw_cards()

    def gate_sequence(self) -> list[tuple[str, int]]:
        ordered = sorted(self.gates, key=lambda item: (item.slot, item.qubit))
        return [(item.gate, item.qubit) for item in ordered]

    def level(self) -> dict[str, Any]:
        return LEVELS[self.level_idx]

    def probabilities(self) -> dict[str, float]:
        probs = get_quantum_probs(self.gate_sequence())
        return {str(state): float(value) for state, value in probs.items()}

    def serialize(self) -> dict[str, Any]:
        self.ensure_card_pool()
        self.ensure_blind_event()
        self.ensure_bonus_objective()
        self.ensure_recommendation()
        level = self.level()
        probs = self.probabilities()
        chips, mult = calculate_score(
            probs,
            level["target_probs"],
            self.gate_sequence(),
            self.active_jokers,
        )
        preview_chips, preview_mult, preview_note = self.apply_event_preview(chips, mult)
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
            "last_recap": {
                "type": "probability",
                "title": "Circuit recap",
                "gates": [
                    {"gate": gate, "qubit": qubit}
                    for gate, qubit in self.last_gate_sequence
                ],
                "probabilities": self.last_probabilities,
                "targets": self.last_target_probs,
                "chips": self.last_chips,
                "mult": round(self.last_mult, 2),
                "score": int(self.last_chips * self.last_mult),
                "note": self.last_recap_note,
            },
            "warning": self.warning,
            "roulette_items": CIRCUIT_ROULETTE_ITEMS,
            "roulette_chances": self.last_roulette_chances or self.roulette_chances(),
            "last_roulette": self.last_roulette,
            "blind_event": {
                **self.blind_event,
                "used": self.event_used,
                "last_result": self.last_event_result,
            },
            "bonus_objective": {
                **self.bonus_objective,
                "complete": self.bonus_complete,
                "claimed": self.bonus_reward_claimed,
            },
            "recommendation": {
                "used": self.recommendation_used,
                "text": self.recommendation_text,
                "gates": self.recommendation_gates,
            },
            "shop_jokers": self.shop_jokers,
            "owned_jokers": self.owned_jokers,
            "active_jokers": self.active_jokers,
            "gates": [item.model_dump() for item in self.gates],
            "hand_cards": self.hand,
            "deck_count": len(self.deck),
            "discard_count": len(self.discard_pile),
            "probabilities": probs,
            "preview": {
                "chips": preview_chips,
                "mult": round(preview_mult, 2),
                "total": int(preview_chips * preview_mult * self.stored_mult),
                "match_chips": preview_chips,
                "gate_mult": round(preview_mult, 2),
                "stored_mult": round(self.stored_mult, 2),
                "event_note": preview_note,
            },
            "lesson": {
                "title": "Target probability puzzle",
                "body": "Match the yellow target marks. Boss blinds add constraints, so the best circuit is sometimes the simplest legal one.",
                "boss": level["boss_type"],
            },
        }

    def ensure_blind_event(self) -> None:
        if not hasattr(self, "blind_event") or not self.blind_event:
            self.blind_event = random.choice(CIRCUIT_BLIND_EVENTS)
        if not hasattr(self, "event_used"):
            self.event_used = False
        if not hasattr(self, "last_event_result"):
            self.last_event_result = ""

    def ensure_bonus_objective(self) -> None:
        if not hasattr(self, "bonus_objective") or not self.bonus_objective:
            self.bonus_objective = random.choice(CIRCUIT_BONUS_OBJECTIVES)
        if not hasattr(self, "bonus_complete"):
            self.bonus_complete = False
        if not hasattr(self, "bonus_reward_claimed"):
            self.bonus_reward_claimed = False
        if not hasattr(self, "last_hand_score"):
            self.last_hand_score = 0
        if not hasattr(self, "score_climb_streak"):
            self.score_climb_streak = 0

    def ensure_recommendation(self) -> None:
        if not hasattr(self, "recommendation_used"):
            self.recommendation_used = False
        if not hasattr(self, "recommendation_text"):
            self.recommendation_text = ""
        if not hasattr(self, "recommendation_gates"):
            self.recommendation_gates = []

    def recommend_play(self) -> dict[str, Any]:
        self.ensure_recommendation()
        if self.phase != "PLAYING":
            return {"text": self.recommendation_text, "gates": self.recommendation_gates}
        if self.recommendation_used:
            return {"text": self.recommendation_text, "gates": self.recommendation_gates}

        targets = self.level()["target_probs"]
        positive = {state: prob for state, prob in targets.items() if prob > 0.01}
        gates: list[dict[str, Any]] = []
        if set(positive) == {"00"}:
            gates = [{"gate": "KEEP", "qubit": 0, "slot": 0}]
            text = "目标只有 00：少放门，保持干净态。可以先不放门直接结算，或只放必要的 X/H。"
        elif positive.get("00", 0) > 0 and positive.get("10", 0) > 0 and len(positive) <= 2:
            gates = [{"gate": "H", "qubit": 0, "slot": 0}]
            text = "想让 00 和 10 都出现：试试把 H 放在 q0，让第一条量子线进入叠加。"
        elif positive.get("00", 0) > 0 and positive.get("11", 0) > 0:
            gates = [
                {"gate": "H", "qubit": 0, "slot": 0},
                {"gate": "CNOT", "qubit": 0, "slot": 1},
            ]
            text = "想做出成对相关：先把 H 放在 q0，再把 CNOT 放在 q0，目标选另一条线。"
        elif len(positive) >= 3:
            gates = [{"gate": "H", "qubit": 0, "slot": 0}]
            text = "目标分布比较分散：优先用 H 制造叠加，再用 X 或 CNOT 调整哪些结果更容易出现。"
        else:
            gates = [{"gate": "X", "qubit": 0, "slot": 0}]
            text = "先找目标里最高的柱子：需要翻到 1 就用 X，需要拆成多个结果就用 H，需要相关性再接 CNOT。"

        self.recommendation_used = True
        self.recommendation_text = text
        self.recommendation_gates = gates
        return {"text": text, "gates": gates}

    def update_bonus_objective(
        self,
        gate_sequence: list[tuple[str, int]],
        hand_score: int,
        cleared: bool,
    ) -> None:
        self.ensure_bonus_objective()
        gate_names = [gate for gate, _ in gate_sequence]
        objective_id = self.bonus_objective["id"]
        if self.last_hand_score and hand_score > self.last_hand_score:
            self.score_climb_streak += 1
        elif self.last_hand_score:
            self.score_climb_streak = 0
        self.last_hand_score = hand_score

        if objective_id == "LOW_GATE_CLEAR" and cleared and len(gate_names) <= 3:
            self.bonus_complete = True
        elif objective_id == "NO_CNOT_CLEAR" and cleared and "CNOT" not in gate_names:
            self.bonus_complete = True
        elif objective_id == "Z_SCORE" and hand_score > 0 and "Z" in gate_names:
            self.bonus_complete = True
        elif objective_id == "TWO_HAND_CLIMB" and self.score_climb_streak >= 2:
            self.bonus_complete = True

    def claim_bonus_reward(self) -> int:
        self.ensure_bonus_objective()
        if not self.bonus_complete or self.bonus_reward_claimed:
            return 0
        reward = int(self.bonus_objective.get("reward", 0))
        self.money += reward
        self.bonus_reward_claimed = True
        return reward

    def roulette_chances(self) -> dict[str, int]:
        self.ensure_blind_event()
        risk = min(45, int(max(0, self.stored_mult - 1) * 5) + self.observe_count * 10)
        if self.blind_event["id"] == "CHEAP_MEASUREMENT":
            risk = max(0, risk - 18)
        safe = max(25, 70 - risk)
        return {
            "SAFE": safe,
            "-1 HAND": 10 + risk // 3,
            "RESET MULT": 10 + risk // 3,
            "-200 CHIPS": 10 + risk - (risk // 3) * 2,
        }

    def apply_event_preview(self, chips: int, mult: float) -> tuple[int, float, str]:
        event_id = self.blind_event["id"]
        if self.event_used and event_id == "CALIBRATION_DRIFT":
            return chips, mult, ""
        gate_names = [gate for gate, _ in self.gate_sequence()]
        if event_id == "CALIBRATION_DRIFT" and "H" in gate_names:
            return chips, mult + 1.5, "+1.5 mult from first H"
        if event_id == "NOISY_HARDWARE" and len(gate_names) > 3:
            return int(chips * 0.85), mult, "-15% chips after 3 gates"
        if event_id == "PHASE_EXPERIMENT" and "Z" in gate_names:
            return chips + 70 * gate_names.count("Z"), mult, "+70 chips per Z"
        if event_id == "ENTANGLEMENT_TAX" and "CNOT" in gate_names:
            return chips + 160 * gate_names.count("CNOT"), mult, "+160 chips per CNOT, -80 score on play"
        return chips, mult, ""

    def apply_event_score(self, chips: int, mult: float) -> tuple[int, float, int, str]:
        chips, mult, note = self.apply_event_preview(chips, mult)
        score_cost = 0
        if self.blind_event["id"] == "ENTANGLEMENT_TAX" and "CNOT" in [gate for gate, _ in self.gate_sequence()]:
            score_cost = 80
        if self.blind_event["id"] == "CALIBRATION_DRIFT" and note:
            self.event_used = True
        return chips, mult, score_cost, note

    def build_starting_deck(self) -> None:
        for gate in ["H", "H", "H", "X", "X", "Z", "CNOT", "CNOT"]:
            self.deck.append(self.create_gate_card(gate))
        random.shuffle(self.deck)

    def ensure_card_pool(self) -> None:
        if not hasattr(self, "next_card_id"):
            self.next_card_id = 1
        if not hasattr(self, "deck"):
            self.deck = []
        if not hasattr(self, "hand"):
            self.hand = []
        if not hasattr(self, "discard_pile"):
            self.discard_pile = []
        if not hasattr(self, "staged_cards"):
            self.staged_cards = {}
        if not self.deck and not self.hand and not self.discard_pile and not self.staged_cards:
            self.build_starting_deck()
            self.draw_cards()

    def create_gate_card(self, gate: str) -> dict[str, Any]:
        details = {
            "H": ("Hadamard", "Superposition", "Split one line into 50/50 probability."),
            "X": ("Pauli-X", "Bit Flip", "Flip |0> into |1> on one line."),
            "Z": ("Pauli-Z", "Phase", "Phase tool for boss locks and joker combos."),
            "CNOT": ("CNOT", "Entangle", "Control one line and flip the other."),
        }
        name, role, text = details[gate]
        card = {
            "id": self.next_card_id,
            "gate": gate,
            "name": name,
            "role": role,
            "text": text,
        }
        self.next_card_id += 1
        return card

    def draw_cards(self, target_size: int = 5) -> None:
        while len(self.hand) < target_size:
            if not self.deck:
                if not self.discard_pile:
                    break
                self.deck = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.deck)
            self.hand.append(self.deck.pop())

    def set_gates(self, gates: list[GatePlacement]) -> None:
        self.ensure_card_pool()
        valid_gates = {"H", "X", "Z", "CNOT"}
        seen_slots: set[tuple[int, int]] = set()
        seen_cards: set[int] = set()
        card_pool = {card["id"]: card for card in [*self.hand, *self.staged_cards.values()]}
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
            if item.card_id is None:
                raise HTTPException(status_code=400, detail="A gate card is required")
            if item.card_id in seen_cards:
                raise HTTPException(status_code=400, detail="A gate card cannot be used twice")
            card = card_pool.get(item.card_id)
            if not card:
                raise HTTPException(status_code=400, detail="Gate card is not in hand")
            if card["gate"] != item.gate:
                raise HTTPException(status_code=400, detail="Gate card does not match placement")
            seen_cards.add(item.card_id)
            clean.append(item)
        self.gates = clean
        self.staged_cards = {card_id: card_pool[card_id] for card_id in seen_cards}
        self.hand = [card for card in card_pool.values() if card["id"] not in seen_cards]
        self.warning = ""

    def clear(self) -> None:
        self.ensure_card_pool()
        self.hand.extend(self.staged_cards.values())
        self.hand.sort(key=lambda card: card["id"])
        self.staged_cards = {}
        self.gates = []
        self.warning = ""

    def discard_staged_and_clear(self) -> None:
        self.ensure_card_pool()
        self.discard_pile.extend(self.staged_cards.values())
        self.staged_cards = {}
        self.gates = []
        self.warning = ""
        self.draw_cards()

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
        _, mult, _, event_note = self.apply_event_score(0, mult)
        self.last_event_result = event_note
        self.stored_mult *= mult
        self.observe_count += 1
        self.discard_staged_and_clear()
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
        chips, mult, score_cost, event_note = self.apply_event_score(chips, mult)
        played_sequence = self.gate_sequence()
        played_probs = self.probabilities()
        final_mult = mult * self.stored_mult
        hand_score = int(chips * final_mult)
        self.score = max(0, self.score - score_cost)
        self.score += hand_score
        self.last_chips = chips
        self.last_mult = final_mult
        self.last_event_result = event_note or (f"-{score_cost} score from Entanglement Tax" if score_cost else "")
        self.last_gate_sequence = played_sequence
        self.last_probabilities = {str(state): float(value) for state, value in played_probs.items()}
        self.last_target_probs = {
            str(state): float(value) for state, value in self.level()["target_probs"].items()
        }
        self.last_recap_note = self.recap_note(played_sequence, self.last_probabilities, self.last_target_probs)
        self.hands_left -= 1
        self.stored_mult = 1.0
        cleared = self.score >= self.level()["target"]
        self.update_bonus_objective(played_sequence, hand_score, cleared)
        self.discard_staged_and_clear()

        if cleared:
            reward = self.level().get("reward", 4)
            self.money += reward + max(self.hands_left, 0)
            self.claim_bonus_reward()
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
        self.last_gate_sequence = []
        self.last_probabilities = {}
        self.last_target_probs = {}
        self.last_recap_note = "Play a circuit to see how gates changed the measured probabilities."
        self.blind_event = random.choice(CIRCUIT_BLIND_EVENTS)
        self.event_used = False
        self.last_event_result = ""
        self.bonus_objective = random.choice(CIRCUIT_BONUS_OBJECTIVES)
        self.bonus_complete = False
        self.bonus_reward_claimed = False
        self.last_hand_score = 0
        self.score_climb_streak = 0
        self.recommendation_used = False
        self.recommendation_text = ""
        self.recommendation_gates = []
        self.deck = []
        self.hand = []
        self.discard_pile = []
        self.staged_cards = {}
        self.build_starting_deck()
        self.draw_cards()
        self.phase = "PLAYING"
        self.last_roulette = None
        self.last_roulette_chances = None
        self.shop_jokers = []
        self.clear()

    def recap_note(
        self,
        gate_sequence: list[tuple[str, int]],
        probabilities: dict[str, float],
        targets: dict[str, float],
    ) -> str:
        gate_names = [gate for gate, _ in gate_sequence]
        overlap = sum(min(probabilities.get(state, 0.0), target) for state, target in targets.items())
        if not gate_sequence:
            return "No gates were staged, so the circuit stayed in |00>."
        if overlap >= 0.95:
            return "Excellent target overlap: the measured distribution closely matched the blind."
        if "H" not in gate_names and len(targets) > 1:
            return "The target has multiple likely states. Try H to create superposition before scoring."
        if "CNOT" not in gate_names and any(state in targets for state in ("11", "10", "01")):
            return "The target suggests correlated states. Try CNOT after preparing a control qubit."
        if "Z" in gate_names:
            return "Z changes phase rather than direct measurement probability, so it matters most with phase rules or phase jokers."
        return "Compare the blue probabilities against the yellow targets, then adjust gates to increase overlap."


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
    if hasattr(game, "ensure_blind_event"):
        game.ensure_blind_event()
    if hasattr(game, "ensure_bonus_objective"):
        game.ensure_bonus_objective()
    if hasattr(game, "ensure_recommendation"):
        game.ensure_recommendation()
    return {
        "active": True,
        "kind": "cards",
        "show_tutorial": not getattr(game, "seen_tutorial", False) and game.phase == 'PLAYING',
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
        "blind_event": {
            **getattr(game, "blind_event", {}),
            "used": getattr(game, "event_used", False),
            "last_result": getattr(game, "last_event_result", ""),
        },
        "bonus_objective": {
            **getattr(game, "bonus_objective", {}),
            "complete": getattr(game, "bonus_complete", False),
            "claimed": getattr(game, "bonus_reward_claimed", False),
        },
        "recommendation": {
            "used": getattr(game, "recommendation_used", False),
            "text": getattr(game, "recommendation_text", ""),
            "gates": getattr(game, "recommendation_gates", []),
        },
        "last_recap": {
            "type": "fidelity",
            "title": getattr(game, "last_hand_played", "None"),
            "gates": getattr(game, "last_played_gate_types", []),
            "fidelity": getattr(game, "last_fidelity", 0.0),
            "note": getattr(game, "current_lesson", {}).get(
                "body",
                "Play a staged hand to compare your circuit with the target state.",
            ),
        },
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
                "event_note": "",
            },
        ),
        "hand_cards": [
            {
                "id": index,
                "name": card.name,
                "gate": card.gate_type,
                "rarity": card.rarity,
                "durability": card.durability,
                "lesson": getattr(card, "lesson", ""),
                "targets": getattr(card, "target_count", 1),
            }
            for index, card in enumerate(game.hand)
        ],
        "jokers": [serialize_card_joker(joker) for joker in game.jokers],
        "shop_jokers": [
            {
                **serialize_card_joker(item["item"]),
                "index": index,
                "cost": item["cost"],
            }
            for index, item in enumerate(getattr(game, "shop_jokers", []))
        ],
        "shop_pack": getattr(game, "shop_pack", False),
        "shop_joker_pack": getattr(game, "shop_joker_pack", False),
        "opened_card": (
            {
                "name": game.opened_card.name,
                "gate": game.opened_card.gate_type,
                "rarity": game.opened_card.rarity,
                "durability": game.opened_card.durability,
                "lesson": getattr(game.opened_card, "lesson", ""),
            }
            if getattr(game, "opened_card", None)
            else None
        ),
        "opened_joker_choices": [
            {
                **serialize_card_joker(joker),
                "index": index,
            }
            for index, joker in enumerate(getattr(game, "opened_joker_choices", []))
        ],
        "lesson": getattr(game, "current_lesson", {}),
        "hand_catalog": getattr(game, "hand_catalog", []),
        "pack_catalog": getattr(game, "pack_catalog", []),
    }


@router.post("/cards/tutorial/complete")
def complete_card_tutorial() -> dict[str, bool]:
    game = active_card_game()
    game.seen_tutorial = True
    return {"ok": True}


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


@router.post("/circuit/recommend")
def recommend_circuit_play() -> dict[str, Any]:
    session = active_circuit_session()
    session.recommend_play()
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


@router.post("/cards/recommend")
def recommend_card_play() -> dict[str, Any]:
    game = active_card_game()
    recommendation = game.recommend_play()
    return {"recommendation": recommendation}


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
    game.opened_card = game.create_pack_card(game.shop_pack["type"])
    game.shop_pack = False
    game.phase = "OPENING_PACK"
    return {"phase": game.phase, "chips": game.chips}


@router.post("/cards/buy-joker-pack")
def buy_card_joker_pack() -> dict[str, Any]:
    game = active_card_game()
    if game.phase != "SHOP":
        raise HTTPException(status_code=400, detail="Packs can only be bought in the shop")
    if not getattr(game, "shop_joker_pack", False):
        raise HTTPException(status_code=404, detail="No joker pack available")
    if game.chips < game.shop_joker_pack["cost"]:
        raise HTTPException(status_code=400, detail="Not enough chips")
    if len(game.jokers) >= 5:
        raise HTTPException(status_code=400, detail="Joker limit reached")

    game.chips -= game.shop_joker_pack["cost"]
    game.opened_joker_choices = game.create_joker_pack_choices()
    game.shop_joker_pack = False
    game.phase = "OPENING_JOKER_PACK"
    return {"phase": game.phase, "chips": game.chips}


@router.post("/cards/collect-pack")
def collect_card_pack() -> dict[str, str]:
    game = active_card_game()
    if game.phase == "OPENING_PACK" and getattr(game, "opened_card", None):
        game.deck.append(game.opened_card)
        game.opened_card = None
        game.phase = "SHOP"
    return {"phase": game.phase}


@router.post("/cards/collect-joker-pack/{choice_index}")
def collect_card_joker_pack(choice_index: int) -> dict[str, str]:
    game = active_card_game()
    choices = getattr(game, "opened_joker_choices", [])
    if game.phase != "OPENING_JOKER_PACK" or not choices:
        raise HTTPException(status_code=400, detail="No joker pack is open")
    if choice_index < 0 or choice_index >= len(choices):
        raise HTTPException(status_code=404, detail="Joker choice not found")
    if len(game.jokers) >= 5:
        raise HTTPException(status_code=400, detail="Joker limit reached")

    game.jokers.append(choices[choice_index])
    game.opened_joker_choices = []
    game.phase = "SHOP"
    return {"phase": game.phase}
