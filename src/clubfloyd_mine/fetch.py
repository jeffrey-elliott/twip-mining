"""Pass 2 - Fetch Local.

Politely fetches each manifest URL to data/raw/<year>/<id>/source.html +
meta.json. See doc/pipeline/02_fetch_local.md.

All network access goes through the injectable `http_get` parameter so
this can be fully unit-tested offline; `run()` wires up the real
urllib-based implementation. `--dry-run` reports what would happen
(fetch vs. skip) without making any network calls at all.
"""
from __future__ import annotations

import argparse
import hashlib
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from clubfloyd_mine import manifest as manifest_io
from clubfloyd_mine import paths
from clubfloyd_mine.models import FetchMeta, ManifestRecord, ManifestStatus

DEFAULT_USER_AGENT = (
    "twip-mining/0.1 (+https://github.com/jeffrey-elliott/twip-mining; "
    "research tool for ClubFloyd transcript mining)"
)
# Matches allthingsjacq.com's robots.txt: "User-agent: * / Crawl-delay: 2".
DEFAULT_DELAY_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 30


@dataclass
class HttpResponse:
    status_code: int
    body: bytes


HttpGet = Callable[[str, str], HttpResponse]


def urllib_get(url: str, user_agent: str) -> HttpResponse:
    """Default real HTTP backend. Connection failures raise OSError;
    HTTP error statuses (404, 500, ...) are returned as a normal response
    so callers can inspect status_code uniformly."""
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return HttpResponse(status_code=response.status, body=response.read())
    except urllib.error.HTTPError as exc:
        return HttpResponse(status_code=exc.code, body=exc.read())


class RateLimitedGet:
    """Wraps an HttpGet so every call after the first sleeps `delay` seconds
    first. One request at a time, with a polite gap, regardless of which
    caller (robots check or page fetch) makes the call."""

    def __init__(
        self,
        http_get: HttpGet,
        delay: float,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._http_get = http_get
        self._delay = delay
        self._sleep = sleep
        self._called = False

    def __call__(self, url: str, user_agent: str) -> HttpResponse:
        if self._called and self._delay > 0:
            self._sleep(self._delay)
        self._called = True
        return self._http_get(url, user_agent)


class RobotsCache:
    """Fetches and caches robots.txt per host via an injectable http_get.

    A missing or unreachable robots.txt is treated as allow-all, the
    conventional interpretation of "no robots.txt present".
    """

    def __init__(self, http_get: HttpGet, user_agent: str):
        self._http_get = http_get
        self._user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    def can_fetch(self, url: str) -> bool:
        split = urlsplit(url)
        host_key = f"{split.scheme}://{split.netloc}"
        parser = self._parsers.get(host_key)
        if parser is None:
            parser = RobotFileParser()
            try:
                response = self._http_get(f"{host_key}/robots.txt", self._user_agent)
                if response.status_code == 200:
                    parser.parse(response.body.decode("utf-8", errors="replace").splitlines())
                else:
                    parser.parse([])
            except OSError:
                parser.parse([])
            self._parsers[host_key] = parser
        return parser.can_fetch(self._user_agent, url)


@dataclass
class FetchResult:
    source_id: str
    action: str  # fetched | skipped_exists | skipped_robots | would_fetch | would_refetch | error
    detail: str = ""


def _load_previous_sha256(meta_path: Path) -> str | None:
    if not meta_path.exists():
        return None
    try:
        return FetchMeta.model_validate_json(meta_path.read_text(encoding="utf-8")).sha256
    except ValueError:
        return None


def fetch_one(
    record: ManifestRecord,
    *,
    root: Path | str | None,
    user_agent: str,
    http_get: HttpGet,
    robots: RobotsCache,
    force: bool,
    dry_run: bool,
) -> FetchResult:
    html_path = paths.raw_html_path(record.year, record.id, root)
    meta_path = paths.raw_meta_path(record.year, record.id, root)
    already_exists = html_path.exists()

    if already_exists and not force:
        return FetchResult(record.id, "skipped_exists", str(html_path))

    if dry_run:
        return FetchResult(
            record.id,
            "would_refetch" if already_exists else "would_fetch",
            record.source_url,
        )

    if not robots.can_fetch(record.source_url):
        return FetchResult(record.id, "skipped_robots", record.source_url)

    try:
        response = http_get(record.source_url, user_agent)
    except OSError as exc:
        return FetchResult(record.id, "error", str(exc))

    if response.status_code != 200:
        return FetchResult(record.id, "error", f"HTTP {response.status_code}")

    previous_sha256 = _load_previous_sha256(meta_path)
    sha256 = hashlib.sha256(response.body).hexdigest()

    paths.ensure_parent(html_path).write_bytes(response.body)
    meta = FetchMeta(
        source_url=record.source_url,
        fetched_at=datetime.now(timezone.utc),
        sha256=sha256,
        http_status=response.status_code,
        content_length=len(response.body),
        user_agent=user_agent,
        previous_sha256=previous_sha256,
    )
    paths.ensure_parent(meta_path).write_text(meta.model_dump_json(), encoding="utf-8")

    return FetchResult(record.id, "fetched", str(html_path))


def _print_summary(results: list[FetchResult], *, dry_run: bool) -> None:
    counts = Counter(result.action for result in results)
    label = "fetch (dry-run)" if dry_run else "fetch"
    summary = ", ".join(f"{action}={count}" for action, count in sorted(counts.items()))
    print(f"{label}: processed {len(results)} record(s) -- {summary}")
    for result in results:
        if result.action in ("error", "skipped_robots"):
            print(f"  {result.action}: {result.source_id} ({result.detail})")


def run(args: argparse.Namespace) -> None:
    manifest_file = paths.manifest_path(args.root)
    records = manifest_io.load_manifest(manifest_file)
    if not records:
        print(f"fetch: no records in {manifest_file}; run discover first")
        return

    http_get = RateLimitedGet(urllib_get, args.delay)
    robots = RobotsCache(http_get, args.user_agent)

    year = getattr(args, "year", None)
    selected = [r for r in records.values() if year is None or r.year == year]

    results = []
    for record in sorted(selected, key=lambda r: (r.year, r.id)):
        result = fetch_one(
            record,
            root=args.root,
            user_agent=args.user_agent,
            http_get=http_get,
            robots=robots,
            force=args.force,
            dry_run=args.dry_run,
        )
        results.append(result)

        if result.action in ("fetched", "skipped_exists"):
            # result.detail is the actual on-disk path for these two actions;
            # keep raw_path accurate even if --root differs from discover time.
            updated = manifest_io.advance_status(record, ManifestStatus.FETCHED)
            records[record.id] = updated.model_copy(update={"raw_path": result.detail})
        elif result.action == "error" and record.status == ManifestStatus.DISCOVERED:
            records[record.id] = record.model_copy(update={"status": ManifestStatus.ERROR})

    if not args.dry_run:
        manifest_io.write_manifest(manifest_file, records)

    _print_summary(results, dry_run=args.dry_run)
