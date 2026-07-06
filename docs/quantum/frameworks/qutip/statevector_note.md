---
title: "QuTiP State Vector Note"
doc_type: "framework"
topic: "statevector"
framework: "qutip"
algorithm: null
difficulty: "beginner"
version: "version-specific"
source: "internal-note"
source_url: null
tags: ["qutip", "statevector", "basis"]
updated: "2026-07-06"
---

# QuTiP State Vector Note

## Version Assumptions

This note is a placeholder for QuTiP examples. Verify the installed QuTiP version before giving API-specific answers.

## Typical Idea

QuTiP represents quantum states and operators with `Qobj`.

```python
from qutip import basis

zero = basis(2, 0)
one = basis(2, 1)
plus = (zero + one).unit()
print(plus)
```

## RAG Notes

QuTiP is often used for open quantum systems and dynamics, so route Lindblad/master-equation questions to QuTiP-specific notes when available.
