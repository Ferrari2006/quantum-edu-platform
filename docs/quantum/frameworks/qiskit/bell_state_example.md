---
title: "Qiskit Bell State Example"
doc_type: "framework"
topic: "entanglement"
framework: "qiskit"
algorithm: null
difficulty: "beginner"
version: "qiskit>=1.0"
source: "internal-note"
source_url: null
tags: ["qiskit", "bell-state", "statevector", "circuit"]
updated: "2026-07-06"
---

# Qiskit Bell State Example

## Version Assumptions

- Framework: Qiskit
- Version: `qiskit>=1.0`
- Simulator/state representation: `qiskit.quantum_info.Statevector`

## Code

```python
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

state = Statevector.from_instruction(qc)
print(state)
print(state.probabilities_dict())
```

## Expected Behavior

The circuit prepares:

```latex
\frac{|00\rangle + |11\rangle}{\sqrt{2}}
```

The probabilities dictionary should contain nonzero probabilities for `00` and `11`.

## Version Warning

When answering Qiskit questions, include the version assumption if the API may differ across releases.
