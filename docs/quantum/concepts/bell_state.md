---
title: "Bell State"
doc_type: "concept"
topic: "entanglement"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "course-note"
source_url: null
tags: ["bell-state", "entanglement", "hadamard", "cnot"]
updated: "2026-07-06"
---

# Bell State

## Definition

One common Bell state is:

```latex
|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}
```

This state is entangled because it cannot be written as a tensor product of two independent single-qubit states.

## Circuit Preparation

Starting from `|00>`, apply `H` to qubit 0 and then `CNOT` with qubit 0 as control and qubit 1 as target.

```text
q0: |0> -- H -- control --
q1: |0> ------- target  --
```

## Why It Is Entangled

The measurement outcomes are perfectly correlated in the computational basis: only `00` and `11` appear, each with probability `1/2`.

## Common Misconception

The Bell state is not simply "both qubits are either 0 or 1 before measurement." The quantum state encodes correlations that cannot be explained as two independent local states.
