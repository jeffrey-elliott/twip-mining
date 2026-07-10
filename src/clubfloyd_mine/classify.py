"""Pass 5 - Classify Outcomes.

Assigns an OutcomeBucket to each command pair: regex/rule first, then LLM
for uncertain cases, then a human-review queue for low confidence.
See doc/pipeline/05_classify_outcomes.md.

Two of the three tiers exist now:

- `classify_pair_rule`: deterministic regex/rule classifier for "obvious"
  cases, per CLAUDE.md's priority to prefer deterministic extraction before
  LLM interpretation. Returns None for anything not confidently matched --
  that is the "uncertain" bucket the next tier handles.
- `classify_pair_llm`: LLM classifier for a *sample* of uncertain pairs
  (calling an LLM on the full corpus is neither cheap nor reviewed yet).
  Takes an injected `call: LlmCallable` rather than talking to a provider
  directly, so it stays testable with a fake and provider-agnostic. Per
  CLAUDE.md priority #1/#3 (source provenance), it never trusts the LLM's
  bare word: the model must return verbatim evidence quotes, and
  `_verify_evidence` checks each quote is actually a substring of the
  pair's own result text before a ClassifiedPair is produced. A response
  that fails that check raises LlmProvenanceError instead of being
  recorded -- an unverifiable classification must not exist at all, rather
  than existing with a misleadingly normal-looking confidence score.

The human-review queue (tier 3, for low-confidence results) does not exist
yet, and `classify_pair_llm` is not yet wired into `run()` or the CLI --
that's a deliberate follow-up (it needs a real provider client and a
decision on how sampling/cost/review interact end to end), not an
oversight. `run()` (writing
data/parsed/<year>/<id>/classified_pairs.jsonl) still raises
NotImplementedError.

The prefixes/phrases below were calibrated against a real fetch of all
2007 ClubFloyd sessions (not committed; see CLAUDE.md's data policy) --
they are standard Inform/Adrift parser-library messages that recur
verbatim across many different games, not game-specific text. Game-specific
reimplementations of these messages (e.g. Lost Pig's "Grunk not know what
that mean.") are deliberately left unmatched -- they fall to "uncertain"
rather than being hardcoded one-off, which would not generalize.
"""
from __future__ import annotations

import argparse
import json
import random
from typing import Callable, Sequence

from clubfloyd_mine.models import ClassificationSource, ClassifiedPair, CommandPair, OutcomeBucket

# A callable that takes a prompt string and returns the raw LLM response
# text. Kept as a plain type alias (not a provider client) so
# classify_pair_llm has no import-time dependency on any LLM SDK -- tests
# inject a fake, and a real provider wrapper (e.g. calling the Anthropic
# API) can live in its own module and be passed in by callers.
LlmCallable = Callable[[str], str]

DEFAULT_LLM_SAMPLE_SIZE = 20

# Matched against the start of any single (stripped, lowercased) result
# line. A prefix rather than an exact match because the standard-library
# message is sometimes followed by extra clause text ("I only understood
# you as far as wanting to short.") or trailing prompt characters.
_OBVIOUS_FAILURE_PREFIXES = (
    "you can't see any such thing",
    "you can't go that way",
    "you can't ride that way",
    "you can't take that",
    "you haven't seen anything like that",
    "you don't see that",
    "you don't feel any such thing",
    "you don't find anything",
    "that's not a verb i recognis",  # "recognise"
    "that's not a verb i recogniz",  # "recognize"
    "that noun did not make sense in this context",
    "that doesn't make any sense",
    "i didn't understand that sentence",
    "i only understood you as far as",
    "that's not something you can enter",
    "that's not something you need to refer to",
    "that's hardly portable",
    "you can only do that to something animate",
    "you can't think of anything to say on that topic",
    "violence isn't the answer to this one",
)

# Matched as a full-line, case-insensitive equality: terse one-word/two-word
# standard-library success confirmations. Deliberately exact (not prefix)
# since these words also occur as ordinary prose elsewhere.
_OBVIOUS_SUCCESS_LINES = {
    "taken.",
    "dropped.",
    "opened.",
    "closed.",
    "locked.",
    "unlocked.",
    "worn.",
    "removed.",
    "done.",
    "ok.",
    "saved.",
    "eaten.",
    "drunk.",
    "burned.",
    "pushed.",
    "pulled.",
    "turned.",
    "switched on.",
    "switched off.",
    "extinguished.",
    "lit.",
}


def classify_pair_rule(pair: CommandPair) -> OutcomeBucket | None:
    """Deterministic "obvious case" classifier. Returns None (uncertain)
    when no rule confidently matches -- callers must not treat that as
    UNKNOWN, only as "not yet classified"."""
    lines = [block.text.strip().lower() for block in pair.result_blocks if block.text.strip()]
    if not lines:
        return None

    for line in lines:
        if any(line.startswith(prefix) for prefix in _OBVIOUS_FAILURE_PREFIXES):
            return OutcomeBucket.PARSER_FAILURE

    for line in lines:
        if line in _OBVIOUS_SUCCESS_LINES:
            return OutcomeBucket.SUCCESS

    return None



class LlmProvenanceError(ValueError):
    """Raised when an LLM classification can't be trusted: malformed
    response shape, an outcome/confidence outside the valid range, or (most
    importantly) evidence quotes that don't verify against the pair's own
    result text. Callers must not construct a ClassifiedPair when this is
    raised -- see the module docstring's provenance note."""


def sample_uncertain_pairs(
    pairs: Sequence[CommandPair], *, sample_size: int = DEFAULT_LLM_SAMPLE_SIZE, seed: int = 0
) -> list[CommandPair]:
    """Deterministically sample from the pairs `classify_pair_rule` left
    uncertain, for the LLM tier to classify. Only pairs already uncertain
    are eligible -- rule-classified pairs are never re-sent to the LLM.

    A fixed `seed` (rather than unseeded randomness) makes this restartable
    and idempotent per CLAUDE.md priority #5: re-running against the same
    input set reproduces the same sample instead of drifting."""
    uncertain = [pair for pair in pairs if classify_pair_rule(pair) is None]
    if sample_size >= len(uncertain):
        return uncertain
    return random.Random(seed).sample(uncertain, sample_size)


def build_llm_prompt(pair: CommandPair) -> str:
    """Build the prompt for `classify_pair_llm`. Pure/deterministic so it's
    directly testable without an LLM: given the same pair, always produces
    the same prompt text."""
    result_lines = [block.text for block in pair.result_blocks if block.text.strip()]
    result_text = "\n".join(result_lines) if result_lines else "(no result text)"
    buckets = ", ".join(bucket.value for bucket in OutcomeBucket)
    return (
        "You are classifying one command/result pair from a ClubFloyd interactive-fiction "
        "transcript into exactly one outcome bucket.\n\n"
        f"Command sent to Floyd: {pair.command_text!r}\n\n"
        f"Game's result text:\n{result_text}\n\n"
        f"Choose exactly one outcome from this list: {buckets}.\n\n"
        "Respond with a single JSON object and nothing else, with these keys:\n"
        '  "outcome": one of the bucket names above\n'
        '  "confidence": a number from 0.0 to 1.0\n'
        '  "evidence": a non-empty list of short substrings copied verbatim, character for '
        "character, from the game's result text above -- do not paraphrase or summarize\n"
        '  "rationale": a one-sentence explanation'
    )


def parse_llm_response(raw: str) -> dict:
    """Parse and shape-validate the LLM's raw response text. Raises
    LlmProvenanceError (not a bare parse error) so every rejection path in
    this module is the same exception type for callers to catch."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LlmProvenanceError(f"LLM response was not valid JSON: {raw!r}") from exc

    if not isinstance(data, dict):
        raise LlmProvenanceError(f"LLM response JSON was not an object: {raw!r}")

    try:
        outcome = OutcomeBucket(data["outcome"])
    except (KeyError, ValueError) as exc:
        raise LlmProvenanceError(f"LLM response had an invalid or missing outcome: {data!r}") from exc

    try:
        confidence = float(data["confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LlmProvenanceError(f"LLM response had an invalid or missing confidence: {data!r}") from exc
    if not 0.0 <= confidence <= 1.0:
        raise LlmProvenanceError(f"LLM response confidence out of range [0, 1]: {confidence!r}")

    evidence = data.get("evidence")
    if not isinstance(evidence, list) or not evidence or not all(isinstance(e, str) and e.strip() for e in evidence):
        raise LlmProvenanceError(f"LLM response had no usable evidence quotes: {data!r}")

    return {
        "outcome": outcome,
        "confidence": confidence,
        "evidence": evidence,
        "rationale": data.get("rationale"),
    }


def _verify_evidence(pair: CommandPair, evidence: Sequence[str]) -> None:
    """Confirm every evidence quote is a verbatim substring of *this pair's*
    own result text. This is the enforcement point for CLAUDE.md's
    provenance priority at the LLM tier: the model is never given
    source_id, so nothing else stops it from hallucinating a plausible
    quote or bleeding in text from a different pair's context window."""
    haystack = "\n".join(block.text for block in pair.result_blocks)
    for quote in evidence:
        if quote not in haystack:
            raise LlmProvenanceError(
                f"evidence quote not found verbatim in source_id={pair.source_id!r} "
                f"pair_index={pair.pair_index}: {quote!r}"
            )


def classify_pair_llm(pair: CommandPair, call: LlmCallable) -> ClassifiedPair:
    """LLM tier (doc 05's tier 2): call only for pairs where
    `classify_pair_rule` returned None. Raises LlmProvenanceError -- rather
    than returning a low-confidence ClassifiedPair -- for any response
    whose evidence can't be verified against the pair's own result text.
    An unverifiable classification must not be recorded at all; see the
    module docstring."""
    raw = call(build_llm_prompt(pair))
    parsed = parse_llm_response(raw)
    _verify_evidence(pair, parsed["evidence"])
    return ClassifiedPair(
        source_id=pair.source_id,
        pair_index=pair.pair_index,
        outcome=parsed["outcome"],
        confidence=parsed["confidence"],
        classifier=ClassificationSource.LLM,
        evidence=list(parsed["evidence"]),
        notes=parsed["rationale"],
    )


def run(args: argparse.Namespace) -> None:
    raise NotImplementedError(
        "classify is not implemented yet beyond classify_pair_rule(); "
        "see doc/pipeline/05_classify_outcomes.md"
    )
