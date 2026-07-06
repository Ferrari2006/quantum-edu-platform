from __future__ import annotations

import argparse
import ssl
import socket
from pathlib import Path
import sys
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.rag.sources.arxiv import fetch_arxiv_metadata, fetch_arxiv_metadata_by_ids, normalize_arxiv_id
from backend.rag.sources.openalex import fetch_openalex_metadata
from backend.rag.sources.paper_metadata import write_paper_markdown
from backend.rag.sources.semantic_scholar import fetch_semantic_scholar_metadata


PROVIDERS = {
    "arxiv": (fetch_arxiv_metadata, ROOT / "docs" / "quantum" / "papers" / "arxiv"),
    "openalex": (fetch_openalex_metadata, ROOT / "docs" / "quantum" / "papers" / "openalex"),
    "semantic_scholar": (
        fetch_semantic_scholar_metadata,
        ROOT / "docs" / "quantum" / "papers" / "semantic_scholar",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect quantum paper metadata and abstracts only. This script never downloads PDFs."
    )
    parser.add_argument("--provider", choices=PROVIDERS.keys(), required=True)
    parser.add_argument("--query")
    parser.add_argument(
        "--arxiv-id",
        action="append",
        default=[],
        help="Specific arXiv ID or arXiv URL. Can be passed multiple times. arXiv provider only.",
    )
    parser.add_argument(
        "--ids-file",
        type=Path,
        help="Text file containing one arXiv ID or URL per line. Lines starting with # are ignored.",
    )
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--ca-bundle", help="Path to a custom CA bundle PEM file for HTTPS verification.")
    parser.add_argument("--timeout", type=int, default=30, help="Network timeout in seconds.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    fetcher, default_output = PROVIDERS[args.provider]
    arxiv_ids = collect_arxiv_ids(args.arxiv_id, args.ids_file)
    if args.provider != "arxiv" and arxiv_ids:
        print("--arxiv-id and --ids-file are only supported with --provider arxiv", file=sys.stderr)
        return 1
    if not args.query and not arxiv_ids:
        print("Provide --query, --arxiv-id, or --ids-file.", file=sys.stderr)
        return 1

    try:
        if args.provider == "arxiv" and arxiv_ids:
            papers = fetch_arxiv_metadata_by_ids(
                arxiv_ids,
                timeout=args.timeout,
                ca_bundle=args.ca_bundle,
            )
        else:
            papers = fetcher(
                args.query,
                max_results=args.max_results,
                timeout=args.timeout,
                ca_bundle=args.ca_bundle,
            )
    except ssl.SSLCertVerificationError as exc:
        print_ssl_help(exc)
        return 2
    except TimeoutError as exc:
        print_timeout_help(exc)
        return 4
    except socket.timeout as exc:
        print_timeout_help(exc)
        return 4
    except URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError):
            print_ssl_help(exc.reason)
            return 2
        if isinstance(exc.reason, TimeoutError | socket.timeout):
            print_timeout_help(exc.reason)
            return 4
        print(f"Network request failed: {exc}", file=sys.stderr)
        return 3

    if args.dry_run:
        for paper in papers:
            identifier = paper.arxiv_id or paper.doi or paper.source_url or "unknown"
            print(f"{paper.source}: {identifier} | {paper.title}")
        return 0

    output_dir = args.output_dir or default_output
    for paper in papers:
        path = write_paper_markdown(paper, output_dir)
        print(path)
    return 0


def print_ssl_help(exc: BaseException) -> None:
    print("HTTPS certificate verification failed.", file=sys.stderr)
    print(f"Details: {exc}", file=sys.stderr)
    print("", file=sys.stderr)
    print("This collector is metadata-only and does not download PDFs, but it still needs HTTPS.", file=sys.stderr)
    print("Try one of these fixes:", file=sys.stderr)
    print("  1. python -m pip install certifi", file=sys.stderr)
    print('  2. $env:SSL_CERT_FILE = (& python -c "import certifi; print(certifi.where())")', file=sys.stderr)
    print("  3. Or pass a trusted PEM bundle: --ca-bundle C:\\path\\to\\root-ca.pem", file=sys.stderr)


def print_timeout_help(exc: BaseException) -> None:
    print("Network request timed out during HTTPS connection.", file=sys.stderr)
    print(f"Details: {exc}", file=sys.stderr)
    print("", file=sys.stderr)
    print("The collector is metadata-only and does not download PDFs.", file=sys.stderr)
    print("Try these checks:", file=sys.stderr)
    print("  1. Open https://export.arxiv.org/api/query in your browser.", file=sys.stderr)
    print("  2. If you use a proxy/VPN, set HTTPS_PROXY/HTTP_PROXY for this terminal.", file=sys.stderr)
    print("  3. Retry with a larger timeout, e.g. --timeout 90.", file=sys.stderr)


def collect_arxiv_ids(values: list[str], ids_file: Path | None) -> list[str]:
    ids = [normalize_arxiv_id(value) for value in values if value.strip()]
    if ids_file:
        for line in ids_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            ids.append(normalize_arxiv_id(stripped))
    return sorted(set(ids))


if __name__ == "__main__":
    raise SystemExit(main())
