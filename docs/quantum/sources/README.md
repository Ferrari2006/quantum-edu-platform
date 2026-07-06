---
title: "External Source Registry"
doc_type: "source-registry"
topic: "knowledge-base"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "internal-note"
source_url: null
tags: ["sources", "crawl", "license", "metadata"]
updated: "2026-07-06"
---

# External Source Registry

This directory tracks approved external sources for the quantum computing RAG knowledge base.

The goal is to collect high-quality, attributable, version-aware material without mixing unsupported web content into the main corpus.

## Source Tiers

Tier 1:

- Official framework documentation.
- Open scholarly metadata APIs.
- Open courseware with clear license terms.
- Standards/specification sites.

Tier 2:

- Open access journals and review articles.
- Institution-hosted lecture notes.

Tier 3:

- Blogs, forum answers, personal notes, and secondary explanations.
- These should not enter the main corpus without manual review.

## Required Fields for Imported Documents

Every imported or generated document should keep:

- `title`
- `doc_type`
- `topic`
- `framework`
- `algorithm`
- `difficulty`
- `version`
- `source`
- `source_url`
- `license`
- `retrieved_at`
- `tags`

## Ingestion Policy

- Prefer APIs over HTML scraping when an API exists.
- Do not crawl paywalled or unclear-license full text.
- Keep source URLs and retrieval dates.
- For framework documentation, store the framework version or docs version.
- For papers, store DOI/arXiv ID, authors, year, abstract source, and open-access status.
- For first-batch paper sources, import metadata and abstracts only unless a specific article license has been reviewed.
- For first-batch course sources, write local summaries rather than mirroring full materials.
- For official technical docs, use focused imports from clearly licensed documentation sources, not whole-site mirrors.
