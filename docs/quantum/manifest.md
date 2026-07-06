---
title: "Quantum Knowledge Base Manifest"
doc_type: "manifest"
topic: "knowledge-base"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "internal-note"
source_url: null
tags: ["manifest", "metadata", "coverage"]
updated: "2026-07-06"
---

# Quantum Knowledge Base Manifest

## Current Coverage

| Area | Status | Seed documents |
| --- | --- | --- |
| Core concepts | Started | `concepts/qubit_and_measurement.md`, `concepts/bell_state.md` |
| Formulas | Started | `formulas/hadamard_gate.md` |
| Algorithms | Started | `algorithms/grover_overview.md` |
| Qiskit | Started | `frameworks/qiskit/bell_state_example.md` |
| PennyLane | Placeholder | `frameworks/pennylane/basic_qubit_example.md` |
| QuTiP | Placeholder | `frameworks/qutip/statevector_note.md` |
| Papers | Placeholder | `papers/README.md` |
| Courses | Started | `courses/intro_module.md` |
| Glossary | Started | `glossary/core_terms.md` |
| External sources | Started | `sources/source_registry.md`, `sources/import_plan.md`, `sources/manual_review.md` |

## Recommended Next Documents

Priority 1:

- `concepts/quantum_gates.md`
- `concepts/tensor_product.md`
- `concepts/phase_and_interference.md`
- `frameworks/qiskit/measurement_counts.md`
- `frameworks/qiskit/transpilation_basics.md`
- `sources/source_status.md`

Priority 2:

- `algorithms/qpe_overview.md`
- `algorithms/vqe_overview.md`
- `algorithms/qaoa_overview.md`
- `formulas/tensor_product_examples.md`
- `formulas/bloch_sphere.md`

Priority 3:

- `papers/grover_1996_summary.md`
- `papers/vqe_original_summary.md`
- `frameworks/pennylane/vqe_example.md`
- `frameworks/qutip/open_systems_intro.md`

## Quality Checklist

- Has YAML front matter.
- Has explicit topic and difficulty.
- Has framework/version metadata when code is included.
- Keeps formulas and code blocks intact.
- Includes source or source placeholder.
- Avoids unsupported claims.
