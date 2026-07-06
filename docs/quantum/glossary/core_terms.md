---
title: "Core Quantum Computing Glossary"
doc_type: "glossary"
topic: "core"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "internal-note"
source_url: null
tags: ["glossary", "qubit", "gate", "measurement"]
updated: "2026-07-06"
---

# Core Quantum Computing Glossary

## Qubit

A qubit is a two-level quantum system whose pure state can be written as a normalized linear combination of basis states:

```latex
|\psi\rangle = \alpha |0\rangle + \beta |1\rangle,\quad |\alpha|^2 + |\beta|^2 = 1
```

## Superposition

Superposition means a quantum state is expressed as a linear combination of basis states. It does not mean the system has a classical hidden value before measurement.

## Measurement

Measurement maps a quantum state to a classical outcome according to the Born rule. For a qubit in state `alpha|0> + beta|1>`, the probabilities are `|alpha|^2` for outcome `0` and `|beta|^2` for outcome `1`.

## Quantum Gate

A quantum gate is usually represented by a unitary matrix acting on one or more qubits.

## Entanglement

Entanglement is a property of multi-qubit states that cannot be written as a tensor product of independent single-qubit states.

## Circuit Depth

Circuit depth is the number of sequential gate layers after accounting for gates that can run in parallel.
