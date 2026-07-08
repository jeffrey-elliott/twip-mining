"""Tests for extract_pairs.py, keyed to doc/pipeline/04_pair_commands_to_results.md
and the pairing heuristic in doc/club_floyd_transcript_classifier_examples.md."""
from pathlib import Path
from types import SimpleNamespace

from clubfloyd_mine import extract_pairs, manifest as manifest_io, normalize, paths
from clubfloyd_mine.models import (
    BlockKind,
    CommandPair,
    GameRef,
    ManifestRecord,
    ManifestStatus,
    Transcript,
    TranscriptBlock,
)

FIXTURE = Path(__file__).parent / "fixtures" / "nevermore_sample.html"


def _block(kind, text, speaker=None, addressee=None):
    return TranscriptBlock(kind=kind, speaker=speaker, addressee=addressee, text=text)


# --- extract_pairs() unit tests on synthetic block lists ---------------------------


def test_command_followed_by_output_is_paired():
    transcript = Transcript(
        source_id="x",
        blocks=[
            _block(BlockKind.COMMAND, "x lamp", speaker="maga", addressee="floyd"),
            _block(BlockKind.GAME_OUTPUT, "An oil-lamp of copper and glass."),
            _block(BlockKind.GAME_OUTPUT, ">"),
        ],
    )
    pairs = extract_pairs.extract_pairs(transcript)
    assert len(pairs) == 1
    pair = pairs[0]
    assert pair.source_id == "x"
    assert pair.pair_index == 0
    assert pair.speaker == "maga"
    assert pair.addressee == "floyd"
    assert pair.command_text == "x lamp"
    assert [b.text for b in pair.result_blocks] == ["An oil-lamp of copper and glass.", ">"]


def test_result_run_stops_at_first_non_game_output_block():
    transcript = Transcript(
        source_id="x",
        blocks=[
            _block(BlockKind.COMMAND, "x lamp", speaker="maga"),
            _block(BlockKind.GAME_OUTPUT, "An oil-lamp."),
            _block(BlockKind.DISCUSSION, "nice one maga", speaker="Rob"),
            _block(BlockKind.GAME_OUTPUT, "stray output that belongs to no command"),
        ],
    )
    pairs = extract_pairs.extract_pairs(transcript)
    assert len(pairs) == 1
    assert [b.text for b in pairs[0].result_blocks] == ["An oil-lamp."]


def test_command_with_no_following_output_still_produces_a_pair():
    transcript = Transcript(
        source_id="x",
        blocks=[
            _block(BlockKind.COMMAND, "Snort coke", speaker="Bishop"),
            _block(BlockKind.COMMAND, "x lamp", speaker="maga"),
        ],
    )
    pairs = extract_pairs.extract_pairs(transcript)
    assert len(pairs) == 2
    assert pairs[0].command_text == "Snort coke"
    assert pairs[0].result_blocks == []
    assert pairs[1].command_text == "x lamp"
    assert pairs[1].pair_index == 1


def test_bot_meta_does_not_extend_a_result_run():
    transcript = Transcript(
        source_id="x",
        blocks=[
            _block(BlockKind.COMMAND, "i", speaker="maga"),
            _block(BlockKind.GAME_OUTPUT, "You are carrying:"),
            _block(BlockKind.BOT_META, "Floyd doesn't know that trick.", addressee="Gunther"),
            _block(BlockKind.GAME_OUTPUT, "unrelated later output"),
        ],
    )
    pairs = extract_pairs.extract_pairs(transcript)
    assert len(pairs) == 1
    assert [b.text for b in pairs[0].result_blocks] == ["You are carrying:"]


def test_non_command_blocks_with_no_preceding_command_are_ignored():
    transcript = Transcript(
        source_id="x",
        blocks=[
            _block(BlockKind.DISCUSSION, "did we decide on Nevermore?", speaker="maga"),
            _block(BlockKind.GAME_OUTPUT, "NEVERMORE"),
        ],
    )
    pairs = extract_pairs.extract_pairs(transcript)
    assert pairs == []


def test_pair_index_increments_across_multiple_commands():
    transcript = Transcript(
        source_id="x",
        blocks=[
            _block(BlockKind.COMMAND, "x lamp", speaker="maga"),
            _block(BlockKind.GAME_OUTPUT, "An oil-lamp."),
            _block(BlockKind.COMMAND, "x desk", speaker="inky"),
            _block(BlockKind.GAME_OUTPUT, "A writing desk."),
        ],
    )
    pairs = extract_pairs.extract_pairs(transcript)
    assert [p.pair_index for p in pairs] == [0, 1]
    assert [p.command_text for p in pairs] == ["x lamp", "x desk"]


# --- Full fixture integration: normalize then extract -------------------------------


def test_extract_pairs_against_full_fixture():
    html = FIXTURE.read_text(encoding="utf-8")
    transcript = normalize.parse_transcript_html(html, source_id="20070901-nevermore")
    pairs = extract_pairs.extract_pairs(transcript)

    assert pairs, "expected at least one command/result pair from the fixture"
    lamp_pair = next(p for p in pairs if p.command_text == "x lamp")
    assert lamp_pair.speaker == "maga"
    assert lamp_pair.result_blocks, "x lamp should have game_output attached"
    assert all(b.kind is BlockKind.GAME_OUTPUT for b in lamp_pair.result_blocks)

    # Every command in the transcript produces a pair, even ones the parser rejects.
    command_texts = [b.text for b in transcript.blocks if b.kind is BlockKind.COMMAND]
    assert [p.command_text for p in pairs] == command_texts


# --- extract_pairs_one / run orchestration ------------------------------------------


def _record(source_id="20070901-nevermore", year=2007, status=ManifestStatus.NORMALIZED):
    return ManifestRecord(
        id=source_id,
        source_url=f"https://allthingsjacq.com/intfic_clubfloyd_{source_id}.html",
        year=year,
        games=[GameRef(title="Nevermore", author="Nate Cull")],
        raw_path="unused-placeholder",
        status=status,
    )


def _write_transcript(record, root):
    html = FIXTURE.read_text(encoding="utf-8")
    transcript = normalize.parse_transcript_html(html, source_id=record.id)
    json_path = paths.transcript_json_path(record.year, record.id, root)
    paths.ensure_parent(json_path).write_text(transcript.model_dump_json(), encoding="utf-8")
    return transcript


def test_extract_pairs_one_writes_jsonl(tmp_path):
    record = _record()
    _write_transcript(record, tmp_path)

    result = extract_pairs.extract_pairs_one(record, root=tmp_path, force=False)

    assert result.action == "extracted"
    assert result.pair_count > 0
    pairs_path = paths.command_pairs_path(record.year, record.id, tmp_path)
    lines = pairs_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == result.pair_count
    first_pair = CommandPair.model_validate_json(lines[0])
    assert first_pair.source_id == record.id


def test_extract_pairs_one_skips_existing_without_reparsing(tmp_path):
    record = _record()
    _write_transcript(record, tmp_path)
    extract_pairs.extract_pairs_one(record, root=tmp_path, force=False)

    pairs_path = paths.command_pairs_path(record.year, record.id, tmp_path)
    sentinel = "SENTINEL - should not be overwritten"
    pairs_path.write_text(sentinel, encoding="utf-8")

    result = extract_pairs.extract_pairs_one(record, root=tmp_path, force=False)

    assert result.action == "skipped_exists"
    assert pairs_path.read_text(encoding="utf-8") == sentinel


def test_extract_pairs_one_force_reparses(tmp_path):
    record = _record()
    _write_transcript(record, tmp_path)
    extract_pairs.extract_pairs_one(record, root=tmp_path, force=False)

    pairs_path = paths.command_pairs_path(record.year, record.id, tmp_path)
    pairs_path.write_text("SENTINEL", encoding="utf-8")

    result = extract_pairs.extract_pairs_one(record, root=tmp_path, force=True)

    assert result.action == "extracted"
    assert "SENTINEL" not in pairs_path.read_text(encoding="utf-8")


def test_extract_pairs_one_skips_missing_transcript(tmp_path):
    record = _record()
    result = extract_pairs.extract_pairs_one(record, root=tmp_path, force=False)
    assert result.action == "skipped_missing_transcript"
    assert not paths.command_pairs_path(record.year, record.id, tmp_path).exists()


def test_run_advances_manifest_status(tmp_path):
    record = _record(status=ManifestStatus.NORMALIZED)
    root = tmp_path / "data"
    _write_transcript(record, root)
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {record.id: record})

    args = SimpleNamespace(root=root, force=False)
    extract_pairs.run(args)

    updated = manifest_io.load_manifest(manifest_file)
    assert updated[record.id].status is ManifestStatus.PARSED


def test_run_leaves_status_alone_when_transcript_missing(tmp_path):
    record = _record(status=ManifestStatus.FETCHED)
    root = tmp_path / "data"
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {record.id: record})

    args = SimpleNamespace(root=root, force=False)
    extract_pairs.run(args)

    updated = manifest_io.load_manifest(manifest_file)
    assert updated[record.id].status is ManifestStatus.FETCHED
