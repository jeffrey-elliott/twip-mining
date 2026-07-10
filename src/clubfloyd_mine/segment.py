"""Segment a normalized transcript into per-game segments.

A single ClubFloyd transcript can cover more than one game (see
doc/annotated_screenshots/multi_game_preamble.png, a real 4-game session).
Reads data/text/<year>/<id>/transcript.json and writes
data/parsed/<year>/<id>/session.json.

Boundary heuristic (the "midamble pattern" documented against the real
transcript in doc/annotated_screenshots/club_floyd_midamble_annotated.png):
when one game ends, its final output/victory text is followed by a
RESTART/RESTORE/QUIT prompt, then a discussion "bridge" (players leave,
the next game is announced), then a human-typed "load X" command that
starts the next game. "load X" is therefore the deterministic,
command-level signal of a new segment starting -- everything from one
"load X" up to (but not including) the next belongs to one segment,
including the trailing discussion/quit "midamble" that precedes the next
load. The very first segment has no preceding "load" at all when a game
was already loaded before the transcript log started (see
doc/annotated_screenshots/preamble.png's single-game Nevermore case, which
has no "load" anywhere) -- that segment starts implicitly at block 0.

Not every "load X" command is a real boundary: a player may retry "load X"
while still trapped in the *previous* game's RESTART/RESTORE/QUIT menu,
which rejects it ("Please give one of the answers above.", now also in
classify.py's _SCORE_OR_END_STATE_PREFIXES) rather than starting anything.
`_is_successful_load` checks the load command's own immediately-following
result run for that rejection marker before treating it as a boundary --
otherwise a single retried "load" would be double-counted as two segments.

Known simplification: this assumes every "load X" starts a *different*
game. A mid-game "load" used as a synonym for restoring a save of the
*same* game (if any real transcript does this) would be wrongly treated as
a new segment; no such example has been seen yet, so this isn't handled.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from clubfloyd_mine import manifest as manifest_io
from clubfloyd_mine import paths
from clubfloyd_mine.models import (
    BlockKind,
    GameSegment,
    ManifestRecord,
    SessionSegments,
    Transcript,
    TranscriptBlock,
)

_LOAD_COMMAND_RE = re.compile(r"^load\b", re.IGNORECASE)
_REJECTED_LOAD_MARKER = "please give one of the answers above"


def _is_successful_load(blocks: list[TranscriptBlock], command_index: int) -> bool:
    """Whether the "load X" command at `command_index` actually started a
    new game, rather than being rejected by the previous game's still-open
    RESTART/RESTORE/QUIT menu. Checks the same immediately-following
    GAME_OUTPUT run extract_pairs.py would attach to this command as its
    result."""
    for block in blocks[command_index + 1 :]:
        if block.kind is not BlockKind.GAME_OUTPUT:
            break
        if _REJECTED_LOAD_MARKER in block.text.strip().lower():
            return False
    return True


def find_segment_boundaries(blocks: list[TranscriptBlock]) -> list[int]:
    """Return block indices where a new per-game segment starts: index 0
    (implicit first segment), plus every COMMAND block that is a
    successful "load X"."""
    if not blocks:
        return []
    boundaries = [0]
    for i, block in enumerate(blocks):
        if i == 0:
            continue
        if (
            block.kind is BlockKind.COMMAND
            and _LOAD_COMMAND_RE.match(block.text.strip())
            and _is_successful_load(blocks, i)
        ):
            boundaries.append(i)
    return boundaries


def segment_transcript(transcript: Transcript) -> SessionSegments:
    blocks = transcript.blocks
    boundaries = find_segment_boundaries(blocks)
    ends = boundaries[1:] + [len(blocks)]

    segments = []
    for index, (start, end) in enumerate(zip(boundaries, ends)):
        start_block = blocks[start]
        start_command = start_block.text if start_block.kind is BlockKind.COMMAND else None
        segments.append(
            GameSegment(
                segment_index=index,
                start_block_index=start,
                end_block_index=end,
                start_command=start_command,
            )
        )
    return SessionSegments(source_id=transcript.source_id, segments=segments)


@dataclass
class SegmentResult:
    source_id: str
    action: str  # segmented | skipped_exists | skipped_missing_transcript | error
    detail: str = ""
    segment_count: int = 0


def segment_one(record: ManifestRecord, *, root: Path | str | None, force: bool) -> SegmentResult:
    transcript_json_path = paths.transcript_json_path(record.year, record.id, root)
    session_path = paths.session_json_path(record.year, record.id, root)

    if session_path.exists() and not force:
        return SegmentResult(record.id, "skipped_exists", str(session_path))

    if not transcript_json_path.exists():
        return SegmentResult(record.id, "skipped_missing_transcript", str(transcript_json_path))

    try:
        transcript = Transcript.model_validate_json(transcript_json_path.read_text(encoding="utf-8"))
        session = segment_transcript(transcript)
    except (OSError, ValueError) as exc:
        return SegmentResult(record.id, "error", str(exc))

    paths.ensure_parent(session_path).write_text(session.model_dump_json(indent=2), encoding="utf-8")
    return SegmentResult(record.id, "segmented", str(session_path), segment_count=len(session.segments))


def _print_summary(results: list[SegmentResult]) -> None:
    from collections import Counter

    counts = Counter(result.action for result in results)
    summary = ", ".join(f"{action}={count}" for action, count in sorted(counts.items()))
    print(f"segment: processed {len(results)} record(s) -- {summary}")
    for result in results:
        if result.action == "error":
            print(f"  error: {result.source_id} ({result.detail})")


def run(args: argparse.Namespace) -> None:
    manifest_file = paths.manifest_path(args.root)
    records = manifest_io.load_manifest(manifest_file)
    if not records:
        print(f"segment: no records in {manifest_file}; run discover/fetch/normalize first")
        return

    year = getattr(args, "year", None)
    selected = [r for r in records.values() if year is None or r.year == year]
    force = getattr(args, "force", False)

    results = [segment_one(record, root=args.root, force=force) for record in sorted(selected, key=lambda r: (r.year, r.id))]
    _print_summary(results)
