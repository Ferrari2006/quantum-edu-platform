from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from games.game2.quantum_balatro_original.game_state import (  # noqa: E402
    GameState,
    SchrodingerCatJoker,
)
from games.game2.quantum_balatro_original.quantum_backend import QuantumBackend  # noqa: E402


def _targets(gate: str, source: int, num_qubits: int, target: int | None = None) -> list[int]:
    if gate in {"CNOT", "CX", "CZ", "SWAP"}:
        other = target if target is not None else (source + 1) % num_qubits
        return [source, other]
    if gate in {"CCX", "TOFFOLI"}:
        others = [qubit for qubit in range(num_qubits) if qubit != source]
        return [source, *others[:2]]
    return [source]


def candidate_plays(game: GameState) -> list[tuple[list[int], list[list[int]], list[int]]]:
    gates = [card.gate_type for card in game.hand]
    candidates: list[tuple[list[int], list[list[int]], list[int]]] = []
    seen: set[tuple] = set()

    def add(indices: list[int], targets: list[list[int]], slots: list[int]) -> None:
        if len(indices) != len(set(indices)) or not indices:
            return
        key = (tuple(indices), tuple(tuple(item) for item in targets), tuple(slots))
        if key not in seen:
            seen.add(key)
            candidates.append((indices, targets, slots))

    for index, gate in enumerate(gates):
        for source in range(game.num_qubits):
            add([index], [_targets(gate, source, game.num_qubits)], [0])

    h_indices = [index for index, gate in enumerate(gates) if gate == "H"]
    x_indices = [index for index, gate in enumerate(gates) if gate == "X"]
    cnot_indices = [index for index, gate in enumerate(gates) if gate in {"CNOT", "CX"}]
    phase_indices = [index for index, gate in enumerate(gates) if gate in {"Z", "CZ", "RZ"}]
    rotation_indices = [index for index, gate in enumerate(gates) if gate in {"RX", "RY", "RZ"}]
    swap_indices = [index for index, gate in enumerate(gates) if gate == "SWAP"]
    ccx_indices = [index for index, gate in enumerate(gates) if gate in {"CCX", "TOFFOLI"}]

    for h_index in h_indices:
        for cnot_index in cnot_indices:
            for control in range(game.num_qubits):
                for target in range(game.num_qubits):
                    if target != control:
                        add([h_index, cnot_index], [[control], [control, target]], [0, 1])

    for h_index in h_indices:
        for x_index in x_indices:
            for h_qubit in range(game.num_qubits):
                for x_qubit in range(game.num_qubits):
                    if h_qubit != x_qubit:
                        add([h_index, x_index], [[h_qubit], [x_qubit]], [0, 0])

    if len(h_indices) >= game.num_qubits:
        chosen = h_indices[: game.num_qubits]
        add(chosen, [[qubit] for qubit in range(game.num_qubits)], [0] * game.num_qubits)

    if h_indices and len(cnot_indices) >= game.num_qubits - 1:
        indices = [h_indices[0], *cnot_indices[: game.num_qubits - 1]]
        targets = [[0], *[[qubit, qubit + 1] for qubit in range(game.num_qubits - 1)]]
        add(indices, targets, list(range(game.num_qubits)))

    if h_indices and len(phase_indices) >= 2:
        indices = [h_indices[0], *phase_indices[:2]]
        targets = [[0]]
        for phase_index in phase_indices[:2]:
            targets.append(_targets(gates[phase_index], 0, game.num_qubits, 1))
        add(indices, targets, [0, 1, 2])

    if len(rotation_indices) >= 3:
        chosen = rotation_indices[:3]
        add(chosen, [[0], [0], [0]], [0, 1, 2])

    if h_indices and cnot_indices and swap_indices and game.num_qubits >= 3:
        add(
            [h_indices[0], cnot_indices[0], swap_indices[0]],
            [[0], [0, 1], [1, 2]],
            [0, 1, 2],
        )

    if len(x_indices) >= 2 and ccx_indices and game.num_qubits >= 3:
        add(
            [x_indices[0], x_indices[1], ccx_indices[0]],
            [[0], [1], [0, 1, 2]],
            [0, 0, 1],
        )

    return candidates


def best_play(game: GameState):
    best = None
    best_preview = None
    for candidate in candidate_plays(game):
        indices, targets, slots = candidate
        preview = game.preview_hand(indices, targets, slot_indices=slots)
        if not preview.get("valid"):
            continue
        if best_preview is None or preview["score"] > best_preview["score"]:
            best = candidate
            best_preview = preview
    return best, best_preview


def simulate_run(seed: int, policy: str) -> dict:
    random.seed(seed)
    game = GameState(backend=QuantumBackend(3))
    if policy == "old_free_cat":
        cat = SchrodingerCatJoker()
        cat.bonus_per_play = 5.0
        game.jokers.append(cat)

    cleared_blinds = 0
    hands_used: list[int] = []
    hand_scores: list[int] = []
    cat_bought = False
    safety = 0

    while game.phase not in {"VICTORY", "GAME_OVER"} and safety < 200:
        safety += 1
        if game.phase == "PLAYING":
            candidate, preview = best_play(game)
            if candidate is None:
                break
            indices, targets, slots = candidate
            hand_scores.append(preview["score"])
            game.play_hand(indices, targets, slot_indices=slots)
            continue

        if game.phase == "REWARD":
            cleared_blinds += 1
            hands_used.append(game.max_plays - game.plays_left)
            game.phase = "SHOP"
            continue

        if game.phase == "SHOP":
            if policy == "shop_cat" and not cat_bought:
                for index, item in enumerate(game.shop_jokers):
                    if isinstance(item["item"], SchrodingerCatJoker) and game.chips >= item["cost"]:
                        game.chips -= item["cost"]
                        game.jokers.append(item["item"])
                        game.shop_jokers.pop(index)
                        cat_bought = True
                        break
            game.next_blind_from_shop()
            continue

        break

    return {
        "won": game.phase == "VICTORY",
        "cleared_blinds": cleared_blinds,
        "hands_used": hands_used,
        "hand_scores": hand_scores,
        "ending_chips": game.chips,
        "cat_bought": cat_bought,
    }


def summarize(results: list[dict]) -> dict:
    hand_scores = [score for result in results for score in result["hand_scores"]]
    hands_used = [hands for result in results for hands in result["hands_used"]]
    sorted_scores = sorted(hand_scores)
    p90_index = min(len(sorted_scores) - 1, int(len(sorted_scores) * 0.9)) if sorted_scores else 0
    return {
        "runs": len(results),
        "win_rate": round(sum(result["won"] for result in results) / len(results), 3),
        "avg_blinds_cleared": round(statistics.mean(result["cleared_blinds"] for result in results), 2),
        "avg_hands_per_clear": round(statistics.mean(hands_used), 2) if hands_used else None,
        "median_hand_score": round(statistics.median(hand_scores), 1) if hand_scores else None,
        "p90_hand_score": sorted_scores[p90_index] if sorted_scores else None,
        "avg_ending_chips": round(statistics.mean(result["ending_chips"] for result in results), 2),
        "cat_purchase_rate": round(sum(result["cat_bought"] for result in results) / len(results), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate complete Quantum Balatro runs.")
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260706)
    args = parser.parse_args()

    report = {}
    for policy in ["no_cat", "shop_cat", "old_free_cat"]:
        results = [simulate_run(args.seed + offset, policy) for offset in range(args.runs)]
        report[policy] = summarize(results)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
