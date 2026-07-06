import pytest

from backend.api.game_routes import CircuitGameSession
from games.game1.quantum_balatro.quantum_core import calculate_score_details, get_quantum_probs
from games.game2.quantum_balatro_original.game_state import Card, GameState, SchrodingerCatJoker
from games.game2.quantum_balatro_original.quantum_backend import QuantumBackend


class MockBackend:
    def __init__(self, num_qubits=3):
        self.num_qubits = num_qubits
        self.applied = []
        self.history = []

    def reset_circuit(self):
        self.applied.clear()

    def upgrade_qubits(self, n):
        self.num_qubits = n

    def apply_gate(self, gate_type, targets, theta=None):
        # 简单记录调用
        if any(t < 0 or t >= self.num_qubits for t in targets):
            raise ValueError("target out of range")
        self.applied.append((gate_type, tuple(targets), theta))
        self.history.append((gate_type, tuple(targets), theta))

    def calculate_fidelity(self, target_state):
        return 1.0

    def get_amplitudes(self):
        return [1.0] + [0.0] * (2 ** self.num_qubits - 1)

    def get_statevector(self):
        return None

    def clone(self):
        cloned = MockBackend(self.num_qubits)
        cloned.applied = self.applied[:]
        cloned.history = self.history[:]
        return cloned


def test_play_hand_success():
    backend = MockBackend()
    game = GameState(backend=backend)
    # 确保手牌已抽取
    assert len(game.hand) >= 1

    # 选用第一张卡打到 q0
    success = game.play_hand([0], [[0]])
    assert success is True
    assert game.plays_left == game.max_plays - 1
    assert game.last_score_breakdown is not None


def test_play_hand_invalid_index():
    backend = MockBackend()
    game = GameState(backend=backend)
    # 使用非法索引
    success = game.play_hand([999], [[0]])
    assert success is False
    assert "Invalid" in game.warning


def test_play_hand_preserves_slot_order_and_target_pairing():
    backend = MockBackend()
    game = GameState(backend=backend)
    game.hand = [Card("X", "X"), Card("H", "H")]

    success = game.play_hand([1, 0], [[2], [1]])

    assert success is True
    assert backend.history[:2] == [("H", (2,), None), ("X", (1,), None)]


def test_preview_is_ordered_and_does_not_mutate_game():
    backend = MockBackend()
    game = GameState(backend=backend)
    game.hand = [Card("X", "X"), Card("H", "H")]
    plays_before = game.plays_left
    hand_before = game.hand[:]

    preview = game.preview_hand([1, 0], [[2], [1]])

    assert preview["valid"] is True
    assert preview["gate_sequence"] == [
        {"gate": "H", "targets": [2]},
        {"gate": "X", "targets": [1]},
    ]
    assert game.plays_left == plays_before
    assert game.hand == hand_before
    assert backend.applied == []


def test_cnot_without_superposition_is_not_bell_pair():
    game = GameState(backend=QuantumBackend(3))
    game.hand = [Card("X", "X"), Card("CNOT", "CNOT")]

    preview = game.preview_hand([0, 1], [[0], [0, 1]])

    assert preview["valid"] is True
    assert not preview["hand"].startswith("Bell Pair")


def test_bell_pair_respects_gate_order_and_target_qubits():
    game = GameState(backend=QuantumBackend(3))
    game.hand = [Card("H", "H"), Card("CNOT", "CNOT")]

    preview = game.preview_hand([0, 1], [[1], [1, 2]])
    reversed_preview = game.preview_hand([1, 0], [[1, 2], [1]])

    assert preview["hand"].startswith("Bell Pair")
    assert preview["fidelity"] == 1.0
    assert not reversed_preview["hand"].startswith("Bell Pair")


def test_ghz_requires_connected_entangling_chain_and_ghz_state():
    game = GameState(backend=QuantumBackend(3))
    game.hand = [Card("H", "H"), Card("CNOT A", "CNOT"), Card("CNOT B", "CNOT")]

    preview = game.preview_hand([0, 1, 2], [[0], [0, 1], [1, 2]])

    assert preview["hand"].startswith("GHZ State")
    assert preview["fidelity"] == 1.0


def test_incomplete_ghz_recipe_does_not_receive_ghz_hand():
    game = GameState(backend=QuantumBackend(3))
    game.hand = [Card("H", "H"), Card("CNOT", "CNOT"), Card("X", "X")]

    preview = game.preview_hand([0, 1, 2], [[0], [0, 1], [2]])

    assert not preview["hand"].startswith("GHZ State")


def test_advanced_hands_require_matching_circuit_and_final_state():
    cases = [
        ("Flush", [("H", [0]), ("H", [1]), ("H", [2])]),
        ("Full House", [("H", [0]), ("X", [1])]),
        ("Phase Lock", [("H", [0]), ("H", [1]), ("Z", [0]), ("Z", [1])]),
        ("Rotation Trio", [("RX", [0]), ("RY", [1]), ("RZ", [2])]),
        ("Swap Network", [("H", [0]), ("CNOT", [0, 1]), ("SWAP", [1, 2])]),
        ("Toffoli Cascade", [("X", [0]), ("X", [1]), ("CCX", [0, 1, 2])]),
    ]

    for expected_hand, operations in cases:
        game = GameState(backend=QuantumBackend(3))
        game.blind_event = {"id": "NONE", "name": "None", "desc": ""}
        game.hand = [Card(gate, gate) for gate, _ in operations]
        preview = game.preview_hand(
            list(range(len(operations))),
            [targets for _, targets in operations],
        )

        assert preview["valid"] is True
        assert preview["hand"].startswith(expected_hand)
        assert preview["fidelity"] == 1.0


def test_redundant_h_gates_do_not_fake_uniform_flush():
    game = GameState(backend=QuantumBackend(3))
    game.hand = [Card("H1", "H"), Card("H2", "H")]

    preview = game.preview_hand([0, 1], [[0], [0]])

    assert not preview["hand"].startswith("Flush")


def test_circuit_score_prefers_clean_match_over_noop_and_cancelled_gates():
    target = {"00": 1.0}
    empty = calculate_score_details(get_quantum_probs([]), target, [], set(), circuit_depth=0)
    noop_cnot = calculate_score_details(
        get_quantum_probs([("CNOT", 0)]),
        target,
        [("CNOT", 0)],
        set(),
        circuit_depth=1,
    )
    cancelled_h = calculate_score_details(
        get_quantum_probs([("H", 0), ("H", 0)]),
        target,
        [("H", 0), ("H", 0)],
        set(),
        circuit_depth=2,
    )

    score = lambda details: details["chips"] * details["mult"]
    assert empty["match_quality"] == noop_cnot["match_quality"] == cancelled_h["match_quality"] == 1.0
    assert score(empty) > score(noop_cnot) > score(cancelled_h)


def test_card_score_penalizes_noop_gate_and_redundant_depth():
    noop_game = GameState(backend=QuantumBackend(3))
    noop_game.blind_event = {"id": "NONE", "name": "None", "desc": ""}
    noop_game.hand = [Card("CNOT", "CNOT")]
    noop_preview = noop_game.preview_hand([0], [[0, 1]], slot_indices=[0])

    parallel_game = GameState(backend=QuantumBackend(3))
    parallel_game.blind_event = {"id": "NONE", "name": "None", "desc": ""}
    parallel_game.hand = [Card("H", "H"), Card("X", "X")]
    parallel_preview = parallel_game.preview_hand([0, 1], [[0], [1]], slot_indices=[0, 0])
    sequential_preview = parallel_game.preview_hand([0, 1], [[0], [1]], slot_indices=[0, 1])

    assert noop_preview["ineffective_gates"] == 1
    assert noop_preview["depth_efficiency"] < 1.0
    assert parallel_preview["depth_efficiency"] == 1.0
    assert sequential_preview["depth_efficiency"] < 1.0
    assert parallel_preview["score"] > sequential_preview["score"]


def test_fidelity_is_squared_in_card_score():
    game = GameState(backend=QuantumBackend(3))
    full_score, full_details = game._score_quantum_hand(100, 10, 1.0, "High Qubit", [], 0, 0)
    half_score, half_details = game._score_quantum_hand(100, 10, 0.5, "High Qubit", [], 0, 0)

    assert full_details["fidelity_weight"] == 1.0
    assert half_details["fidelity_weight"] == 0.25
    assert full_score == half_score * 4


def test_live_preview_score_matches_committed_score_with_depth_rules():
    game = GameState(backend=QuantumBackend(3))
    game.blind_event = {"id": "NONE", "name": "None", "desc": ""}
    game.hand = [Card("H", "H"), Card("CNOT", "CNOT")]

    preview = game.preview_hand([0, 1], [[0], [0, 1]], slot_indices=[0, 1])
    success = game.play_hand([0, 1], [[0], [0, 1]], slot_indices=[0, 1])

    assert success is True
    assert preview["score"] == game.last_score_breakdown["score"]
    assert preview["depth_efficiency"] == game.last_score_breakdown["depth_efficiency"]
    assert preview["fidelity_weight"] == game.last_score_breakdown["fidelity_weight"]


def test_cat_joker_is_not_free_and_uses_half_mult_per_remaining_play():
    from backend.api.game_routes import games_instances, start_game

    start_game("game2")
    game = games_instances["active"]["instance"]
    assert game.jokers == []

    cat = SchrodingerCatJoker()
    chips, mult = cat.on_calculate_score(10, 2, game)
    assert chips == 10
    assert mult == 2 + game.plays_left * 0.5


def test_each_committed_hand_resets_hidden_quantum_state():
    game = GameState(backend=QuantumBackend(3))
    game.blind_event = {"id": "NONE", "name": "None", "desc": ""}
    game.target_score = 10_000
    game.hand = [Card("H", "H"), Card("CNOT", "CNOT")]

    assert game.play_hand([0, 1], [[0], [0, 1]], slot_indices=[0, 1]) is True
    probabilities = game.backend.get_amplitudes()

    assert probabilities[0] == 1.0
    assert sum(probabilities[1:]) == 0.0


def test_circuit_discard_redraws_cards():
    game = CircuitGameSession()
    original_ids = [card["id"] for card in game.hand]
    discarded_ids = original_ids[:2]

    success = game.discard_hand(discarded_ids)

    assert success is True
    assert game.discards_left == game.max_discards - 1
    assert len(game.hand) == 5
    assert not set(discarded_ids) & {card["id"] for card in game.hand}
    assert set(discarded_ids) <= {card["id"] for card in game.discard_pile}
