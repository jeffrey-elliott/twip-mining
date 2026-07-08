"""Pass 1 - Discover Transcripts.

Parses a saved copy of the ClubFloyd index page and writes/merges
data/manifest.jsonl. See doc/pipeline/01_discover_transcripts.md.

Live fetching of the index page is not implemented yet: `run()` requires
a local HTML file (see CLAUDE.md priority "Add tests before broad
crawling"). The index page gives no reliable played-date text and its
URLs are NOT calendar dates (e.g. intfic_clubfloyd_20070901..20070905 are
five sessions in September 2007, numbered by sequence within the month,
not by day). So `played_date` and `page_title` are left unset here; a
later pass that reads the actual transcript page fills them in.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

from clubfloyd_mine import manifest as manifest_io
from clubfloyd_mine import paths
from clubfloyd_mine.models import GameRef, ManifestRecord, ManifestStatus

INDEX_URL = "https://allthingsjacq.com/interactive_fiction.html"

# Matches transcript link basenames like "intfic_clubfloyd_20070901.html" or
# "intfic_clubfloyd_20120403-NF.html". Group 2 is kept verbatim (not
# reinterpreted as YYYYMMDD) since it is not reliably a calendar date.
_TRANSCRIPT_HREF_RE = re.compile(r"^intfic_(?:club|night)floyd_(.+)\.html$", re.IGNORECASE)
# Matches the index page's per-year section markers: <a name="CF2007">.
_YEAR_ANCHOR_RE = re.compile(r"^CF(\d{4})$", re.IGNORECASE)
_LEADING_BY_RE = re.compile(r"^by\s+(.*)$", re.IGNORECASE)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def _parse_title_and_author(a_tag: Tag) -> tuple[str, str | None]:
    """Split an anchor like `<i>Monk by the Sea</i> by Elizabeth Decoste`.

    Splits on the <i> tag boundary rather than the text " by ", since some
    game titles themselves contain the word "by" (e.g. "Monk by the Sea").
    """
    italic = a_tag.find("i")
    if italic is not None:
        title = italic.get_text(strip=True)
        after = "".join(str(sibling) for sibling in italic.next_siblings).strip()
    else:
        title = a_tag.get_text(strip=True)
        after = ""
    if not after:
        return title, None
    match = _LEADING_BY_RE.match(after)
    return title, (match.group(1).strip() if match else after)


def parse_index_html(
    html: str, base_url: str = INDEX_URL, root: Path | str | None = None
) -> list[ManifestRecord]:
    """Pure function: index page HTML -> candidate ManifestRecords.

    One record per unique transcript href; a single href that lists
    multiple consecutive rows (a session covering several games) becomes
    one record with multiple `games` entries. `root` is threaded through
    to `raw_path` so it matches wherever the manifest itself is written.
    """
    soup = BeautifulSoup(html, "html.parser")
    current_year: int | None = None
    games_by_href: dict[str, list[GameRef]] = {}
    year_by_href: dict[str, int] = {}
    href_order: list[str] = []

    for a_tag in soup.find_all("a"):
        name_attr = a_tag.get("name")
        if name_attr:
            year_match = _YEAR_ANCHOR_RE.match(name_attr)
            if year_match:
                current_year = int(year_match.group(1))
            continue

        href = a_tag.get("href")
        if not href or current_year is None:
            continue
        basename = Path(urlsplit(href).path).name
        if not _TRANSCRIPT_HREF_RE.match(basename):
            continue

        title, author = _parse_title_and_author(a_tag)
        if href not in games_by_href:
            games_by_href[href] = []
            year_by_href[href] = current_year
            href_order.append(href)
        games_by_href[href].append(GameRef(title=title, author=author))

    records = []
    for href in href_order:
        year = year_by_href[href]
        games = games_by_href[href]
        basename = Path(urlsplit(href).path).name
        url_suffix = _TRANSCRIPT_HREF_RE.match(basename).group(1).lower()
        source_id = f"{url_suffix}-{_slugify(games[0].title)}"
        records.append(
            ManifestRecord(
                id=source_id,
                source_url=urljoin(base_url, href),
                year=year,
                games=games,
                raw_path=str(paths.raw_html_path(year, source_id, root)),
                status=ManifestStatus.DISCOVERED,
            )
        )
    return records


def merge_discovered(
    existing: dict[str, ManifestRecord], discovered: list[ManifestRecord]
) -> tuple[dict[str, ManifestRecord], int]:
    """Add newly discovered records without disturbing already-tracked ones.

    Keeps the pass restartable/idempotent: a record already in the
    manifest (possibly with status advanced by a later pass) is left
    untouched even if the fixture would regenerate it identically.
    """
    merged = dict(existing)
    new_count = 0
    for record in discovered:
        if record.id not in merged:
            merged[record.id] = record
            new_count += 1
    return merged, new_count


def run(args: argparse.Namespace) -> None:
    html = args.input.read_text(encoding="utf-8", errors="replace")
    discovered = parse_index_html(html, base_url=args.index_url, root=args.root)
    year = getattr(args, "year", None)
    if year is not None:
        discovered = [record for record in discovered if record.year == year]

    manifest_file = paths.manifest_path(args.root)
    existing = manifest_io.load_manifest(manifest_file)
    merged, new_count = merge_discovered(existing, discovered)
    manifest_io.write_manifest(manifest_file, merged)

    print(
        f"discover: parsed {len(discovered)} candidate transcript(s) from {args.input}, "
        f"added {new_count} new record(s) ({len(merged)} total in {manifest_file})"
    )
