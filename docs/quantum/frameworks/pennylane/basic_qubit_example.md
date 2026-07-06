---
title: "PennyLane Basic Qubit Example"
doc_type: "framework"
topic: "qubit"
framework: "pennylane"
algorithm: null
difficulty: "beginner"
version: "version-specific"
source: "internal-note"
source_url: null
tags: ["pennylane", "qubit", "hadamard", "expectation"]
updated: "2026-07-06"
---

# PennyLane Basic Qubit Example

## Version Assumptions

This note is a placeholder for PennyLane examples. Verify the installed PennyLane version before giving API-specific answers.

## Typical Task

Prepare a single-qubit superposition and measure an expectation value.

```python
import pennylane as qml

dev = qml.device("default.qubit", wires=1)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    return qml.expval(qml.PauliZ(0))

print(circuit())
```

## RAG Notes

Answers should mention the device, wires, and return type because these are common sources of beginner confusion.
