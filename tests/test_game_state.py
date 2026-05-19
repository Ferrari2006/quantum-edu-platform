import pytest

from games.game2.quantum_balatro_original.game_state import GameState


class MockBackend:
    def __init__(self, num_qubits=3):
        self.num_qubits = num_qubits
        self.applied = []

    def reset_circuit(self):
        self.applied.clear()

    def upgrade_qubits(self, n):
        self.num_qubits = n

    def apply_gate(self, gate_type, targets, theta=None):
        # 简单记录调用
        if any(t < 0 or t >= self.num_qubits for t in targets):
            raise ValueError("target out of range")
        self.applied.append((gate_type, tuple(targets), theta))

    def calculate_fidelity(self, target_state):
        return 1.0

    def get_amplitudes(self):
        return [1.0] + [0.0] * (2 ** self.num_qubits - 1)

    def get_statevector(self):
        return None


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
