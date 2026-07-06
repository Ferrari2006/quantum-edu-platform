---
title: "Initial Import Plan"
doc_type: "source-registry"
topic: "knowledge-base"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "internal-note"
source_url: null
tags: ["import-plan", "mvp", "rag"]
updated: "2026-07-06"
---

# Initial Import Plan

## Phase 1: Metadata and Summaries

Do first:

- arXiv metadata and abstracts for classic quantum algorithms and recent educational material.
- OpenAlex metadata for DOI, venue, authors, citation graph, and open-access status.
- Semantic Scholar metadata, abstracts when permitted, citations, and recommendations.
- Internal summaries written from approved sources with attribution and source URLs.

Avoid at this phase:

- Downloading or locally storing full-text PDFs by default.
- Crawling entire official documentation sites.
- Importing unreviewed blogs or forum answers.
- Mirroring course materials or journal full text.

## Phase 2: Framework Documentation Seeds

Start with small, focused framework pages:

- Qiskit: circuits, measurement, statevector, transpilation basics.
- PennyLane: QNode, devices, measurements, VQE demo.
- QuTiP: `Qobj`, basis states, operators, `mesolve`.
- Q#: intro syntax, operations, Azure Quantum job flow.
- Cirq: circuits, simulators, measurements, noise basics.

Rules:

- Prefer official documentation repositories or clearly licensed documentation sources.
- Preserve attribution, source URL, license, docs version, framework version, and retrieval date.
- Store documentation text and code sample license metadata separately when the source distinguishes them.
- Do not mirror whole websites, images, trademarks, or unclear-license resources.

## Phase 3: Courseware

Current decision:

- MIT OCW course materials are `approved_summary_only`.
- Do not mirror full course materials in the first batch.

After future noncommercial/attribution/share-alike review:

- Build course module summaries.
- Keep lecture URL and attribution.
- Convert exercises into original RAG-friendly notes where allowed.

## Phase 3b: Journals and Open Access Articles

Current decision:

- npj Quantum Information articles are `link_only` or `approved_summary_only` by default.
- Check article licenses one by one.
- Only clearly reusable CC BY articles may be considered for local copy.
- Do not locally copy or perform derivative full-text processing on CC BY-NC-ND articles.

## Phase 4: Evaluation Set

For each imported topic, add QA cases:

- One conceptual question.
- One formula/derivation question.
- One code question when relevant.
- One "context insufficient" negative question.
