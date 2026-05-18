from quantum_backend import QuantumBackend


def run():
    backend = QuantumBackend(num_qubits=3)
    backend.apply_gate("H", [0])
    backend.apply_gate("CNOT", [0, 1])
    backend.apply_gate("CNOT", [1, 2])
    target = backend.get_statevector()
    backend.inject_noise(intensity=0.05)
    fidelity = backend.calculate_fidelity(target)
    return {"fidelity": float(fidelity), "probs_len": int(len(backend.get_amplitudes()))}


if __name__ == "__main__":
    print(run())
