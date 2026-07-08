"""Pass 3 - Normalize Data.

Converts raw HTML into data/text/<year>/<id>/transcript.txt + transcript.json.
See doc/pipeline/03_normalize_data.md and
doc/club_floyd_transcript_classifier_examples.md for the classification
rules this implements.

Core distinction (confirmed against real transcripts + the classifier
examples doc):
  - game_output: a line whose left prefix is exactly "Floyd |". Preserved
    verbatim after the pipe (no stripping) -- real transcripts use leading
    spaces for centered ASCII art (game title screens).
  - command (game_input): "<speaker> says|asks (to Floyd/CF/ClubFloyd), "..."
  - bot_meta: Floyd itself speaking ("Floyd says/asks ...", with or without
    an addressee), as opposed to relaying game text via "Floyd |".
  - discussion: everything else -- human chat, MUD arrivals/actions/channel
    events, room descriptions, whispers, commands aimed at someone other
    than Floyd. This is a deliberately broad catch-all, not a last-resort
    dumping ground: real transcripts are messy MUD chat logs, and most
    non-game content genuinely has no signal worth a separate kind.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

from clubfloyd_mine import manifest as manifest_io
from clubfloyd_mine import paths
from clubfloyd_mine.models import (
    BlockKind,
    ManifestRecord,
    ManifestStatus,
    Transcript,
    TranscriptBlock,
)

# The addressee forms that mean "this command is aimed at the game via Floyd".
_FLOYD_ADDRESSEE_NAMES = {"floyd", "cf", "clubfloyd"}

_GAME_OUTPUT_RE = re.compile(r"^floyd \|(?P<text>.*)$", re.IGNORECASE | re.DOTALL)
# Speaker is bounded to name-like characters (letters/digits/spaces/apostrophes/
# hyphens, no sentence punctuation) so prose that happens to contain the word
# "says" or "asks" mid-sentence (e.g. a room description: "The sign over it
# says, ...") can't be mistaken for a chat line -- an unbounded ".+?" here
# matched the entire preceding sentence as a bogus "speaker".
_SPEECH_RE = re.compile(
    r"^(?P<speaker>[A-Za-z][A-Za-z0-9 '_-]{0,29}?)\s+(?:says|asks)\s*"
    r"(?:\(to\s+(?P<addressee>[^)]+)\))?\s*,?\s*(?P<text>.*)$",
    re.IGNORECASE | re.DOTALL,
)


def _strip_wrapping_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    return text


def _classify_row(raw_text: str) -> TranscriptBlock:
    game_output_match = _GAME_OUTPUT_RE.match(raw_text)
    if game_output_match:
        return TranscriptBlock(kind=BlockKind.GAME_OUTPUT, text=game_output_match.group("text"))

    speech_match = _SPEECH_RE.match(raw_text)
    if speech_match:
        speaker = speech_match.group("speaker").strip()
        addressee = speech_match.group("addressee")
        addressee = addressee.strip() if addressee else None
        text = _strip_wrapping_quotes(speech_match.group("text"))

        if speaker.lower() == "floyd":
            kind = BlockKind.BOT_META
        elif addressee is not None and addressee.lower() in _FLOYD_ADDRESSEE_NAMES:
            kind = BlockKind.COMMAND
        else:
            kind = BlockKind.DISCUSSION
        return TranscriptBlock(kind=kind, speaker=speaker, addressee=addressee, text=text)

    return TranscriptBlock(kind=BlockKind.DISCUSSION, text=raw_text.strip())


def _extract_rows(html: str) -> list[str]:
    """Pull one text string per transcript row, in document order.

    Real transcript HTML has malformed markup (a bare <tr> nested inside a
    <td> with no <table> wrapper), so this walks every <td> and skips ones
    that themselves contain a nested tr/table -- those are the malformed
    "container" cells that would otherwise duplicate their children's text.
    The transcript content lives in the *last* <table> on the page (the
    site's nav header is an earlier, separate <table>).
    """
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return []
    transcript_table = tables[-1]

    rows = []
    for td in transcript_table.find_all("td"):
        if td.find(["tr", "table"]) is not None:
            continue
        text = td.get_text()
        if text.strip():
            rows.append(text)
    return rows


def parse_transcript_html(html: str, source_id: str) -> Transcript:
    blocks = [_classify_row(row) for row in _extract_rows(html)]
    return Transcript(source_id=source_id, blocks=blocks)


def render_transcript_txt(transcript: Transcript) -> str:
    lines = []
    for block in transcript.blocks:
        if block.kind == BlockKind.GAME_OUTPUT:
            lines.append(block.text)
        elif block.kind == BlockKind.COMMAND:
            lines.append(f"{block.speaker} > {block.text}")
        elif block.kind == BlockKind.BOT_META:
            if block.addressee:
                lines.append(f"Floyd (to {block.addressee}): {block.text}")
            else:
                lines.append(f"Floyd: {block.text}")
        else:  # DISCUSSION
            lines.append(f"{block.speaker}: {block.text}" if block.speaker else block.text)
    return "\n".join(lines) + ("\n" if lines else "")


def _read_html(path: Path) -> str:
    raw_bytes = path.read_bytes()
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return raw_bytes.decode("cp1252", errors="replace")


@dataclass
class NormalizeResult:
    source_id: str
    action: str  # normalized | skipped_exists | skipped_missing_raw | error
    detail: str = ""


def normalize_one(record: ManifestRecord, *, root: Path | str | None, force: bool) -> NormalizeResult:
    raw_html_path = paths.raw_html_path(record.year, record.id, root)
    txt_path = paths.transcript_txt_path(record.year, record.id, root)
    json_path = paths.transcript_json_path(record.year, record.id, root)

    if txt_path.exists() and json_path.exists() and not force:
        return NormalizeResult(record.id, "skipped_exists", str(json_path))

    if not raw_html_path.exists():
        return NormalizeResult(record.id, "skipped_missing_raw", str(raw_html_path))

    try:
        html = _read_html(raw_html_path)
        transcript = parse_transcript_html(html, source_id=record.id)
    except (OSError, ValueError) as exc:
        return NormalizeResult(record.id, "error", str(exc))

    paths.ensure_parent(txt_path).write_text(render_transcript_txt(transcript), encoding="utf-8")
    paths.ensure_parent(json_path).write_text(transcript.model_dump_json(indent=2), encoding="utf-8")

    return NormalizeResult(record.id, "normalized", str(json_path))


def _print_summary(results: list[NormalizeResult]) -> None:
    from collections import Counter

    counts = Counter(result.action for result in results)
    summary = ", ".join(f"{action}={count}" for action, count in sorted(counts.items()))
    print(f"normalize: processed {len(results)} record(s) -- {summary}")
    for result in results:
        if result.action == "error":
            print(f"  error: {result.source_id} ({result.detail})")


def run(args: argparse.Namespace) -> None:
    manifest_file = paths.manifest_path(args.root)
    records = manifest_io.load_manifest(manifest_file)
    if not records:
        print(f"normalize: no records in {manifest_file}; run discover/fetch first")
        return

    year = getattr(args, "year", None)
    selected = [r for r in records.values() if year is None or r.year == year]

    results = []
    for record in sorted(selected, key=lambda r: (r.year, r.id)):
        result = normalize_one(record, root=args.root, force=args.force)
        results.append(result)
        if result.action in ("normalized", "skipped_exists"):
            records[record.id] = manifest_io.advance_status(record, ManifestStatus.NORMALIZED)

    manifest_io.write_manifest(manifest_file, records)
    _print_summary(results)
