"""Pass 5 - Classify Outcomes.

Assigns an OutcomeBucket to each command pair: regex/rule first, then LLM
for uncertain cases, then a human-review queue for low confidence.
See doc/pipeline/05_classify_outcomes.md.

Only the first tier (deterministic regex/rule classifier for "obvious"
cases) is implemented so far, per CLAUDE.md's priority to prefer
deterministic extraction before LLM interpretation. `classify_pair_rule`
returns None for anything not confidently matched -- that is the
"uncertain" bucket doc 05 defers to an LLM classifier and then a
human-review queue, neither of which exist yet. `run()` (writing
data/parsed/<year>/<id>/classified_pairs.jsonl) is not implemented until
those later tiers exist.

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

from clubfloyd_mine.models import CommandPair, OutcomeBucket

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


def run(args: argparse.Namespace) -> None:
    raise NotImplementedError(
        "classify is not implemented yet beyond classify_pair_rule(); "
        "see doc/pipeline/05_classify_outcomes.md"
    )
