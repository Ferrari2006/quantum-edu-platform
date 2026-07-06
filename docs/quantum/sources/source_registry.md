---
title: "Quantum RAG Source Registry"
doc_type: "source-registry"
topic: "knowledge-base"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "internal-note"
source_url: null
tags: ["sources", "crawl-plan", "quantum"]
updated: "2026-07-06"
---

# Quantum RAG Source Registry

## Literature and Paper Discovery

| Source | URL | Method | Target path | Notes |
| --- | --- | --- | --- | --- |
| arXiv | `https://arxiv.org/` | API | `papers/arxiv/` | Use API for metadata and abstracts. Focus on `quant-ph` first. |
| OpenAlex | `https://openalex.org/` | API | `papers/openalex/` | Use for DOI, citation graph, OA status, authors, venues. |
| Semantic Scholar | `https://www.semanticscholar.org/` | API | `papers/semantic_scholar/` | Use for recommendations, citations, abstracts when permitted. |
| npj Quantum Information | `https://www.nature.com/npjqi/` | Manual/API when available | `papers/npj_quantum_information/` | Link-only or summary-only by default. Check license per article before any local full-text copy. |

## Framework Documentation

| Source | URL | Method | Target path | Notes |
| --- | --- | --- | --- | --- |
| IBM Quantum / Qiskit Docs | `https://docs.quantum.ibm.com/` | Licensed docs source, focused import | `frameworks/qiskit/` | Prefer official docs repository or clearly licensed source. Capture attribution, source URL, license, and version. Do not mirror the whole site. |
| PennyLane Docs | `https://docs.pennylane.ai/` | Licensed docs source, focused import | `frameworks/pennylane/` | Capture source URL, license, version, attribution, and demo/code metadata. |
| QuTiP Docs | `https://qutip.readthedocs.io/en/latest/` | Licensed docs source, focused import | `frameworks/qutip/` | Capture docs version. Track text and code sample license separately. |
| Microsoft Quantum / Q# Docs | `https://learn.microsoft.com/en-us/azure/quantum/` | Licensed docs source, focused import | `frameworks/qsharp/` | Prefer MicrosoftDocs/Learn sources with explicit license. Avoid unclear web assets, images, and trademark materials. |
| Google Quantum AI / Cirq Docs | `https://quantumai.google/cirq` | Licensed docs source, focused import | `frameworks/cirq/` | Capture attribution, source URL, license, version. Track code and text licenses separately. |

## Standards and Courseware

| Source | URL | Method | Target path | Notes |
| --- | --- | --- | --- | --- |
| OpenQASM Specification | `https://openqasm.com/` | Licensed specification source, focused import | `standards/openqasm/` | Store grammar, gates, measurement, classical control separately with license and version metadata. |
| MIT OCW Quantum Computation | `https://ocw.mit.edu/` | Summary-only | `courses/mit_ocw/` | Do not mirror full course materials in the first batch. Keep attribution and source URLs for summaries. |

## First-Batch Boundaries

- Use paper APIs for metadata and abstracts only.
- Do not default to downloading or storing PDFs.
- Do not mirror entire documentation sites.
- Do not copy course full text.
- Do not copy journal full text unless article-level license explicitly permits it.
- Keep license, attribution, source URL, version, and retrieval date in every imported document.

## Excluded by Default

| Source type | Reason |
| --- | --- |
| Google Scholar pages | No stable public API and scraping risk. |
| Paywalled publisher full text | Copyright and access restrictions. |
| Pirated textbooks or mirrors | Copyright risk. |
| Random blogs/forums | Quality and attribution issues unless manually reviewed. |
