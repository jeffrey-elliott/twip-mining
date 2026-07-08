"""Tests for classify.classify_pair_rule, the deterministic "obvious case"
tier described in doc/pipeline/05_classify_outcomes.md."""
from pathlib import Path

from clubfloyd_mine import classify, extract_pairs, normalize
from clubfloyd_mine.models import BlockKind, CommandPair, OutcomeBucket, TranscriptBlock

FIXTURE = Path(__file__).parent / "fixtures" / "nevermore_sample.html"


def _pair(*result_texts, command_text="look"):
    return CommandPair(
        source_id="x",
        pair_index=0,
        command_text=command_text,
        result_blocks=[TranscriptBlock(kind=BlockKind.GAME_OUTPUT, text=t) for t in result_texts],
    )


# --- obvious failure ---------------------------------------------------------------


def test_cant_see_any_such_thing_is_obvious_failure():
    pair = _pair(" You can't see any such thing.", "", " >")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_cant_go_that_way_is_obvious_failure():
    pair = _pair(" You can't go that way.")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_verb_not_recognised_is_obvious_failure():
    pair = _pair(" That's not a verb I recognise.")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_verb_not_recognized_american_spelling_is_obvious_failure():
    pair = _pair(" That's not a verb I recognize.")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_failure_message_after_a_synonym_substitution_line_is_still_detected():
    # Real transcript shape: a "[verb -> synonym]" notice line precedes the
    # actual failure message, so the rule must not only look at line one.
    pair = _pair(" [snort -> short]", " I only understood you as far as wanting to short.", "", " >")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_failure_takes_priority_over_a_coincidental_success_line():
    pair = _pair(" That noun did not make sense in this context.", " Ok.")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


# --- obvious success ----------------------------------------------------------------


def test_taken_is_obvious_success():
    pair = _pair(" Taken.", "", " >")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_dropped_is_obvious_success():
    pair = _pair(" Dropped.")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_success_confirmation_after_a_synonym_notice_is_still_detected():
    pair = _pair(" [grab -> take]", " Taken.", "", " >")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


# --- uncertain (no confident rule match) ---------------------------------------------


def test_no_result_blocks_is_uncertain():
    pair = _pair()
    assert classify.classify_pair_rule(pair) is None


def test_blank_only_result_is_uncertain():
    pair = _pair("", " >")
    assert classify.classify_pair_rule(pair) is None


def test_rich_descriptive_output_is_uncertain():
    pair = _pair(
        " An oil-lamp of copper and glass, warm to the touch and old as time.",
        " Like the desk it is a family heirloom.",
    )
    assert classify.classify_pair_rule(pair) is None


def test_game_specific_reimplemented_failure_message_is_uncertain():
    # Lost Pig's Grunk-voiced parser failure -- deliberately not hardcoded,
    # see the module docstring.
    pair = _pair(" Grunk not know what that mean.")
    assert classify.classify_pair_rule(pair) is None


# --- against the real Nevermore fixture ----------------------------------------------


def test_against_full_fixture_snort_coke_is_obvious_failure():
    html = FIXTURE.read_text(encoding="utf-8")
    transcript = normalize.parse_transcript_html(html, source_id="20070901-nevermore")
    pairs = extract_pairs.extract_pairs(transcript)

    snort_pair = next(p for p in pairs if p.command_text == "Snort coke")
    assert classify.classify_pair_rule(snort_pair) is OutcomeBucket.PARSER_FAILURE

    lamp_pair = next(p for p in pairs if p.command_text == "x lamp")
    assert classify.classify_pair_rule(lamp_pair) is None  # rich descriptive text, uncertain
