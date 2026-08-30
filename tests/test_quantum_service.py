import math
import unittest

from backend.quantum.service import (
    QuantumCircuitValidationError,
    calculate_fidelity,
    execute_circuit,
)


class QuantumServiceTests(unittest.TestCase):
    def test_hadamard_creates_equal_probability_distribution(self):
        result = execute_circuit(1, [{"gate": "H", "targets": [0]}])

        self.assertAlmostEqual(result["probabilities"]["0"], 0.5)
        self.assertAlmostEqual(result["probabilities"]["1"], 0.5)
        self.assertEqual(result["metrics"]["operation_count"], 1)
        self.assertIn("qc.h(0)", result["qiskit_code"])

    def test_bell_circuit_returns_correlated_states(self):
        result = execute_circuit(
            2,
            [
                {"gate": "H", "targets": [0]},
                {"gate": "CX", "targets": [0, 1]},
            ],
        )

        self.assertAlmostEqual(result["probabilities"]["00"], 0.5)
        self.assertAlmostEqual(result["probabilities"]["11"], 0.5)
        self.assertAlmostEqual(result["probabilities"]["01"], 0.0)
        self.assertAlmostEqual(result["probabilities"]["10"], 0.0)

    def test_rotation_requires_theta(self):
        with self.assertRaises(QuantumCircuitValidationError):
            execute_circuit(1, [{"gate": "RY", "targets": [0]}])

    def test_multi_qubit_gate_rejects_duplicate_or_missing_targets(self):
        with self.assertRaises(QuantumCircuitValidationError):
            execute_circuit(2, [{"gate": "CX", "targets": [0]}])
        with self.assertRaises(QuantumCircuitValidationError):
            execute_circuit(2, [{"gate": "CX", "targets": [0, 0]}])

    def test_statevector_fidelity_accepts_complex_objects(self):
        amplitude = 1 / math.sqrt(2)
        result = calculate_fidelity(
            2,
            [
                {"gate": "H", "targets": [0]},
                {"gate": "CX", "targets": [0, 1]},
            ],
            target_statevector=[
                {"real": amplitude, "imag": 0},
                0,
                0,
                {"real": amplitude, "imag": 0},
            ],
        )

        self.assertAlmostEqual(result["fidelity"], 1.0)
        self.assertEqual(result["fidelity_kind"], "statevector")

    def test_probability_fidelity_is_labeled_separately(self):
        result = calculate_fidelity(
            1,
            [{"gate": "H", "targets": [0]}],
            target_probabilities={"0": 0.5, "1": 0.5},
        )

        self.assertAlmostEqual(result["fidelity"], 1.0)
        self.assertEqual(result["fidelity_kind"], "probability")


if __name__ == "__main__":
    unittest.main()
