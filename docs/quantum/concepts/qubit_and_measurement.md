---
title: "Qubits and Measurement"
doc_type: "concept"
topic: "qubit"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "course-note"
source_url: null
tags: ["qubit", "measurement", "born-rule", "statevector"]
updated: "2026-07-06"
---

# Qubits and Measurement

## Definition

A single qubit pure state is written as:

```latex
|\psi\rangle = \alpha |0\rangle + \beta |1\rangle
```

where `alpha` and `beta` are complex amplitudes and:

```latex
|\alpha|^2 + |\beta|^2 = 1
```

## Measurement Rule

Measuring this qubit in the computational basis gives:

```latex
P(0) = |\alpha|^2,\quad P(1) = |\beta|^2
```

After measurement, the state collapses to the observed basis state in this measurement model.

## Learning Notes

- Amplitudes are not probabilities; squared magnitudes are probabilities.
- A global phase does not change measurement probabilities.
- Measurement basis matters. Measuring in the computational basis is only one possible measurement.

## Common Questions

- Why can amplitudes be complex?
- Why does global phase not affect measurement?
- How is measurement represented in a circuit simulator?
