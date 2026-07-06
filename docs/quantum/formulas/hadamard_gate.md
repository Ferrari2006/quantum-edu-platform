---
title: "Hadamard Gate Matrix and Action"
doc_type: "formula"
topic: "gate"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "course-note"
source_url: null
tags: ["hadamard", "matrix", "superposition"]
updated: "2026-07-06"
---

# Hadamard Gate Matrix and Action

## Matrix

```latex
H = \frac{1}{\sqrt{2}}
\begin{bmatrix}
1 & 1 \\
1 & -1
\end{bmatrix}
```

## Action on Basis States

```latex
H|0\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}
```

```latex
H|1\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}
```

## Notes for RAG

Questions about "creating superposition" often retrieve this document, but the answer should mention that `H` is basis-dependent and is not the only way to create superposition.
