# Quantum Computing Knowledge Base

This directory is the source corpus for the quantum computing RAG system.

Documents should use Markdown with YAML front matter so the ingestion pipeline can preserve domain metadata.

## Directory Layout

```text
docs/quantum/
  concepts/        # Qubits, gates, measurement, entanglement, noise
  formulas/        # Derivations, matrices, Dirac notation, identities
  algorithms/      # Grover, QPE, VQE, QAOA, Shor, HHL
  frameworks/      # Qiskit, PennyLane, QuTiP, Q# notes and examples
  papers/          # Paper summaries and reading notes
  courses/         # Course modules, lesson plans, exercises
  glossary/        # Short canonical definitions
  templates/       # Authoring templates for new knowledge documents
```

## Metadata Standard

Every document should start with YAML front matter:

```yaml
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
tags: ["bell-state", "cnot", "hadamard"]
updated: "2026-07-06"
---
```

Recommended metadata dimensions:

- `title`: Human-readable title.
- `doc_type`: `concept`, `formula`, `algorithm`, `framework`, `paper`, `course`, `glossary`, `exercise`.
- `topic`: Domain topic, such as `qubit`, `gate`, `measurement`, `entanglement`, `noise`, `optimization`.
- `framework`: `qiskit`, `pennylane`, `qutip`, `qsharp`, or `null`.
- `algorithm`: `grover`, `qpe`, `vqe`, `qaoa`, `shor`, `hhl`, or `null`.
- `difficulty`: `beginner`, `intermediate`, `advanced`.
- `version`: Framework or document version when relevant.
- `source`: `course-note`, `official-doc`, `paper`, `book`, `internal-note`.
- `source_url`: Original source URL when available.
- `tags`: Search/filter tags.
- `updated`: Last content update date in `YYYY-MM-DD`.

## Authoring Rules

- Keep equations in fenced LaTeX blocks or standalone display math.
- Keep code examples in fenced code blocks with language labels.
- Do not split a theorem, derivation, circuit explanation, or code example across unrelated sections.
- For framework code, always state the framework and version assumptions.
- Prefer explicit source citations over unsupported explanation.
