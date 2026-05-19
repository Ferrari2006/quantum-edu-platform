import pytest

from games.game2.quantum_balatro_original.quantum_backend import QuantumBackend


def test_apply_gate_invalid_targets_raises():
    backend = QuantumBackend(num_qubits=3)
    with pytest.raises(ValueError):
        backend.apply_gate('H', [-1])
    with pytest.raises(ValueError):
        backend.apply_gate('CNOT', [0, 10])


def test_inject_noise_clamps_intensity_and_runs():
    backend = QuantumBackend(num_qubits=3)
    # Should not raise even for out-of-range intensity
    backend.inject_noise(intensity=5.0)
    backend.inject_noise(intensity=-1.0)
