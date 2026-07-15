"""Pass 3 - Normalize Data.

Converts raw HTML into data/text/<year>/<id>/transcript.txt + transcript.json.
See doc/pipeline/03_normalize_data.md and
doc/club_floyd_transcript_classifier_examples.md for the classification
rules this implements.

Core distinction (confirmed against real transcripts + the classifier
examples doc):
  - game_output: a line whose left prefix is exactly "Floyd |"/"Floyd ]"
    (main output stream / status-bar-or-menu line -- room name, score/turns,
    paging menus) or the same pair under "CF" instead of "Floyd" --
    confirmed against real transcripts: the relay bot's name changes from
    "Floyd" to "CF" starting around 2020 (e.g.
    data/raw/2023/20230403-nothing-could-be-further-from-the-truth uses "CF
    |"/"CF ]" throughout; every 2020-2025 session in this corpus does), and
    every session from either era is otherwise internally consistent about
    which name it uses. Classified per physical line, not per whole row: a
    single row/td routinely bundles many original lines (a whole turn's
    screen output) with a newline between each, and any row where every
    non-blank line carries one of these prefixes is one game_output block --
    a blank line (a paragraph break inside a longer description) is treated
    as part of the block rather than breaking it, since real multi-paragraph
    game output routinely has one between paragraphs. Preserved verbatim
    after the prefix (no stripping) -- real transcripts use leading spaces
    for centered ASCII art (game title screens).
  - command (game_input): "<speaker> says|asks (to Floyd/CF/ClubFloyd), "..."
  - bot_meta: Floyd itself speaking ("Floyd says/asks ...", with or without
    an addressee), as opposed to relaying game text via "Floyd |".
  - pagination: a MORE-prompt pause, not real game input/output -- either a
    command to Floyd/CF whose text is exactly "space"/"push space"/"press
    space", or the MUD emote a client sends when a user hits the pause key
    ("<name> pushes the green 'space' button."/"<name> presses the yellow
    enter button."). Confirmed against the real corpus at large scale
    (~8,000 occurrences): a long game_output reply often spans several
    MORE pages, each followed by one of these lines, so treating them as
    ordinary command/discussion blocks fragmented a single reply into
    several bogus command_pairs at every pause (see extract_pairs.py).
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

# Matched per physical line (see _classify_row), not against a whole
# (possibly multi-line) row -- a row that starts with a "Floyd ]" status-bar
# line before its "Floyd |" body text used to fail this when it was anchored
# against the entire row, silently dumping real game output into discussion.
# "cf" alongside "floyd": the relay bot's own name in the transcript changes
# around 2020 (see module docstring) -- _FLOYD_ADDRESSEE_NAMES below already
# treated "cf" as an equivalent addressee for commands, but this regex only
# ever matched "floyd", so every 2020+ session's game output was silently
# landing in discussion until this was noticed.
_GAME_OUTPUT_LINE_RE = re.compile(r"^(?:floyd|cf) [|\]](?P<text>.*)$", re.IGNORECASE)
# Speaker is bounded to name-like characters (letters/digits/spaces/apostrophes/
# hyphens, no sentence punctuation) so prose that happens to contain the word
# "says" or "asks" mid-sentence (e.g. a room description: "The sign over it
# says, ...") can't be mistaken for a chat line -- an unbounded ".+?" here
# matched the entire preceding sentence as a bogus "speaker".
#
# "hollers" (doc/annotated_screenshots/club_floyd_midamble_annotated.png:
# "Jacqueline hollers, \"Next game, Nazi Mice...\"") is added alongside
# says/asks -- without it this line still lands correctly in DISCUSSION via
# _classify_row's final catch-all, but speaker/addressee extraction is lost.
# Other MUD-emote verbs (shouts/yells/exclaims/...) are deliberately not
# added without their own real transcript evidence.
_SPEECH_RE = re.compile(
    r"^(?P<speaker>[A-Za-z][A-Za-z0-9 '_-]{0,29}?)\s+(?:says|asks|hollers)\s*"
    r"(?:\(to\s+(?P<addressee>[^)]+)\))?\s*,?\s*(?P<text>.*)$",
    re.IGNORECASE | re.DOTALL,
)

# A command sent to Floyd/CF that's purely a MORE-prompt pagination nudge,
# not a real game command -- confirmed against the real corpus (~250
# occurrences across 95 transcripts). Deliberately an exact-text allowlist,
# not a "starts with space" pattern: "x space"/"examine space" is a real
# in-game command in several games (confirmed against real transcripts,
# e.g. data/text/2012/20120405-dinner-bell) and must not be swept in here.
_PAGINATION_COMMAND_TEXTS = {"space", "push space", "press space"}

# The MUD emote a client sends when a user hits the pause key at a MORE
# prompt -- confirmed against the real corpus: "<name> pushes the green
# 'space' button." / "<name> presses the yellow enter button." account for
# ~7,900 of ~7,903 matches of this shape; the handful of other button
# colors/objects (e.g. "pushes the left leg") look like real in-game puzzle
# actions and are deliberately excluded by anchoring to exactly these two
# button/verb combinations rather than a general "pushes/presses the ...
# button" pattern.
_PAGINATION_EMOTE_RE = re.compile(
    r"^(?P<speaker>[A-Za-z][A-Za-z0-9 '_-]{0,29}?) "
    r"(?:pushes the green 'space' button|presses the yellow enter button)\.?$",
    re.IGNORECASE,
)


def _strip_wrapping_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    return text


def _classify_row(raw_text: str) -> TranscriptBlock:
    # A row can bundle a whole turn's screen output as several newline-
    # separated physical lines in one td (see _extract_rows). Only treat the
    # row as one game_output block if EVERY non-blank line carries a
    # recognized prefix -- a row with even one non-matching, non-blank line
    # isn't evidenced to be safe to reinterpret, so it falls through to the
    # speech/discussion checks below unchanged, same as before this per-line
    # split existed. A blank line is tolerated as-is (not required to carry
    # its own prefix): real multi-paragraph game output routinely has one as
    # a paragraph break -- _extract_rows already drops any row that's blank
    # in aggregate, so an all-blank `lines` here can't happen.
    lines = raw_text.splitlines()
    game_output_texts: list[str] | None = []
    for line in lines:
        if line.strip() == "":
            game_output_texts.append("")
            continue
        match = _GAME_OUTPUT_LINE_RE.match(line)
        if match is None:
            game_output_texts = None
            break
        game_output_texts.append(match.group("text"))

    if game_output_texts is not None:
        return TranscriptBlock(kind=BlockKind.GAME_OUTPUT, text="\n".join(game_output_texts))

    pagination_match = _PAGINATION_EMOTE_RE.match(raw_text.strip())
    if pagination_match:
        return TranscriptBlock(
            kind=BlockKind.PAGINATION,
            speaker=pagination_match.group("speaker").strip(),
            text=raw_text.strip(),
        )

    speech_match = _SPEECH_RE.match(raw_text)
    if speech_match:
        speaker = speech_match.group("speaker").strip()
        addressee = speech_match.group("addressee")
        addressee = addressee.strip() if addressee else None
        text = _strip_wrapping_quotes(speech_match.group("text"))

        if speaker.lower() == "floyd":
            kind = BlockKind.BOT_META
        elif addressee is not None and addressee.lower() in _FLOYD_ADDRESSEE_NAMES:
            if text.strip().lower() in _PAGINATION_COMMAND_TEXTS:
                kind = BlockKind.PAGINATION
            else:
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
        elif block.kind == BlockKind.PAGINATION:
            lines.append(f"{block.speaker} [pause]: {block.text}" if block.speaker else f"[pause] {block.text}")
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
