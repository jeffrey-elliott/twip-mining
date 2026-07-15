"""Pass 4 - Pair Commands to Results.

Reads normalized transcript blocks and writes
data/parsed/<year>/<id>/command_pairs.jsonl.
See doc/pipeline/04_pair_commands_to_results.md and
doc/club_floyd_transcript_classifier_examples.md.

Pairing heuristic (from the classifier examples doc's "practical extraction
heuristic"): each COMMAND block starts a new pair. The immediately following
run of consecutive GAME_OUTPUT (and PAGINATION -- see below) blocks is
attached as that command's result; the run stops at the first block that is
neither. A command with no following GAME_OUTPUT blocks (e.g. two commands
sent back-to-back before Floyd replies, or a command as the last block in
the transcript) still produces a pair with an empty result_blocks list --
per "invalid/unanswered commands are still input", it must not be dropped.

PAGINATION blocks (MORE-prompt pauses -- see normalize.py's module
docstring) are included in a result run rather than ending it: confirmed
against the real corpus, a long reply routinely spans several MORE pages
with one of these pause lines between each, and treating them like an
ordinary COMMAND/DISCUSSION boundary fragmented that single reply into
several bogus pairs, one per pause. They stay in result_blocks (not
dropped) so the pair still shows exactly where the pause fell.

Leading game output (doc/annotated_screenshots/preamble.png +
combat_loop_annotated.png style annotations against the real 2007-09-01
Nevermore transcript): a game that's already loaded before the transcript
log starts prints its title/credits/opening room description with no
command in front of it at all -- blocks 41-60 of that transcript are
GAME_OUTPUT sitting right after the preamble's MUD chatter, before the
first COMMAND block ("about") anywhere. The main loop below only ever
attaches a GAME_OUTPUT run to the COMMAND immediately before it, so this
leading run was previously skipped one block at a time and silently
dropped -- never written to command_pairs.jsonl, and therefore invisible to
classify/make-records too. `extract_pairs` now emits it as a single
synthetic pair (`is_leading_output=True`, `command_text=""`) ahead of
pair_index 0, so it still traces back to source instead of vanishing. This
does not apply to a game's boot text printed after an in-transcript "load
X" command (see club_floyd_midamble_annotated.png) -- that already attaches
correctly as `load X`'s own result via the normal loop, since `load` is a
real preceding COMMAND block.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from clubfloyd_mine import manifest as manifest_io
from clubfloyd_mine import paths
from clubfloyd_mine.models import (
    BlockKind,
    CommandPair,
    ManifestRecord,
    ManifestStatus,
    Transcript,
)


def extract_pairs(transcript: Transcript) -> list[CommandPair]:
    pairs: list[CommandPair] = []
    blocks = transcript.blocks
    n = len(blocks)

    first_command_idx = next((idx for idx, b in enumerate(blocks) if b.kind is BlockKind.COMMAND), n)
    leading_output = [
        b for b in blocks[:first_command_idx] if b.kind in (BlockKind.GAME_OUTPUT, BlockKind.PAGINATION)
    ]
    if leading_output:
        pairs.append(
            CommandPair(
                source_id=transcript.source_id,
                pair_index=0,
                command_text="",
                result_blocks=leading_output,
                is_leading_output=True,
            )
        )

    i = 0
    while i < n:
        block = blocks[i]
        if block.kind is not BlockKind.COMMAND:
            i += 1
            continue

        result_blocks = []
        j = i + 1
        while j < n and blocks[j].kind in (BlockKind.GAME_OUTPUT, BlockKind.PAGINATION):
            result_blocks.append(blocks[j])
            j += 1

        pairs.append(
            CommandPair(
                source_id=transcript.source_id,
                pair_index=len(pairs),
                speaker=block.speaker,
                addressee=block.addressee,
                command_text=block.text,
                result_blocks=result_blocks,
            )
        )
        i = j
    return pairs


def _write_command_pairs(path: Path, pairs: list[CommandPair]) -> None:
    lines = [pair.model_dump_json() for pair in pairs]
    paths.ensure_parent(path).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_command_pairs(record: ManifestRecord, root: Path | str | None = None) -> list[CommandPair]:
    """Read data/parsed/<year>/<id>/command_pairs.jsonl for one manifest
    record, or [] if extract-pairs hasn't produced it yet. Shared by any
    pass or tool that needs to read back this pass's output (audit, view)."""
    pairs_path = paths.command_pairs_path(record.year, record.id, root)
    if not pairs_path.exists():
        return []
    pairs = []
    for line in pairs_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            pairs.append(CommandPair.model_validate_json(line))
    return pairs


@dataclass
class ExtractPairsResult:
    source_id: str
    action: str  # extracted | skipped_exists | skipped_missing_transcript | error
    detail: str = ""
    pair_count: int = 0


def extract_pairs_one(
    record: ManifestRecord, *, root: Path | str | None, force: bool
) -> ExtractPairsResult:
    transcript_json_path = paths.transcript_json_path(record.year, record.id, root)
    pairs_path = paths.command_pairs_path(record.year, record.id, root)

    if pairs_path.exists() and not force:
        return ExtractPairsResult(record.id, "skipped_exists", str(pairs_path))

    if not transcript_json_path.exists():
        return ExtractPairsResult(record.id, "skipped_missing_transcript", str(transcript_json_path))

    try:
        transcript = Transcript.model_validate_json(transcript_json_path.read_text(encoding="utf-8"))
        pairs = extract_pairs(transcript)
    except (OSError, ValueError) as exc:
        return ExtractPairsResult(record.id, "error", str(exc))

    _write_command_pairs(pairs_path, pairs)
    return ExtractPairsResult(record.id, "extracted", str(pairs_path), pair_count=len(pairs))


def _print_summary(results: list[ExtractPairsResult]) -> None:
    from collections import Counter

    counts = Counter(result.action for result in results)
    summary = ", ".join(f"{action}={count}" for action, count in sorted(counts.items()))
    print(f"extract-pairs: processed {len(results)} record(s) -- {summary}")
    for result in results:
        if result.action == "error":
            print(f"  error: {result.source_id} ({result.detail})")


def run(args: argparse.Namespace) -> None:
    manifest_file = paths.manifest_path(args.root)
    records = manifest_io.load_manifest(manifest_file)
    if not records:
        print(f"extract-pairs: no records in {manifest_file}; run discover/fetch/normalize first")
        return

    year = getattr(args, "year", None)
    selected = [r for r in records.values() if year is None or r.year == year]

    results = []
    for record in sorted(selected, key=lambda r: (r.year, r.id)):
        result = extract_pairs_one(record, root=args.root, force=args.force)
        results.append(result)
        if result.action in ("extracted", "skipped_exists"):
            records[record.id] = manifest_io.advance_status(record, ManifestStatus.PARSED)

    manifest_io.write_manifest(manifest_file, records)
    _print_summary(results)
