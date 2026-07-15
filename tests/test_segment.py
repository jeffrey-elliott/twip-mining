"""Tests for segment.py: splitting a normalized transcript into per-game
segments via the "load X" boundary heuristic documented in
doc/annotated_screenshots/club_floyd_midamble_annotated.png."""
from pathlib import Path
from types import SimpleNamespace

from clubfloyd_mine import manifest as manifest_io, paths, segment
from clubfloyd_mine.models import (
    BlockKind,
    GameRef,
    ManifestRecord,
    ManifestStatus,
    SessionSegments,
    Transcript,
    TranscriptBlock,
)


def _block(kind, text, speaker=None, addressee=None):
    return TranscriptBlock(kind=kind, speaker=speaker, addressee=addressee, text=text)


# --- find_segment_boundaries ---------------------------------------------------------


def test_empty_blocks_has_no_boundaries():
    assert segment.find_segment_boundaries([]) == []


def test_single_game_with_no_load_command_is_one_implicit_segment():
    # Real Nevermore shape: pre-loaded before the log starts, no "load"
    # anywhere in the transcript at all.
    blocks = [
        _block(BlockKind.DISCUSSION, "did we decide on Nevermore?"),
        _block(BlockKind.GAME_OUTPUT, "NEVERMORE"),
        _block(BlockKind.COMMAND, "about", addressee="floyd"),
        _block(BlockKind.GAME_OUTPUT, "NEVERMORE is a work of Interactive Fiction..."),
    ]
    assert segment.find_segment_boundaries(blocks) == [0]


def test_successful_load_command_is_a_boundary():
    # A "load" at index 0 doesn't get double-counted -- it's simply where
    # the implicit first segment happens to start.
    blocks = [
        _block(BlockKind.COMMAND, "load thedayishothitler", addressee="floyd"),
        _block(BlockKind.GAME_OUTPUT, "The Day I Shot Hitler"),
    ]
    assert segment.find_segment_boundaries(blocks) == [0]


def test_second_successful_load_command_is_a_real_boundary():
    blocks = [
        _block(BlockKind.COMMAND, "load thedayishothitler", addressee="floyd"),  # 0
        _block(BlockKind.GAME_OUTPUT, "The Day I Shot Hitler"),  # 1
        _block(BlockKind.COMMAND, "load nazimice", addressee="floyd"),  # 2
        _block(BlockKind.GAME_OUTPUT, "Nazi Mice"),  # 3
    ]
    assert segment.find_segment_boundaries(blocks) == [0, 2]


def test_rejected_load_attempt_is_not_a_boundary():
    # club_floyd_midamble_annotated.png's "LOAD ATTEMPT" box: typed while
    # still inside the old game's RESTART/RESTORE/QUIT prompt.
    blocks = [
        _block(BlockKind.GAME_OUTPUT, "*** You have won ***"),
        _block(BlockKind.GAME_OUTPUT, "Would you like to RESTART, RESTORE a saved game or QUIT?"),
        _block(BlockKind.COMMAND, "load nazimice", addressee="floyd"),
        _block(BlockKind.GAME_OUTPUT, "Please give one of the answers above."),
        _block(BlockKind.COMMAND, "quit", addressee="floyd"),
        _block(BlockKind.BOT_META, "That game over already? It was just getting good. Wanna play another?"),
        _block(BlockKind.COMMAND, "load nazimice", addressee="floyd"),
        _block(BlockKind.GAME_OUTPUT, "Welcome to the Cheap Glk Implementation, library version 8.0.6."),
        _block(BlockKind.GAME_OUTPUT, "Nazi Mice"),
    ]
    boundaries = segment.find_segment_boundaries(blocks)
    # Only the second "load nazimice" (index 6) is real; the first (index 2)
    # was rejected and must not double-count as its own segment.
    assert boundaries == [0, 6]


def test_rejected_load_attempt_across_a_pagination_pause_is_still_not_a_boundary():
    # Same as test_rejected_load_attempt_is_not_a_boundary, but the
    # rejection message arrives after a MORE-prompt pause -- the pause must
    # not stop the scan before it reaches the rejection marker.
    blocks = [
        _block(BlockKind.GAME_OUTPUT, "Would you like to RESTART, RESTORE a saved game or QUIT?"),
        _block(BlockKind.COMMAND, "load nazimice", addressee="floyd"),
        _block(BlockKind.PAGINATION, "maga pushes the green 'space' button.", speaker="maga"),
        _block(BlockKind.GAME_OUTPUT, "Please give one of the answers above."),
        _block(BlockKind.COMMAND, "quit", addressee="floyd"),
        _block(BlockKind.COMMAND, "load nazimice", addressee="floyd"),
        _block(BlockKind.GAME_OUTPUT, "Nazi Mice"),
    ]
    boundaries = segment.find_segment_boundaries(blocks)
    assert boundaries == [0, 5]


def test_load_command_as_last_block_with_no_following_output_is_still_treated_as_successful():
    # No following GAME_OUTPUT means _is_successful_load's scan finds no
    # rejection marker and defaults to "successful" -- exercised properly
    # via a load command that isn't at index 0.
    blocks = [
        _block(BlockKind.DISCUSSION, "chatter"),
        _block(BlockKind.COMMAND, "load thedayishothitler", addressee="floyd"),
    ]
    assert segment.find_segment_boundaries(blocks) == [0, 1]


def test_load_is_case_insensitive_and_matched_as_a_whole_word():
    blocks = [
        _block(BlockKind.DISCUSSION, "loaded question, don't you think?"),
        _block(BlockKind.COMMAND, "LOAD nazimice", addressee="floyd"),
    ]
    assert segment.find_segment_boundaries(blocks) == [0, 1]


# --- segment_transcript ---------------------------------------------------------------


def test_segment_transcript_single_segment_when_no_load():
    transcript = Transcript(
        source_id="x",
        blocks=[
            _block(BlockKind.DISCUSSION, "chatter"),
            _block(BlockKind.COMMAND, "x lamp"),
            _block(BlockKind.GAME_OUTPUT, "An oil-lamp."),
        ],
    )
    session = segment.segment_transcript(transcript)
    assert session.source_id == "x"
    assert len(session.segments) == 1
    only = session.segments[0]
    assert only.segment_index == 0
    assert only.start_block_index == 0
    assert only.end_block_index == 3
    assert only.start_command is None


def test_segment_transcript_splits_on_successful_load_and_keeps_midamble_with_previous_segment():
    transcript = Transcript(
        source_id="x",
        blocks=[
            _block(BlockKind.COMMAND, "load thedayishothitler", addressee="floyd"),  # 0
            _block(BlockKind.GAME_OUTPUT, "The Day I Shot Hitler"),  # 1
            _block(BlockKind.GAME_OUTPUT, "*** You have won ***"),  # 2
            _block(BlockKind.DISCUSSION, "Jacqueline hollers, next game announced"),  # 3 (midamble)
            _block(BlockKind.COMMAND, "load nazimice", addressee="floyd"),  # 4
            _block(BlockKind.GAME_OUTPUT, "Nazi Mice"),  # 5
        ],
    )
    session = segment.segment_transcript(transcript)
    assert [(s.start_block_index, s.end_block_index) for s in session.segments] == [(0, 4), (4, 6)]
    assert session.segments[0].start_command == "load thedayishothitler"
    assert session.segments[1].start_command == "load nazimice"
    # The midamble discussion (index 3) stays inside the first segment, not the second.
    assert session.segments[0].start_block_index <= 3 < session.segments[0].end_block_index


def test_segment_transcript_empty_blocks_is_empty_segments():
    session = segment.segment_transcript(Transcript(source_id="x", blocks=[]))
    assert session.segments == []


# --- segment_one / run orchestration --------------------------------------------------


def _record(source_id="20070901-nevermore", year=2007, status=ManifestStatus.NORMALIZED):
    return ManifestRecord(
        id=source_id,
        source_url=f"https://allthingsjacq.com/intfic_clubfloyd_{source_id}.html",
        year=year,
        games=[GameRef(title="Nevermore", author="Nate Cull")],
        raw_path="unused-placeholder",
        status=status,
    )


def _write_transcript(record, root, blocks):
    transcript = Transcript(source_id=record.id, blocks=blocks)
    json_path = paths.transcript_json_path(record.year, record.id, root)
    paths.ensure_parent(json_path).write_text(transcript.model_dump_json(), encoding="utf-8")
    return transcript


_SIMPLE_BLOCKS = [
    _block(BlockKind.COMMAND, "x lamp"),
    _block(BlockKind.GAME_OUTPUT, "An oil-lamp."),
]


def test_segment_one_writes_session_json(tmp_path):
    record = _record()
    _write_transcript(record, tmp_path, _SIMPLE_BLOCKS)

    result = segment.segment_one(record, root=tmp_path, force=False)

    assert result.action == "segmented"
    assert result.segment_count == 1
    session_path = paths.session_json_path(record.year, record.id, tmp_path)
    session = SessionSegments.model_validate_json(session_path.read_text(encoding="utf-8"))
    assert session.source_id == record.id


def test_segment_one_skips_existing_without_reparsing(tmp_path):
    record = _record()
    _write_transcript(record, tmp_path, _SIMPLE_BLOCKS)
    segment.segment_one(record, root=tmp_path, force=False)

    session_path = paths.session_json_path(record.year, record.id, tmp_path)
    sentinel = "SENTINEL - should not be overwritten"
    session_path.write_text(sentinel, encoding="utf-8")

    result = segment.segment_one(record, root=tmp_path, force=False)

    assert result.action == "skipped_exists"
    assert session_path.read_text(encoding="utf-8") == sentinel


def test_segment_one_force_reparses(tmp_path):
    record = _record()
    _write_transcript(record, tmp_path, _SIMPLE_BLOCKS)
    segment.segment_one(record, root=tmp_path, force=False)

    session_path = paths.session_json_path(record.year, record.id, tmp_path)
    session_path.write_text("SENTINEL", encoding="utf-8")

    result = segment.segment_one(record, root=tmp_path, force=True)

    assert result.action == "segmented"
    assert "SENTINEL" not in session_path.read_text(encoding="utf-8")


def test_segment_one_skips_missing_transcript(tmp_path):
    record = _record()
    result = segment.segment_one(record, root=tmp_path, force=False)
    assert result.action == "skipped_missing_transcript"
    assert not paths.session_json_path(record.year, record.id, tmp_path).exists()


def test_run_year_filter_only_touches_matching_records(tmp_path):
    record_2007 = _record(source_id="20070901-nevermore", year=2007)
    record_2025 = _record(source_id="20250101-no-more", year=2025)
    root = tmp_path / "data"
    _write_transcript(record_2007, root, _SIMPLE_BLOCKS)
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {record_2007.id: record_2007, record_2025.id: record_2025})

    args = SimpleNamespace(root=root, force=False, year=2007)
    segment.run(args)

    assert paths.session_json_path(record_2007.year, record_2007.id, root).exists()
    assert not paths.session_json_path(record_2025.year, record_2025.id, root).exists()


def test_run_no_manifest_records_prints_message_and_does_not_crash(tmp_path, capsys):
    args = SimpleNamespace(root=tmp_path, force=False, year=None)
    segment.run(args)
    assert "no records" in capsys.readouterr().out
