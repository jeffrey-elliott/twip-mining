"""Tests for normalize.py, keyed directly to the worked examples in
doc/club_floyd_transcript_classifier_examples.md (source: intfic_clubfloyd_20070901.html,
"Nevermore"). Each classification test names the doc section it covers.
"""
from pathlib import Path
from types import SimpleNamespace

from clubfloyd_mine import manifest as manifest_io, normalize, paths
from clubfloyd_mine.models import BlockKind, GameRef, ManifestRecord, ManifestStatus

FIXTURE = Path(__file__).parent / "fixtures" / "nevermore_sample.html"


def _classify(text):
    return normalize._classify_row(text)


# --- Positive examples: game input ------------------------------------------------


def test_simple_command_to_floyd():
    block = _classify('maga says (to floyd), "x lamp"')
    assert block.kind is BlockKind.COMMAND
    assert block.speaker == "maga"
    assert block.addressee == "floyd"
    assert block.text == "x lamp"


def test_another_examine_command():
    block = _classify('inky says (to Floyd), "x desk"')
    assert block.kind is BlockKind.COMMAND
    assert block.speaker == "inky"
    assert block.text == "x desk"


def test_inventory_shorthand():
    block = _classify('maga says (to floyd), "i"')
    assert block.kind is BlockKind.COMMAND
    assert block.text == "i"


def test_invalid_command_is_still_game_input():
    block = _classify('Bishop says (to floyd), "Snort coke"')
    assert block.kind is BlockKind.COMMAND
    assert block.speaker == "Bishop"
    assert block.text == "Snort coke"


def test_multiple_commands_in_one_utterance_preserved_whole():
    block = _classify('inky says (to Floyd), "open window. look behind curtains"')
    assert block.kind is BlockKind.COMMAND
    assert block.text == "open window. look behind curtains"


# --- Negative examples: not game input ---------------------------------------------


def test_general_setup_chatter_has_no_addressee():
    block = _classify('maga asks, "did we decide on Nevermore?"')
    assert block.kind is BlockKind.DISCUSSION
    assert block.speaker == "maga"
    assert block.addressee is None
    assert block.text == "did we decide on Nevermore?"


def test_session_coordination_is_chatter():
    block = _classify(
        'Jacqueline says, "We\'ll keep the commentary to the channel, and the game play here."'
    )
    assert block.kind is BlockKind.DISCUSSION


def test_hollers_extracts_speaker_like_says_and_asks():
    # Real example: club_floyd_midamble_annotated.png -- announcing the
    # next game. "hollers" isn't addressed to Floyd, so this is chatter,
    # but speaker attribution should still work like it does for says/asks.
    block = _classify('Jacqueline hollers, "Next game, Nazi Mice, starting at five past the hour!"')
    assert block.kind is BlockKind.DISCUSSION
    assert block.speaker == "Jacqueline"
    assert block.text == "Next game, Nazi Mice, starting at five past the hour!"
    assert block.speaker == "Jacqueline"


def test_player_arrival_is_mud_event_not_game_text():
    block = _classify("maga arrives, full of neither funk nor fun.")
    assert block.kind is BlockKind.DISCUSSION
    assert block.speaker is None
    assert block.text == "maga arrives, full of neither funk nor fun."


def test_channel_event_is_mud_metadata():
    block = _classify("* maga has added PerrySimm to the channel.")
    assert block.kind is BlockKind.DISCUSSION
    assert block.speaker is None


def test_command_looking_text_not_sent_to_floyd():
    block = _classify('Rob asks, "inventory?"')
    assert block.kind is BlockKind.DISCUSSION
    assert block.addressee is None


def test_thought_bubble_syntax_is_not_a_command():
    block = _classify("Rob . o O ( look behind couch. look under couch. search couch. )")
    assert block.kind is BlockKind.DISCUSSION
    assert block.speaker is None  # no says/asks verb, so no speaker is extracted


def test_command_sent_to_another_bot_is_not_game_input():
    block = _classify('Rob says (to alex), "touch couch"')
    assert block.kind is BlockKind.DISCUSSION
    assert block.speaker == "Rob"
    assert block.addressee == "alex"


def test_bare_command_looking_chatter_without_target():
    block = _classify('Rob says, "push button"')
    assert block.kind is BlockKind.DISCUSSION
    assert block.addressee is None


# --- Non-game Floyd-adjacent examples -----------------------------------------------


def test_whisper_is_mud_interaction_not_game_output():
    block = _classify('Gunther | You whisper "HELLO!!!" to Floyd.')
    assert block.kind is BlockKind.DISCUSSION


def test_floyd_whispers_via_other_players_prefix_is_not_game_output():
    block = _classify('Gunther | Floyd whispers, "Hi!"')
    assert block.kind is BlockKind.DISCUSSION


def test_instructional_line_with_wrong_prefix_is_not_game_output():
    block = _classify("Jacqueline | ..Floyd x me")
    assert block.kind is BlockKind.DISCUSSION


# --- Game output ---------------------------------------------------------------------


def test_game_output_banner_line_preserves_leading_space():
    block = _classify("Floyd | NEVERMORE")
    assert block.kind is BlockKind.GAME_OUTPUT
    assert block.text == " NEVERMORE"


def test_game_output_blank_line():
    block = _classify("Floyd |")
    assert block.kind is BlockKind.GAME_OUTPUT
    assert block.text == ""


def test_game_output_prompt_line():
    block = _classify("Floyd | >")
    assert block.kind is BlockKind.GAME_OUTPUT
    assert block.text == " >"


def test_game_output_case_insensitive_on_floyd():
    block = _classify("floyd | some text")
    assert block.kind is BlockKind.GAME_OUTPUT


def test_game_output_status_bar_bracket_line():
    # Real example: data/raw/2017/20170402-a-fly-on-the-wall-or-an-appositional-eye
    # -- the game's status bar/menu uses "Floyd ]", not "Floyd |".
    block = _classify("Floyd ] Soul Dancers Ballroom")
    assert block.kind is BlockKind.GAME_OUTPUT
    assert block.text == " Soul Dancers Ballroom"


def test_game_output_row_mixing_bracket_and_pipe_lines_stays_one_block():
    # Real example, same session: a single row bundles several "Floyd ]"
    # status-bar lines followed by "Floyd |" body text -- this used to fail
    # entirely (the whole row fell through to DISCUSSION) because the old
    # regex anchored against the whole row and required it to start with
    # "Floyd |" specifically.
    raw = "Floyd ] How to watch\nFloyd ] (page 1 of 1)\nFloyd |\nFloyd | In A Fly on the Wall..."
    block = _classify(raw)
    assert block.kind is BlockKind.GAME_OUTPUT
    assert block.text == " How to watch\n (page 1 of 1)\n\n In A Fly on the Wall..."


def test_game_output_row_with_one_non_matching_line_falls_through():
    # A row that mixes a recognized Floyd-prefixed line with something else
    # entirely isn't evidenced to be safe to reinterpret as one block, so it
    # should fall through to the existing discussion catch-all unchanged.
    raw = "Floyd | some text\nnot a floyd line"
    block = _classify(raw)
    assert block.kind is BlockKind.DISCUSSION


def test_game_output_row_with_blank_paragraph_break_line_stays_one_block():
    # Real example: data/raw/2007/20070903-fear -- a homogeneous multi-line
    # game_output row with a blank line between paragraphs used to fall
    # through entirely to DISCUSSION, because the blank line ("") doesn't
    # itself carry a "Floyd |" prefix and the old per-line check required
    # every line, blank or not, to match.
    raw = "Floyd | First paragraph.\nFloyd |\n\nFloyd | Second paragraph."
    block = _classify(raw)
    assert block.kind is BlockKind.GAME_OUTPUT
    assert block.text == " First paragraph.\n\n\n Second paragraph."


def test_game_output_cf_pipe_line():
    # Real example: the relay bot's name changes from "Floyd" to "CF"
    # starting around 2020 -- every session from 2020-2025 in this corpus
    # uses "CF |"/"CF ]" instead of "Floyd |"/"Floyd ]".
    block = _classify("CF | some text")
    assert block.kind is BlockKind.GAME_OUTPUT
    assert block.text == " some text"


def test_game_output_cf_bracket_status_bar_line():
    # Real example: data/raw/2023/20230403-nothing-could-be-further-from-the-truth
    block = _classify("CF ] Lab Hallway Outward")
    assert block.kind is BlockKind.GAME_OUTPUT
    assert block.text == " Lab Hallway Outward"


def test_game_output_cf_case_insensitive():
    block = _classify("cf | some text")
    assert block.kind is BlockKind.GAME_OUTPUT


def test_game_output_row_mixing_cf_and_non_cf_line_falls_through():
    # A row can't mix bot names and still be safely reinterpreted -- same
    # conservative fallthrough as the Floyd-only mixed case above.
    raw = "CF | some text\nnot a cf line"
    block = _classify(raw)
    assert block.kind is BlockKind.DISCUSSION


# --- Bot meta --------------------------------------------------------------------------


def test_bot_meta_with_addressee():
    block = _classify('Floyd says (to Gunther), "Floyd doesn\'t know that trick."')
    assert block.kind is BlockKind.BOT_META
    assert block.addressee == "Gunther"
    assert block.text == "Floyd doesn't know that trick."


def test_bot_meta_without_addressee():
    block = _classify(
        'Floyd asks, "That game over already?  It was just getting good.  Wanna play another?"'
    )
    assert block.kind is BlockKind.BOT_META
    assert block.addressee is None


# --- Full fixture parse ----------------------------------------------------------------


def test_parse_transcript_html_against_full_fixture():
    html = FIXTURE.read_text(encoding="utf-8")
    transcript = normalize.parse_transcript_html(html, source_id="20070901-nevermore")

    assert transcript.source_id == "20070901-nevermore"
    kinds = [b.kind for b in transcript.blocks]
    assert BlockKind.COMMAND in kinds
    assert BlockKind.GAME_OUTPUT in kinds
    assert BlockKind.BOT_META in kinds
    assert BlockKind.DISCUSSION in kinds

    # Nav table chrome must not leak into blocks.
    assert not any("nav placeholder" in b.text for b in transcript.blocks)

    # A command immediately followed by its game_output turn stays contiguous and ordered.
    lamp_index = next(i for i, b in enumerate(transcript.blocks) if b.text == "x lamp")
    assert transcript.blocks[lamp_index].kind is BlockKind.COMMAND
    assert transcript.blocks[lamp_index + 1].kind is BlockKind.GAME_OUTPUT


def test_render_transcript_txt_formats_each_kind():
    html = FIXTURE.read_text(encoding="utf-8")
    transcript = normalize.parse_transcript_html(html, source_id="x")
    text = normalize.render_transcript_txt(transcript)

    assert "maga > x lamp" in text
    assert "Floyd (to Gunther): Floyd doesn't know that trick." in text
    assert "An oil-lamp of copper and glass" in text  # bare game_output, no prefix


# --- normalize_one / run orchestration --------------------------------------------------


def _record(source_id="20070901-nevermore", year=2007, status=ManifestStatus.FETCHED):
    return ManifestRecord(
        id=source_id,
        source_url=f"https://allthingsjacq.com/intfic_clubfloyd_{source_id}.html",
        year=year,
        games=[GameRef(title="Nevermore", author="Nate Cull")],
        raw_path="unused-placeholder",
        status=status,
    )


def test_normalize_one_writes_txt_and_json(tmp_path):
    record = _record()
    raw_path = paths.raw_html_path(record.year, record.id, tmp_path)
    paths.ensure_parent(raw_path).write_bytes(FIXTURE.read_bytes())

    result = normalize.normalize_one(record, root=tmp_path, force=False)

    assert result.action == "normalized"
    txt_path = paths.transcript_txt_path(record.year, record.id, tmp_path)
    json_path = paths.transcript_json_path(record.year, record.id, tmp_path)
    assert "x lamp" in txt_path.read_text(encoding="utf-8")
    assert json_path.exists()


def test_normalize_one_skips_existing_without_reparsing(tmp_path):
    record = _record()
    raw_path = paths.raw_html_path(record.year, record.id, tmp_path)
    paths.ensure_parent(raw_path).write_bytes(FIXTURE.read_bytes())
    normalize.normalize_one(record, root=tmp_path, force=False)

    txt_path = paths.transcript_txt_path(record.year, record.id, tmp_path)
    sentinel = "SENTINEL - should not be overwritten"
    txt_path.write_text(sentinel, encoding="utf-8")

    result = normalize.normalize_one(record, root=tmp_path, force=False)

    assert result.action == "skipped_exists"
    assert txt_path.read_text(encoding="utf-8") == sentinel


def test_normalize_one_force_reparses(tmp_path):
    record = _record()
    raw_path = paths.raw_html_path(record.year, record.id, tmp_path)
    paths.ensure_parent(raw_path).write_bytes(FIXTURE.read_bytes())
    normalize.normalize_one(record, root=tmp_path, force=False)

    txt_path = paths.transcript_txt_path(record.year, record.id, tmp_path)
    txt_path.write_text("SENTINEL", encoding="utf-8")

    result = normalize.normalize_one(record, root=tmp_path, force=True)

    assert result.action == "normalized"
    assert "x lamp" in txt_path.read_text(encoding="utf-8")


def test_normalize_one_skips_missing_raw(tmp_path):
    record = _record()
    result = normalize.normalize_one(record, root=tmp_path, force=False)
    assert result.action == "skipped_missing_raw"
    assert not paths.transcript_txt_path(record.year, record.id, tmp_path).exists()


def test_run_advances_manifest_status(tmp_path):
    record = _record(status=ManifestStatus.FETCHED)
    root = tmp_path / "data"
    raw_path = paths.raw_html_path(record.year, record.id, root)
    paths.ensure_parent(raw_path).write_bytes(FIXTURE.read_bytes())
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {record.id: record})

    args = SimpleNamespace(root=root, force=False)
    normalize.run(args)

    updated = manifest_io.load_manifest(manifest_file)
    assert updated[record.id].status is ManifestStatus.NORMALIZED


def test_run_year_filter_only_touches_matching_records(tmp_path):
    record_2007 = _record(source_id="20070901-nevermore", year=2007, status=ManifestStatus.FETCHED)
    record_2025 = _record(source_id="20250101-no-more", year=2025, status=ManifestStatus.FETCHED)
    root = tmp_path / "data"
    paths.ensure_parent(paths.raw_html_path(record_2007.year, record_2007.id, root)).write_bytes(
        FIXTURE.read_bytes()
    )
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {record_2007.id: record_2007, record_2025.id: record_2025})

    args = SimpleNamespace(root=root, force=False, year=2007)
    normalize.run(args)

    updated = manifest_io.load_manifest(manifest_file)
    assert updated[record_2007.id].status is ManifestStatus.NORMALIZED
    assert updated[record_2025.id].status is ManifestStatus.FETCHED  # untouched
    assert not paths.transcript_json_path(record_2025.year, record_2025.id, root).exists()


def test_run_leaves_status_alone_when_raw_missing(tmp_path):
    record = _record(status=ManifestStatus.DISCOVERED)
    root = tmp_path / "data"
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {record.id: record})

    args = SimpleNamespace(root=root, force=False)
    normalize.run(args)

    updated = manifest_io.load_manifest(manifest_file)
    assert updated[record.id].status is ManifestStatus.DISCOVERED
