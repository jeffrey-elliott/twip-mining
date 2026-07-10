"""CLI entry point for the clubfloyd pipeline (see CLAUDE.md's pass table)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from clubfloyd_mine import (
    audit,
    classify,
    discover,
    extract_pairs,
    fetch,
    make_records,
    normalize,
    segment,
    view,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clubfloyd",
        description="Deterministic tooling for mining ClubFloyd transcripts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_root_arg(sub: argparse.ArgumentParser) -> None:
        sub.add_argument(
            "--root",
            default=None,
            help="Data root directory (default: ./data, or $CLUBFLOYD_DATA_ROOT)",
        )

    def add_year_arg(sub: argparse.ArgumentParser) -> None:
        sub.add_argument(
            "--year",
            type=int,
            default=None,
            help="Only process records from this year (default: all years in the manifest)",
        )

    p_discover = subparsers.add_parser("discover", help="Discover transcripts from a saved index page")
    p_discover.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to a saved copy of the index page HTML (live fetching is not implemented yet)",
    )
    p_discover.add_argument(
        "--index-url",
        default=discover.INDEX_URL,
        help="Base URL for resolving relative links and recording provenance",
    )
    add_year_arg(p_discover)
    add_root_arg(p_discover)
    p_discover.set_defaults(func=discover.run)

    p_fetch = subparsers.add_parser("fetch", help="Fetch manifest URLs to local raw HTML")
    p_fetch.add_argument("--force", action="store_true", help="Refetch even if a local copy already exists")
    p_fetch.add_argument(
        "--delay",
        type=float,
        default=fetch.DEFAULT_DELAY_SECONDS,
        help="Seconds to wait between requests (matches the source site's robots.txt Crawl-delay)",
    )
    p_fetch.add_argument(
        "--user-agent",
        default=fetch.DEFAULT_USER_AGENT,
        help="User-Agent header sent with every request",
    )
    p_fetch.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be fetched without making any network requests",
    )
    add_year_arg(p_fetch)
    add_root_arg(p_fetch)
    p_fetch.set_defaults(func=fetch.run)

    p_normalize = subparsers.add_parser("normalize", help="Convert raw HTML to normalized transcript text/json")
    p_normalize.add_argument("--force", action="store_true", help="Re-normalize even if output exists")
    add_year_arg(p_normalize)
    add_root_arg(p_normalize)
    p_normalize.set_defaults(func=normalize.run)

    p_segment = subparsers.add_parser("segment", help="Split a normalized transcript into per-game segments")
    add_root_arg(p_segment)
    p_segment.set_defaults(func=segment.run)

    p_extract_pairs = subparsers.add_parser("extract-pairs", help="Pair commands to Floyd with their results")
    p_extract_pairs.add_argument("--force", action="store_true", help="Re-extract even if output exists")
    add_year_arg(p_extract_pairs)
    add_root_arg(p_extract_pairs)
    p_extract_pairs.set_defaults(func=extract_pairs.run)

    p_classify = subparsers.add_parser("classify", help="Classify command pairs into outcome buckets")
    add_root_arg(p_classify)
    p_classify.set_defaults(func=classify.run)

    p_make_records = subparsers.add_parser("make-records", help="Generate candidate markdown records")
    add_root_arg(p_make_records)
    p_make_records.set_defaults(func=make_records.run)

    p_audit = subparsers.add_parser("audit", help="Report pipeline progress and obvious-case outcome counts")
    add_year_arg(p_audit)
    add_root_arg(p_audit)
    p_audit.set_defaults(func=audit.run)

    p_view = subparsers.add_parser("view", help="Serve a local read-only webpage for browsing command pairs")
    p_view.add_argument("--port", type=int, default=view.DEFAULT_PORT, help="Port to listen on")
    p_view.add_argument(
        "--host",
        default=view.DEFAULT_HOST,
        help="Bind address (default: loopback only, not exposed on the network)",
    )
    add_year_arg(p_view)
    add_root_arg(p_view)
    p_view.set_defaults(func=view.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except NotImplementedError as exc:
        print(f"clubfloyd {args.command}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
