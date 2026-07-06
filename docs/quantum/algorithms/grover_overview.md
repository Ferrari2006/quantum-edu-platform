---
title: "Grover Search Overview"
doc_type: "algorithm"
topic: "search"
framework: null
algorithm: "grover"
difficulty: "intermediate"
version: null
source: "course-note"
source_url: null
tags: ["grover", "amplitude-amplification", "oracle", "diffusion"]
updated: "2026-07-06"
---

# Grover Search Overview

## Problem

Grover search addresses unstructured search over `N` candidates when an oracle can mark target states.

## Core Idea

Grover's algorithm alternates two operations:

- Oracle phase marking of target states.
- Diffusion or inversion-about-the-mean to amplify marked amplitudes.

## Query Complexity

The ideal query complexity is:

```latex
O(\sqrt{N})
```

compared with classical unstructured search complexity `O(N)`.

## RAG Notes

Do not describe Grover as a general database lookup speedup without explaining the oracle model.
