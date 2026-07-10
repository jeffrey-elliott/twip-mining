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


# --- LLM tier: classify_pair_llm / provenance verification --------------------------


def _uncertain_pair(*result_texts, command_text="x lamp", source_id="src", pair_index=0):
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
    obvious = _pair(" Taken.")  # rule-classified as SUCCESS
    uncertain = _pair(" An oil-lamp of copper and glass, warm to the touch.")
    sampled = classify.sample_uncertain_pairs([obvious, uncertain], sample_size=10)
    assert sampled == [uncertain]


def test_sample_uncertain_pairs_returns_all_when_sample_size_covers_them():
    pairs = [
        _pair(" A red door.", command_text="x door"),
        _pair(" A blue door.", command_text="x other door"),
    ]
    sampled = classify.sample_uncertain_pairs(pairs, sample_size=10)
    assert set(id(p) for p in sampled) == set(id(p) for p in pairs)


def test_sample_uncertain_pairs_is_deterministic_for_a_fixed_seed():
    pairs = [
        _pair(f" description of item {i}.", command_text=f"x item{i}") for i in range(10)
    ]
    first = classify.sample_uncertain_pairs(pairs, sample_size=3, seed=42)
    second = classify.sample_uncertain_pairs(pairs, sample_size=3, seed=42)
    assert first == second
    assert len(first) == 3


# --- LLM tier: build_llm_prompt / parse_llm_response ---------------------------------


def test_build_llm_prompt_includes_command_and_result_text():
    pair = _uncertain_pair(" An oil-lamp of copper and glass, warm to the touch.")
    prompt = classify.build_llm_prompt(pair)
    assert "x lamp" in prompt
    assert "An oil-lamp of copper and glass, warm to the touch." in prompt
    for bucket in OutcomeBucket:
        assert bucket.value in prompt


def test_parse_llm_response_accepts_well_formed_json():
    raw = json.dumps({"outcome": "world_failure", "confidence": 0.4, "evidence": ["can't do that"]})
    parsed = classify.parse_llm_response(raw)
    assert parsed["outcome"] is OutcomeBucket.WORLD_FAILURE
    assert parsed["confidence"] == 0.4
    assert parsed["evidence"] == ["can't do that"]
