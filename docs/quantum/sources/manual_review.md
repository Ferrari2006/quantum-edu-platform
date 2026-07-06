---
title: "Manual Review Checklist"
doc_type: "source-registry"
topic: "knowledge-base"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "internal-note"
source_url: null
tags: ["manual-review", "license", "terms"]
updated: "2026-07-06"
---

# Manual Review Checklist

These are the places where a human should check terms, licenses, and attribution before expanding beyond the current conservative first-batch decisions.

## Please Review First

1. arXiv API terms and attribution guidance
   - URL: `https://info.arxiv.org/help/api/index.html`
   - Current decision: `approved_api_metadata`.
   - Confirm before expansion: rate limits, attribution text, API terms, and article-level license before any full-text PDF use.

2. IBM Quantum / Qiskit documentation terms
   - URL: `https://docs.quantum.ibm.com/`
   - Current decision: `approved_local_copy`.
   - Confirm before import: prefer official documentation repository or clearly licensed source; keep attribution, source URL, license, and version.

3. PennyLane documentation terms
   - URL: `https://docs.pennylane.ai/`
   - Current decision: `approved_local_copy`.
   - Confirm before import: docs license, demo/code sample license, source URL, version, and attribution.

4. QuTiP documentation license
   - URL: `https://qutip.readthedocs.io/en/latest/`
   - Current decision: `approved_local_copy`.
   - Confirm before import: docs license, attribution requirement, docs version, and separate handling for text/code samples.

5. Microsoft Learn / Azure Quantum terms
   - URL: `https://learn.microsoft.com/en-us/azure/quantum/`
   - Current decision: `approved_local_copy`.
   - Confirm before import: use MicrosoftDocs/Learn sources with explicit license; avoid unclear webpages, images, and trademark materials.

6. Google Quantum AI / Cirq documentation terms
   - URL: `https://quantumai.google/cirq`
   - Current decision: `approved_local_copy`.
   - Confirm before import: content license, code sample license, source URL, version, and attribution.

7. OpenQASM specification license
   - URL: `https://openqasm.com/`
   - Current decision: `approved_local_copy`.
   - Confirm before import: specification license, source URL, version, and citation requirements.

8. MIT OpenCourseWare license for the selected course
   - URL: `https://ocw.mit.edu/`
   - Current decision: `approved_summary_only`.
   - Confirm before expansion: noncommercial education/research use, attribution format, noncommercial/share-alike requirements, and whether local copies are allowed.

9. npj Quantum Information article licenses
   - URL: `https://www.nature.com/npjqi/`
   - Current decision: `link_only` or `approved_summary_only`.
   - Confirm per article: local copy only if clearly allowed, such as CC BY. Do not copy or transform full text for CC BY-NC-ND articles.

## Import Decision Labels

Use one of these labels in source notes:

- `approved_api_metadata`: Safe to import metadata through API.
- `approved_summary_only`: Use source to write our own summary, do not mirror full text.
- `approved_local_copy`: Content license allows local corpus copy with attribution.
- `link_only`: Store metadata and source URL only.
- `blocked`: Do not import.
