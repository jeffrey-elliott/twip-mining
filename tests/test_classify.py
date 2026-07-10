"""Tests for classify.classify_pair_rule (the deterministic "obvious case"
tier) and classify.classify_pair_llm (the LLM tier for a sample of
uncertain pairs), both described in doc/pipeline/05_classify_outcomes.md."""
import json
from pathlib import Path

import pytest

from clubfloyd_mine import classify, extract_pairs, normalize
from clubfloyd_mine.models import (
    BlockKind,
    ClassificationSource,
    CommandPair,
    OutcomeBucket,
    TranscriptBlock,
)

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


def test_opened_is_obvious_success():
    pair = _pair(" Opened.", "", " >")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_ok_is_obvious_success():
    pair = _pair(" Ok.")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_you_are_carrying_is_obvious_success_not_inventory_change():
    # A listing is observational, not a mutation -- see inventory.md.
    pair = _pair(" You are carrying:", " a brass lamp", " a rusty key", command_text="i")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_find_nothing_of_interest_is_obvious_success():
    pair = _pair(" You find nothing of interest.", command_text="search desk")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_you_open_the_object_sentence_is_success():
    # Real Nevermore transcript wording (pair #119): a full-sentence
    # confirmation with the object's name embedded, distinct from the
    # terse invariant "Opened." already in _OBVIOUS_SUCCESS_LINES.
    pair = _pair(" You open the wooden door.", command_text="open door")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_you_unlock_the_object_sentence_is_success():
    # Real Nevermore transcript wording (pair #117).
    pair = _pair(" You unlock the wooden door.", command_text="unlock door with key")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


# --- inventory change ----------------------------------------------------------------


def test_taken_is_inventory_change():
    pair = _pair(" Taken.", "", " >", command_text="take lamp")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.INVENTORY_CHANGE


def test_dropped_is_inventory_change():
    pair = _pair(" Dropped.", command_text="drop lamp")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.INVENTORY_CHANGE


def test_inventory_change_confirmation_after_a_synonym_notice_is_still_detected():
    pair = _pair(" [grab -> take]", " Taken.", "", " >", command_text="grab lamp")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.INVENTORY_CHANGE


def test_removed_suffix_is_inventory_change():
    # take.md's bulk-take confirmation format: "<item>: Removed."
    pair = _pair(" peyote button: Removed.", " opium pipe: Removed.", command_text="take all from pallas")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.INVENTORY_CHANGE


# --- world failure (understood, but refused for a world-state reason) ----------------


def test_already_have_that_is_world_failure_not_parser_failure():
    pair = _pair(" You already have that.", command_text="take lamp")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_dont_have_that_is_world_failure():
    pair = _pair(" You don't have that.", command_text="drop lamp")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_dont_have_the_key_is_world_failure():
    pair = _pair(" You don't have the key.", command_text="unlock door with key")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_already_open_is_world_failure():
    pair = _pair(" That's already open.", command_text="open door")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_locked_is_world_failure():
    pair = _pair(" It is locked.", command_text="open door")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_blocked_movement_is_world_failure():
    pair = _pair(" The way is blocked.", command_text="north")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_it_seems_to_be_locked_is_world_failure():
    # Real Nevermore transcript wording (pair #116), distinct from the
    # already-covered "it is locked." -- see solvable_blocked_action.md.
    pair = _pair(" It seems to be locked.", command_text="open door")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_blocked_move_with_variable_object_name_is_world_failure_not_location_change():
    # Real Nevermore transcript wording (pairs #115/#118): "the wooden door
    # is closed" doesn't start with the door.md-documented "the door is
    # closed" prefix, so this only matches via _WORLD_FAILURE_SUBSTRINGS.
    # Before that fix, this fell through to the _MOVEMENT_COMMANDS fallback
    # and was wrongly classified as location_change.
    pair = _pair(" The wooden door is closed, and bars your way.", command_text="e")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_world_failure_takes_priority_over_parser_failure_list():
    # "you can't take that" (parser_failure) and "already have that"
    # (world_failure) are different phrases; make sure adding the
    # world_failure tier didn't disturb the parser_failure one.
    pair = _pair(" You can't take that.", command_text="take wall")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


# --- disambiguation --------------------------------------------------------------------


def test_which_do_you_mean_is_disambiguation():
    pair = _pair(" Which do you mean, the opium resin or the opium pipe?", command_text="x opium")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.DISAMBIGUATION


def test_too_many_matching_objects_is_disambiguation():
    pair = _pair(
        " There are far too many books to remove them all. You should select a",
        " volume by name.",
        command_text="take books",
    )
    assert classify.classify_pair_rule(pair) is OutcomeBucket.DISAMBIGUATION


# --- score or end state ------------------------------------------------------------------


def test_death_marker_is_score_or_end_state():
    pair = _pair(" *** You have died ***", " ", command_text="out")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SCORE_OR_END_STATE


def test_game_over_is_score_or_end_state():
    pair = _pair(" Game over.", command_text="jump")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SCORE_OR_END_STATE


def test_bare_the_end_as_a_full_line_is_score_or_end_state():
    pair = _pair(" The End", command_text="wait")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SCORE_OR_END_STATE


def test_the_end_as_a_prefix_of_ordinary_prose_is_not_score_or_end_state():
    # "the end" is deliberately exact-line-only, not a prefix, since prose
    # like this is a plausible false positive for SCORE_OR_END_STATE. It
    # still resolves to SUCCESS, not None: "look" falls to the
    # examine/look command fallback below once score/end-state has been
    # ruled out, per look_or_examine.md's "any prose back is a successful
    # look" rule.
    pair = _pair(" The end of the hallway fades into darkness.", command_text="look")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


# --- command-based: meta_or_floyd_control -----------------------------------------------


def test_about_command_is_meta_or_floyd_control():
    pair = _pair(" NEVERMORE is a work of Interactive Fiction by Nate Cull.", command_text="about")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.META_OR_FLOYD_CONTROL


def test_hint_command_is_meta_or_floyd_control():
    pair = _pair(" Nevermore Hints", " N = next subject", command_text="hint")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.META_OR_FLOYD_CONTROL


def test_meta_command_result_text_rule_still_wins_over_command_based_fallback():
    # A world_failure/etc. phrase in the result should take priority over
    # the plain command-based meta fallback.
    pair = _pair(" You already have that.", command_text="about")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.WORLD_FAILURE


def test_quit_command_alone_is_not_meta_or_floyd_control():
    # meta_quit.md: don't assume every "q"/"quit" is a real quit without a
    # result-text confirmation prompt.
    pair = _pair(" Study (on the velvet couch)", command_text="quit")
    assert classify.classify_pair_rule(pair) is None


def test_xyzzy_is_not_auto_classified():
    # xyzzy.md: response is too game-specific to bucket by verb alone.
    pair = _pair(" The name of old, lost magic briefly echoes, then is gone.", command_text="xyzzy")
    assert classify.classify_pair_rule(pair) is None


def test_again_is_not_auto_classified():
    # again.md: outcome depends on resolving the prior command.
    pair = _pair(" An oil-lamp of copper and glass, warm to the touch.", command_text="g")
    assert classify.classify_pair_rule(pair) is None


# --- command-based: location_change -----------------------------------------------------


def test_successful_direction_command_is_location_change():
    pair = _pair(" Hallway", " A dim, narrow hallway leads north and south.", command_text="north")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.LOCATION_CHANGE


def test_abbreviated_direction_command_is_location_change():
    pair = _pair(" Hallway", " A dim, narrow hallway leads north and south.", command_text="n")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.LOCATION_CHANGE


# --- command-based: examine/look (prose with no failure phrase = success) --------------


def test_examine_self_with_prose_is_success():
    # The exact case this was raised against: "x me" -> descriptive prose,
    # no failure phrase anywhere in it.
    pair = _pair(
        " You look like a gentleman of ease, but that is not how you feel.",
        " A staccato rap echoes through the room.",
        " The coca rush fades, but the sense of alertness remains.",
        command_text="x me",
    )
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_examine_object_with_prose_is_success():
    pair = _pair(" A thin paper envelope, of the kind in which exotic substances are stored.", command_text="examine sachet")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_look_at_object_with_prose_is_success():
    pair = _pair(" A relic from Byzantine days, perhaps.", command_text="look at desk")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_bare_look_with_room_description_is_success():
    pair = _pair(" Gallery", " The dust of ages clings to crooked stone walls.", command_text="look")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_abbreviated_look_with_room_description_is_success():
    pair = _pair(" Gallery", " The dust of ages clings to crooked stone walls.", command_text="l")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_examine_target_not_found_is_parser_failure_not_success():
    pair = _pair(" You can't see any such thing.", command_text="x unicorn")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_examine_i_cant_find_that_is_parser_failure():
    pair = _pair(" I can't find that.", command_text="x unicorn")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_examine_thats_not_here_is_parser_failure():
    pair = _pair(" That's not here.", command_text="x unicorn")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_go_phrase_command_is_location_change():
    pair = _pair(" You go through the door.", command_text="go through door")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.LOCATION_CHANGE


def test_blocked_direction_command_is_world_failure_not_location_change():
    pair = _pair(" You can't go that way.", command_text="north")
    assert classify.classify_pair_rule(pair) is OutcomeBucket.PARSER_FAILURE


def test_direction_command_with_no_result_is_uncertain():
    pair = _pair(command_text="north")
    assert classify.classify_pair_rule(pair) is None


# --- uncertain (no confident rule match) ---------------------------------------------


def test_no_result_blocks_is_uncertain():
    pair = _pair()
    assert classify.classify_pair_rule(pair) is None


def test_blank_only_result_is_uncertain():
    pair = _pair("", " >")
    assert classify.classify_pair_rule(pair) is None


def test_rich_descriptive_output_for_look_is_success_not_uncertain():
    # look_or_examine.md: for look/examine, prose with no failure phrase
    # *is* the successful result, not merely "uncertain" -- see the module
    # docstring's note on _EXAMINE_OR_LOOK_COMMANDS.
    pair = _pair(
        " An oil-lamp of copper and glass, warm to the touch and old as time.",
        " Like the desk it is a family heirloom.",
    )
    assert classify.classify_pair_rule(pair) is OutcomeBucket.SUCCESS


def test_rich_descriptive_output_for_a_non_examine_verb_is_still_uncertain():
    # The "prose with no failure phrase = success" shortcut is deliberately
    # scoped to _EXAMINE_OR_LOOK_COMMANDS only. A manipulation verb with no
    # rule coverage at all still can't be told apart from a custom failure
    # message, so it stays uncertain.
    pair = _pair(
        " The idol wobbles unsteadily but does not fall.",
        command_text="push idol",
    )
    assert classify.classify_pair_rule(pair) is None


def test_game_specific_reimplemented_failure_message_is_uncertain():
    # Lost Pig's Grunk-voiced parser failure -- deliberately not hardcoded,
    # see the module docstring. Uses a command outside
    # _EXAMINE_OR_LOOK_COMMANDS on purpose: this message could plausibly
    # follow *any* unrecognized command, and the module docstring already
    # documents that a game reimplementing this specifically for x/examine
    # is an accepted, undetectable blind spot of that fallback -- this test
    # covers the general case, not that specific tradeoff.
    pair = _pair(" Grunk not know what that mean.", command_text="pray")
    assert classify.classify_pair_rule(pair) is None


# --- against the real Nevermore fixture ----------------------------------------------


def test_against_full_fixture_snort_coke_is_obvious_failure():
    html = FIXTURE.read_text(encoding="utf-8")
    transcript = normalize.parse_transcript_html(html, source_id="20070901-nevermore")
    pairs = extract_pairs.extract_pairs(transcript)

    snort_pair = next(p for p in pairs if p.command_text == "Snort coke")
    assert classify.classify_pair_rule(snort_pair) is OutcomeBucket.PARSER_FAILURE

    lamp_pair = next(p for p in pairs if p.command_text == "x lamp")
    # rich descriptive text following "x lamp" -- successful examine, not
    # uncertain, per _EXAMINE_OR_LOOK_COMMANDS.
    assert classify.classify_pair_rule(lamp_pair) is OutcomeBucket.SUCCESS


# --- LLM tier: classify_pair_llm / provenance verification --------------------------


def _uncertain_pair(*result_texts, command_text="push idol", source_id="src", pair_index=0):
    pair = _pair(*result_texts, command_text=command_text)
    pair = pair.model_copy(update={"source_id": source_id, "pair_index": pair_index})
    assert classify.classify_pair_rule(pair) is None  # sanity: must be a real uncertain case
    return pair


def _fake_call(response: dict):
    """Build an LlmCallable that ignores the prompt and always returns the given response."""
    return lambda prompt: json.dumps(response)


def test_classify_pair_llm_happy_path_returns_classified_pair_with_evidence():
    pair = _uncertain_pair(" An oil-lamp of copper and glass, warm to the touch.")
    call = _fake_call(
        {
            "outcome": "success",
            "confidence": 0.82,
            "evidence": ["An oil-lamp of copper and glass"],
            "rationale": "The description confirms the object was examined.",
        }
    )
    result = classify.classify_pair_llm(pair, call)
    assert result.source_id == "src"
    assert result.pair_index == 0
    assert result.outcome is OutcomeBucket.SUCCESS
    assert result.confidence == 0.82
    assert result.classifier is ClassificationSource.LLM
    assert result.evidence == ["An oil-lamp of copper and glass"]
    assert result.notes == "The description confirms the object was examined."


def test_classify_pair_llm_rejects_response_missing_from_json():
    pair = _uncertain_pair(" An oil-lamp of copper and glass, warm to the touch.")
    call = lambda prompt: "not json at all"
    with pytest.raises(classify.LlmProvenanceError):
        classify.classify_pair_llm(pair, call)


def test_classify_pair_llm_rejects_invalid_outcome_bucket():
    pair = _uncertain_pair(" An oil-lamp of copper and glass, warm to the touch.")
    call = _fake_call({"outcome": "not_a_real_bucket", "confidence": 0.9, "evidence": ["oil-lamp"]})
    with pytest.raises(classify.LlmProvenanceError):
        classify.classify_pair_llm(pair, call)


def test_classify_pair_llm_rejects_confidence_out_of_range():
    pair = _uncertain_pair(" An oil-lamp of copper and glass, warm to the touch.")
    call = _fake_call({"outcome": "success", "confidence": 1.5, "evidence": ["oil-lamp"]})
    with pytest.raises(classify.LlmProvenanceError):
        classify.classify_pair_llm(pair, call)


def test_classify_pair_llm_rejects_missing_evidence():
    pair = _uncertain_pair(" An oil-lamp of copper and glass, warm to the touch.")
    call = _fake_call({"outcome": "success", "confidence": 0.9, "evidence": []})
    with pytest.raises(classify.LlmProvenanceError):
        classify.classify_pair_llm(pair, call)


def test_classify_pair_llm_rejects_hallucinated_evidence_not_in_source_text():
    # This is the core provenance guarantee: even a well-formed, confident
    # response must be discarded if its evidence can't be verified against
    # the pair's actual result text.
    pair = _uncertain_pair(" An oil-lamp of copper and glass, warm to the touch.")
    call = _fake_call(
        {
            "outcome": "success",
            "confidence": 0.95,
            "evidence": ["The door creaks open slowly"],  # not present in this pair's result text
        }
    )
    with pytest.raises(classify.LlmProvenanceError):
        classify.classify_pair_llm(pair, call)


def test_classify_pair_llm_rejects_blank_evidence_strings():
    pair = _uncertain_pair("")  # empty result text
    call = _fake_call({"outcome": "unknown", "confidence": 0.5, "evidence": [""]})
    with pytest.raises(classify.LlmProvenanceError):
        classify.classify_pair_llm(pair, call)


# --- LLM tier: sample_uncertain_pairs ------------------------------------------------


def test_sample_uncertain_pairs_excludes_already_rule_classified_pairs():
    obvious = _pair(" Taken.")  # rule-classified as INVENTORY_CHANGE
    # "push idol", not "x idol": _EXAMINE_OR_LOOK_COMMANDS would make this
    # pair rule-classified too, defeating the point of this test.
    uncertain = _pair(" The idol wobbles unsteadily but does not fall.", command_text="push idol")
    sampled = classify.sample_uncertain_pairs([obvious, uncertain], sample_size=10)
    assert sampled == [uncertain]


def test_sample_uncertain_pairs_returns_all_when_sample_size_covers_them():
    pairs = [
        _pair(" A red door.", command_text="push door"),
        _pair(" A blue door.", command_text="push other door"),
    ]
    sampled = classify.sample_uncertain_pairs(pairs, sample_size=10)
    assert set(id(p) for p in sampled) == set(id(p) for p in pairs)


def test_sample_uncertain_pairs_is_deterministic_for_a_fixed_seed():
    pairs = [
        _pair(f" description of item {i}.", command_text=f"push item{i}") for i in range(10)
    ]
    first = classify.sample_uncertain_pairs(pairs, sample_size=3, seed=42)
    second = classify.sample_uncertain_pairs(pairs, sample_size=3, seed=42)
    assert first == second
    assert len(first) == 3


# --- LLM tier: build_llm_prompt / parse_llm_response ---------------------------------


def test_build_llm_prompt_includes_command_and_result_text():
    pair = _uncertain_pair(" An oil-lamp of copper and glass, warm to the touch.")
    prompt = classify.build_llm_prompt(pair)
    assert "push idol" in prompt
    assert "An oil-lamp of copper and glass, warm to the touch." in prompt
    for bucket in OutcomeBucket:
        assert bucket.value in prompt


def test_parse_llm_response_accepts_well_formed_json():
    raw = json.dumps({"outcome": "world_failure", "confidence": 0.4, "evidence": ["can't do that"]})
    parsed = classify.parse_llm_response(raw)
    assert parsed["outcome"] is OutcomeBucket.WORLD_FAILURE
    assert parsed["confidence"] == 0.4
    assert parsed["evidence"] == ["can't do that"]
