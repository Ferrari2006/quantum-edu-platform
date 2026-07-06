---
title: "Source Review Status"
doc_type: "source-registry"
topic: "knowledge-base"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "internal-note"
source_url: null
tags: ["source-status", "license", "approval"]
updated: "2026-07-06"
---

# Source Review Status

| Source | Status | Decision | Notes |
| --- | --- | --- | --- |
| arXiv | `approved` | `approved_api_metadata` | Use arXiv API/OpenAlex/Semantic Scholar for metadata, abstracts, authors, arXiv IDs, DOI, and URLs. Do not download or locally store PDFs by default. Check article license before full-text use. |
| OpenAlex | `approved` | `approved_api_metadata` | Use for paper metadata, DOI, authors, venues, citation graph, open-access status, and source URLs. Do not treat metadata as full-text permission. |
| Semantic Scholar | `approved` | `approved_api_metadata` | Use for metadata, abstracts when permitted, citations, and recommendations. Do not store full-text PDFs by default. |
| IBM Quantum / Qiskit Docs | `approved` | `approved_local_copy` | Prefer official documentation repository or clearly licensed documentation source. Keep attribution, source URL, license, and version. Do not blindly mirror the whole website. |
| PennyLane Docs | `approved` | `approved_local_copy` | Keep source URL, license, version, and attribution for docs and demos. |
| QuTiP Docs | `approved` | `approved_local_copy` | Keep source URL, docs version, attribution, and license. Track documentation text and code sample licenses separately. |
| Microsoft Quantum / Q# Docs | `approved` | `approved_local_copy` | Prefer MicrosoftDocs/Learn sources with explicit license. Keep attribution, source URL, license, and version. Do not mirror unclear web assets, images, or trademark materials. |
| Google Quantum AI / Cirq Docs | `approved` | `approved_local_copy` | Keep attribution, source URL, license, and version. Track documentation text and code sample licenses separately. |
| OpenQASM Specification | `approved` | `approved_local_copy` | Keep source URL, license, and specification version. |
| MIT OCW Quantum Computation | `approved` | `approved_summary_only` | Do not mirror full course materials for now. If future use is confirmed as noncommercial education/research and attribution + noncommercial + share-alike can be satisfied, reconsider local copy. |
| npj Quantum Information | `approved` | `link_only` or `approved_summary_only` | Do not copy full text by default. Check each article license individually. Only clear CC BY articles may be considered for local copy; CC BY-NC-ND should not be copied or used for derivative full-text processing. |

## First-Batch Corpus Strategy

The first batch should prioritize:

- arXiv/OpenAlex/Semantic Scholar metadata and abstracts.
- Official technical documentation with clear reuse terms: Qiskit, PennyLane, QuTiP, Cirq, OpenQASM.
- Internally written summaries with source URLs and attribution.

The first batch should avoid:

- Large-scale paper full-text crawling.
- Course full-text mirroring.
- Whole-site mirroring of documentation websites.
- Copying images, trademark materials, or unclear-license assets.

## Status Values

- `needs_review`: Human review required before import.
- `approved`: Content may be imported according to the decision label.
- `blocked`: Do not import.
- `deferred`: Review later.

## Decision Labels

- `approved_api_metadata`
- `approved_summary_only`
- `approved_local_copy`
- `link_only`
- `blocked`
