from __future__ import annotations

import math
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, partial_trace, state_fidelity


class QuantumCircuitValidationError(ValueError):
    pass


GATE_SPECS: dict[str, tuple[int, bool]] = {
    "H": (1, False),
    "X": (1, False),
    "Y": (1, False),
    "Z": (1, False),
    "S": (1, False),
    "SDG": (1, False),
    "T": (1, False),
    "TDG": (1, False),
    "RX": (1, True),
    "RY": (1, True),
    "RZ": (1, True),
    "CX": (2, False),
    "CNOT": (2, False),
    "CZ": (2, False),
    "SWAP": (2, False),
    "CCX": (3, False),
    "TOFFOLI": (3, False),
}


def _operation_dict(operation: Any) -> dict[str, Any]:
    if isinstance(operation, dict):
        return operation
    if hasattr(operation, "model_dump"):
        return operation.model_dump()
    return {
        "gate": getattr(operation, "gate", ""),
        "targets": getattr(operation, "targets", []),
        "theta": getattr(operation, "theta", None),
    }


def _validated_operation(
    operation: Any,
    num_qubits: int,
    index: int,
) -> tuple[str, list[int], float | None]:
    item = _operation_dict(operation)
    gate = str(item.get("gate", "")).strip().upper()
    targets = item.get("targets", [])
    theta = item.get("theta")

    if gate not in GATE_SPECS:
        raise QuantumCircuitValidationError(
            f"operation {index}: unsupported gate '{gate or item.get('gate', '')}'"
        )
    if not isinstance(targets, list) or any(not isinstance(value, int) for value in targets):
        raise QuantumCircuitValidationError(
            f"operation {index}: targets must be a list of integer qubit indices"
        )

    expected_arity, needs_theta = GATE_SPECS[gate]
    if len(targets) != expected_arity:
        raise QuantumCircuitValidationError(
            f"operation {index}: gate {gate} requires {expected_arity} target(s)"
        )
    if len(set(targets)) != len(targets):
        raise QuantumCircuitValidationError(
            f"operation {index}: a multi-qubit gate requires distinct targets"
        )
    if any(value < 0 or value >= num_qubits for value in targets):
        raise QuantumCircuitValidationError(
            f"operation {index}: target index out of range for {num_qubits} qubits"
        )
    if needs_theta:
        if not isinstance(theta, (int, float)) or not math.isfinite(float(theta)):
            raise QuantumCircuitValidationError(
                f"operation {index}: gate {gate} requires a finite theta value"
            )
        theta = float(theta)
    else:
        theta = None
    return gate, targets, theta


def build_circuit(num_qubits: int, operations: list[Any]) -> QuantumCircuit:
    if not isinstance(num_qubits, int) or not 1 <= num_qubits <= 5:
        raise QuantumCircuitValidationError("num_qubits must be between 1 and 5")
    if len(operations) > 40:
        raise QuantumCircuitValidationError("a circuit may contain at most 40 operations")

    circuit = QuantumCircuit(num_qubits)
    for index, operation in enumerate(operations, start=1):
        gate, targets, theta = _validated_operation(operation, num_qubits, index)
        if gate == "H":
            circuit.h(targets[0])
        elif gate == "X":
            circuit.x(targets[0])
        elif gate == "Y":
            circuit.y(targets[0])
        elif gate == "Z":
            circuit.z(targets[0])
        elif gate == "S":
            circuit.s(targets[0])
        elif gate == "SDG":
            circuit.sdg(targets[0])
        elif gate == "T":
            circuit.t(targets[0])
        elif gate == "TDG":
            circuit.tdg(targets[0])
        elif gate == "RX":
            circuit.rx(theta, targets[0])
        elif gate == "RY":
            circuit.ry(theta, targets[0])
        elif gate == "RZ":
            circuit.rz(theta, targets[0])
        elif gate in {"CX", "CNOT"}:
            circuit.cx(targets[0], targets[1])
        elif gate == "CZ":
            circuit.cz(targets[0], targets[1])
        elif gate == "SWAP":
            circuit.swap(targets[0], targets[1])
        elif gate in {"CCX", "TOFFOLI"}:
            circuit.ccx(targets[0], targets[1], targets[2])
    return circuit


def _state_payload(state: Statevector, num_qubits: int) -> dict[str, Any]:
    raw_probabilities = state.probabilities_dict()
    probabilities = {
        format(index, f"0{num_qubits}b"): round(
            float(raw_probabilities.get(format(index, f"0{num_qubits}b"), 0.0)),
            10,
        )
        for index in range(2**num_qubits)
    }
    amplitudes = [
        {"real": round(float(value.real), 10), "imag": round(float(value.imag), 10)}
        for value in state.data
    ]
    return {"probabilities": probabilities, "amplitudes": amplitudes}


def _bloch_vectors(state: Statevector, num_qubits: int) -> list[dict[str, float | int]]:
    pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
    pauli_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    pauli_z = np.array([[1, 0], [0, -1]], dtype=complex)
    vectors: list[dict[str, float | int]] = []
    for qubit in range(num_qubits):
        traced_out = [index for index in range(num_qubits) if index != qubit]
        density = partial_trace(state, traced_out).data if traced_out else state.to_operator().data
        if not traced_out:
            vector = state.data.reshape((-1, 1))
            density = vector @ vector.conjugate().T
        vectors.append(
            {
                "qubit": qubit,
                "x": round(float(np.trace(density @ pauli_x).real), 8),
                "y": round(float(np.trace(density @ pauli_y).real), 8),
                "z": round(float(np.trace(density @ pauli_z).real), 8),
            }
        )
    return vectors


def generate_qiskit_code(num_qubits: int, operations: list[Any]) -> str:
    lines = [
        "from qiskit import QuantumCircuit",
        "from qiskit.quantum_info import Statevector",
        "",
        f"qc = QuantumCircuit({num_qubits})",
    ]
    method_names = {"CNOT": "cx", "TOFFOLI": "ccx"}
    for index, operation in enumerate(operations, start=1):
        gate, targets, theta = _validated_operation(operation, num_qubits, index)
        method = method_names.get(gate, gate.lower())
        arguments: list[str] = []
        if theta is not None:
            arguments.append(repr(round(theta, 10)))
        arguments.extend(str(target) for target in targets)
        lines.append(f"qc.{method}({', '.join(arguments)})")
    lines.extend(
        [
            "",
            "state = Statevector.from_instruction(qc)",
            "print(state.probabilities_dict())",
        ]
    )
    return "\n".join(lines)


def execute_circuit(num_qubits: int, operations: list[Any]) -> dict[str, Any]:
    circuit = build_circuit(num_qubits, operations)
    state = Statevector.from_instruction(circuit)
    return {
        "num_qubits": num_qubits,
        "operations": [_operation_dict(operation) for operation in operations],
        **_state_payload(state, num_qubits),
        "bloch_vectors": _bloch_vectors(state, num_qubits),
        "metrics": {
            "depth": circuit.depth(),
            "size": circuit.size(),
            "operation_count": len(operations),
        },
        "diagram": str(circuit.draw(output="text")),
        "qiskit_code": generate_qiskit_code(num_qubits, operations),
        "execution": "statevector_simulation",
    }


def _parse_complex_amplitude(value: Any, index: int) -> complex:
    if isinstance(value, (int, float)):
        return complex(float(value), 0.0)
    if isinstance(value, dict):
        real = value.get("real", 0.0)
        imag = value.get("imag", 0.0)
        if isinstance(real, (int, float)) and isinstance(imag, (int, float)):
            return complex(float(real), float(imag))
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(isinstance(item, (int, float)) for item in value)
    ):
        return complex(float(value[0]), float(value[1]))
    raise QuantumCircuitValidationError(
        f"target_statevector[{index}] must be a number, [real, imag], or real/imag object"
    )


def calculate_fidelity(
    num_qubits: int,
    operations: list[Any],
    *,
    target_statevector: list[Any] | None = None,
    target_basis_state: str | None = None,
    target_probabilities: dict[str, float] | None = None,
) -> dict[str, Any]:
    circuit = build_circuit(num_qubits, operations)
    state = Statevector.from_instruction(circuit)
    current = _state_payload(state, num_qubits)

    if target_basis_state is not None:
        if (
            len(target_basis_state) != num_qubits
            or any(value not in "01" for value in target_basis_state)
        ):
            raise QuantumCircuitValidationError(
                "target_basis_state must be a bit string matching num_qubits"
            )
        target = Statevector.from_label(target_basis_state)
        fidelity = float(state_fidelity(state, target))
        kind = "statevector"
    elif target_statevector:
        expected_length = 2**num_qubits
        if len(target_statevector) != expected_length:
            raise QuantumCircuitValidationError(
                f"target_statevector must contain {expected_length} amplitudes"
            )
        amplitudes = np.array(
            [
                _parse_complex_amplitude(value, index)
                for index, value in enumerate(target_statevector)
            ],
            dtype=complex,
        )
        norm = float(np.linalg.norm(amplitudes))
        if not math.isfinite(norm) or norm <= 0:
            raise QuantumCircuitValidationError("target_statevector must have a non-zero norm")
        target = Statevector(amplitudes / norm)
        fidelity = float(state_fidelity(state, target))
        kind = "statevector"
    elif target_probabilities:
        normalized_target: dict[str, float] = {}
        for basis, probability in target_probabilities.items():
            if len(basis) != num_qubits or any(value not in "01" for value in basis):
                raise QuantumCircuitValidationError(
                    "target probability keys must be bit strings matching num_qubits"
                )
            if not isinstance(probability, (int, float)) or probability < 0:
                raise QuantumCircuitValidationError(
                    "target probabilities must be non-negative numbers"
                )
            normalized_target[basis] = float(probability)
        total = sum(normalized_target.values())
        if total <= 0:
            raise QuantumCircuitValidationError("target probabilities must sum to more than zero")
        normalized_target = {
            basis: probability / total for basis, probability in normalized_target.items()
        }
        overlap = sum(
            math.sqrt(probability * current["probabilities"].get(basis, 0.0))
            for basis, probability in normalized_target.items()
        )
        fidelity = overlap**2
        kind = "probability"
    else:
        raise QuantumCircuitValidationError(
            "provide target_basis_state, target_statevector, or target_probabilities"
        )

    return {
        "num_qubits": num_qubits,
        "fidelity": round(max(0.0, min(fidelity, 1.0)), 10),
        "fidelity_kind": kind,
        "probabilities": current["probabilities"],
        "qiskit_code": generate_qiskit_code(num_qubits, operations),
    }
