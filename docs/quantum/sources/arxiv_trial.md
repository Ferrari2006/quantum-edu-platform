---
title: "arXiv Metadata Trial"
doc_type: "source-registry"
topic: "paper-metadata"
framework: null
algorithm: null
difficulty: "beginner"
version: null
source: "internal-note"
source_url: "https://export.arxiv.org/api/query"
tags: ["arxiv", "trial", "metadata-only"]
updated: "2026-07-06"
---

# arXiv Metadata Trial

This is the first single-site trial for the quantum RAG source collectors.

## Policy

- Decision: `approved_api_metadata`
- Import metadata, abstracts, authors, arXiv IDs, DOI, and URLs.
- Do not download PDFs.
- Do not store full text by default.
- Check each article license before full-text use.

## Dry Run

```powershell
python scripts\collect_paper_metadata.py --provider arxiv --query "cat:quant-ph AND grover" --max-results 3 --dry-run
```

## Dry Run With Specific arXiv IDs

```powershell
python scripts\collect_paper_metadata.py --provider arxiv --arxiv-id "quant-ph/9605043" --dry-run
```

You can also collect a list:

```powershell
python scripts\collect_paper_metadata.py --provider arxiv --ids-file docs\quantum\sources\arxiv_seed_ids.txt --dry-run
```

## Write Markdown Records

```powershell
python scripts\collect_paper_metadata.py --provider arxiv --query "cat:quant-ph AND grover" --max-results 3
```

Or with specific IDs:

```powershell
python scripts\collect_paper_metadata.py --provider arxiv --ids-file docs\quantum\sources\arxiv_seed_ids.txt
```

Default output:

```text
docs/quantum/papers/arxiv/
```

## SSL Troubleshooting

If Windows Python cannot verify certificates:

```powershell
python -m pip install certifi
$env:SSL_CERT_FILE = (& python -c "import certifi; print(certifi.where())")
```

If your network uses a campus/company root certificate, export that certificate as a PEM file and pass:

```powershell
python scripts\collect_paper_metadata.py --provider arxiv --query "cat:quant-ph AND grover" --max-results 3 --dry-run --ca-bundle C:\path\to\root-ca.pem
```
