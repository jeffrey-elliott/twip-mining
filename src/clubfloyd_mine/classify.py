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

`classify_pair_rule` was extended using the verb-by-verb classification
guides in doc/classification/examples/*.md, which supply two kinds of new
signal beyond the original result-text prefix/exact-line matching:

- More result-text phrase families, in priority order (first match wins):
  score_or_end_state (death/game-over markers) > disambiguation ("which do
  you mean") > world_failure (command was understood, but refused for a
  world-state reason -- locked, already open, don't have the key/object)
  > parser_failure (command/noun not understood at all) > inventory_change
  (taken/dropped/removed-style confirmations) > generic success. The
  world_failure/parser_failure split matters: "you can't take that" means
  the parser didn't resolve the object, while "you already have that" or
  "you don't have the key" mean it did, and the attempt still failed --
  those are different buckets, not both parser_failure.
- Command-text-based fallbacks, checked only when no result-text rule
  matched: a fixed set of meta-verbs (about/help/hint/restart/...) that are
  meta_or_floyd_control regardless of their (highly game-specific) output
  text, and a fixed set of movement verbs/prefixes that become
  location_change when they didn't already fail one of the checks above.
  This is the first time the rule tier reads command_text, not just result
  text -- verbs like `again`/`g` (whose outcome depends on resolving a
  prior command) and `xyzzy` (whose response is too game-specific to bucket
  by verb alone) are deliberately NOT included here; per those docs' own
  cautions they stay "uncertain" rather than becoming an unreliable rule.

Running the updated rules against the real corpus (`clubfloyd audit`)
surfaced a real-data quirk in how result lines get extracted: a single
result_blocks entry isn't always one clean physical line. normalize.py's
game-output regex (anchored on a leading "floyd |", DOTALL) can swallow several
"Floyd | ..." continuation lines from the source HTML into one block, so
block.text is sometimes e.g. " Taken.\nFloyd |\nFloyd | >\n" -- one block,
three embedded physical lines. The original exact-line matching (treating
`block.text.strip().lower()` as one line) essentially never matched real
data because of this; prefix matching happened to still work since it
only needs the start of the string to line up. `_result_lines` below fixes
this at the Pass-5 consumption site (not in normalize.py, which is a
separate pass with its own blast radius) by splitting each block on
newlines and stripping embedded "Floyd |" residue before matching.

A close read of pairs #115-120 of the real 2007-09-01 Nevermore transcript
(doc/classification/examples/solvable_blocked_action.md) surfaced two more
gaps, both fixed here: (1) `_WORLD_FAILURE_SUBSTRINGS` catches blocked-
movement phrasing where the invariant wording doesn't start the line
because the game inserts a variable object description first ("The wooden
door is closed, and bars your way." vs. the door.md-documented "The door is
closed."); without it, these pairs fell through every rule and were
misclassified by the `_MOVEMENT_COMMANDS` fallback as a successful
location_change even though the room never changed. (2) `_SUCCESS_PREFIXES`
catches open.md/unlock.md's own full-sentence success confirmations ("You
open/unlock the wooden door.") that embed the object's name, as opposed to
the terse invariant `_OBVIOUS_SUCCESS_LINES` ("Opened.", "Unlocked.").

`_EXAMINE_OR_LOOK_COMMANDS`/`_EXAMINE_OR_LOOK_PREFIXES` encode a stronger,
deliberate claim from look_or_examine.md: for `x`/`examine`/`inspect`/`look
at`/bare `look`, there is no third outcome beyond "the parser didn't
resolve the target" (already caught earlier by `_OBVIOUS_FAILURE_PREFIXES`,
e.g. "you don't see that"/"i can't find that"/"that's not here") and "here
is a description" -- so any non-blank prose reaching this fallback *is* a
successful examine/look, not merely "uncertain". This is a real accuracy
tradeoff, not a free win: a game that reimplements parser failure in its
own voice for one of these verbs specifically (the way Lost Pig's Grunk
says "Grunk not know what that mean." generically) would be misclassified
as a successful examine rather than staying uncertain. That's accepted
deliberately here, on the grounds that a genuinely unresolved target is
already covered by the failure-phrase list above for every real game seen
so far; if a counterexample turns up, add its specific phrase to
`_OBVIOUS_FAILURE_PREFIXES` rather than walking back this fallback.
"""
from __future__ import annotations

import argparse
import json
import random
import re
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
#
# This bucket is reserved for the parser not understanding the verb/noun at
# all. "you can't take that"/"you can't go that way" mean there's no such
# object/exit in the parser's model of the world -- contrast with
# _WORLD_FAILURE_PREFIXES below, where the parser understood the command
# fine and refused it for an in-world reason (locked, already done, don't
# have the required object).
_OBVIOUS_FAILURE_PREFIXES = (
    "you can't see any such thing",
    "you can't go that way",
    "you cannot go that way",
    "there is no exit in that direction",
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
    "i can't find that",
    "that's not here",
)

# doc/classification/examples/{take,open,open_close,unlock,go,
# special_blocked_move}.md: the command was understood and the target
# resolved, but the action was refused for a world-state reason (locked,
# already in that state, missing prerequisite, blocked by hazard). Matched
# the same way as _OBVIOUS_FAILURE_PREFIXES (prefix, on stripped/lowercased
# lines).
_WORLD_FAILURE_PREFIXES = (
    "you already have that",
    "that's fixed in place",
    "you can't carry any more",
    "that's already open",
    "it's already closed",
    "that's already closed",
    "it is locked",
    "it is bolted shut",
    "you cannot open that",
    "it refuses to move",
    "you can't close that",
    "there is nothing to close",
    "that doesn't seem to fit the lock",
    "the door has no lock",
    "you can't unlock that",
    "you'll need a key",
    "you don't have the",  # template: "you don't have the key/lamp/..."
    "you don't have that",
    "the door is already unlocked",
    "the door is closed",
    "the way is blocked",
    "the door is locked",
    "it is too dark",
    "you would not chance it",
    "you need more light",
    "you would fall",
    "you cannot safely proceed",
    "darkness bars your way",
    "it seems to be locked",
)

# doc/classification/examples/solvable_blocked_action.md, sourced from the
# real 2007-09-01 Nevermore transcript (pairs #115/#118): a blocked-movement
# message whose invariant wording doesn't start the line, because the game
# inserts a variable object description first -- "The wooden door is closed,
# and bars your way." vs. the door.md-documented "The door is closed."
# _WORLD_FAILURE_PREFIXES can't catch this with startswith(); matched by
# substring instead. Kept as its own tuple (rather than switching
# _WORLD_FAILURE_PREFIXES to substring matching) so the existing invariant
# prefixes keep their tighter, safer match semantics.
_WORLD_FAILURE_SUBSTRINGS = (
    "is closed, and bars your way",
)

# doc/classification/examples/disambiguation.md: "which do you mean...?"
# and its variants, regardless of the verb that triggered it.
_DISAMBIGUATION_PREFIXES = (
    "which do you mean",
    "which one do you mean",
    "which do you want",
    "do you mean",
    "did you mean",
    "please be more specific",
    "there are far too many",  # take.md: "There are far too many books to remove them all."
)

# doc/classification/examples/death.md's "strong markers" and post-death
# prompt text. "the end" is matched as a full line, not a prefix, since
# unlike the others it's short enough to risk matching ordinary prose
# ("The end of the hallway...").
_SCORE_OR_END_STATE_PREFIXES = (
    "*** you have died ***",
    "you have died",
    "you are dead",
    "game over",
    "you have lost",
    "you have failed",
    "would you like to restart",
    "restart, restore or quit",
    "press any key to restart",
    "restore a saved game",
)
_SCORE_OR_END_STATE_EXACT_LINES = {"the end", "the end."}

# doc/classification/examples/{take,inventory}.md: taken/dropped/removed
# mean an object moved into or out of the player's inventory -- a more
# specific bucket than generic success. ": Removed." (e.g. "peyote button:
# Removed.") is take.md's bulk-take confirmation format: an item name
# followed by this suffix.
_INVENTORY_CHANGE_LINES = {"taken.", "dropped.", "worn.", "removed."}
_INVENTORY_CHANGE_SUFFIX = ": removed."

# Matched as a full-line, case-insensitive equality: terse one-word/two-word
# standard-library success confirmations. Deliberately exact (not prefix)
# since these words also occur as ordinary prose elsewhere.
_OBVIOUS_SUCCESS_LINES = {
    "opened.",
    "closed.",
    "locked.",
    "unlocked.",
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
    "you find nothing of interest.",  # search.md: recognized, completed, nothing found
    "you are carrying:",  # inventory.md: a listing, not a mutation -- success, not inventory_change
}

# doc/classification/examples/{open,unlock}.md's own canonical examples,
# sourced from the real 2007-09-01 Nevermore transcript (pairs #117/#119):
# "You open/unlock the wooden door." -- a full-sentence success confirmation
# with the object's name embedded, unlike the terse invariant lines above.
# Matched as a prefix (the object name and trailing punctuation vary, but
# the verb phrase always starts the line), and safe to keep broad: any
# refusal wording ("you can't open that", "it is locked", ...) is checked
# earlier in classify_pair_rule's priority order and would have already
# matched before this is reached.
_SUCCESS_PREFIXES = (
    "you open the ",
    "you unlock the ",
)

# doc/classification/examples/meta_{about,help,hint,quit}.md, death.md:
# command verbs whose bucket is meta_or_floyd_control almost regardless of
# their (highly game-specific) output. Checked only as a command-text
# fallback, after every result-text rule above has had a chance to fire --
# per meta_about.md's own caution, a result that clearly signals something
# else (e.g. a world_failure phrase) should win.
#
# Deliberately excluded: `quit`/`q` (meta_quit.md warns not to assume this
# without a result-text confirmation prompt -- that's handled by
# _WORLD_FAILURE/_SCORE_OR_END_STATE-style phrases instead, not here),
# `xyzzy`/`plugh`/`plover` (xyzzy.md: response is too game-specific to
# bucket by verb alone), and `again`/`g` (again.md: outcome depends on
# resolving the prior command, which this single-pair classifier can't do).
_META_COMMANDS = {
    "about",
    "credits",
    "info",
    "version",
    "license",
    "help",
    "?",
    "hint",
    "hints",
    "instructions",
    "commands",
    "restart",
    "restore",
}

# doc/classification/examples/go.md: movement commands. Checked as a
# command-text fallback, and only once every result-text failure/refusal
# check above has already had a chance to catch a blocked move -- if none
# matched and the game printed something back, treat it as a successful
# room change. Deliberately excludes "forward"/"back" (go.md: game-specific,
# not safe to assume) and "sit"/"stand" (not movement unless the result
# proves otherwise, which this rule tier can't confirm).
_MOVEMENT_COMMANDS = {
    "n", "north", "s", "south", "e", "east", "w", "west",
    "ne", "northeast", "nw", "northwest", "se", "southeast", "sw", "southwest",
    "u", "up", "d", "down",
    "in", "inside", "out", "outside", "enter", "exit", "leave",
}
_MOVEMENT_PREFIXES = ("go ", "walk ", "head ", "climb ", "descend ", "ascend ", "enter ", "exit ", "leave ")

# doc/classification/examples/look_or_examine.md: examine/look commands.
# Checked as a command-text fallback, same position and rationale as
# _MOVEMENT_COMMANDS above -- every failure/refusal check runs first (in
# particular "you can't see any such thing"/"you don't see that"/"i can't
# find that"/"that's not here" in _OBVIOUS_FAILURE_PREFIXES, which cover the
# parser-didn't-resolve-the-target case), so if none of those matched and
# the game printed prose back, that prose *is* the successful examine/look
# result -- there's no third outcome for this verb family beyond "target
# not found" and "here's a description". Deliberately excludes "look under
# X"/"look in X"/"search X" (search.md: a distinct, more active verb) and
# "read X" (read.md: has its own readable/not-readable failure modes this
# blanket rule can't safely assume).
_EXAMINE_OR_LOOK_COMMANDS = {"look", "l"}
_EXAMINE_OR_LOOK_PREFIXES = ("x ", "examine ", "inspect ", "look at ")

# Strips a leading "floyd |" (any case, optional trailing space) from a
# physical line -- see the module docstring's note on _result_lines.
_EMBEDDED_FLOYD_PREFIX_RE = re.compile(r"^floyd\s*\|\s?", re.IGNORECASE)


def _result_lines(pair: CommandPair) -> list[str]:
    """Flatten pair.result_blocks into individual physical lines, each
    stripped and lowercased, with any embedded "Floyd |" continuation
    residue removed. See the module docstring: a single result block isn't
    always one clean line in real data."""
    lines = []
    for block in pair.result_blocks:
        for raw_line in block.text.split("\n"):
            line = _EMBEDDED_FLOYD_PREFIX_RE.sub("", raw_line).strip().lower()
            if line:
                lines.append(line)
    return lines


def classify_pair_rule(pair: CommandPair) -> OutcomeBucket | None:
    """Deterministic "obvious case" classifier. Returns None (uncertain)
    when no rule confidently matches -- callers must not treat that as
    UNKNOWN, only as "not yet classified". See the module docstring for the
    priority order and its rationale."""
    lines = _result_lines(pair)
    if not lines:
        return None

    for line in lines:
        if line in _SCORE_OR_END_STATE_EXACT_LINES or any(
            line.startswith(prefix) for prefix in _SCORE_OR_END_STATE_PREFIXES
        ):
            return OutcomeBucket.SCORE_OR_END_STATE

    for line in lines:
        if any(line.startswith(prefix) for prefix in _DISAMBIGUATION_PREFIXES):
            return OutcomeBucket.DISAMBIGUATION

    for line in lines:
        if any(line.startswith(prefix) for prefix in _WORLD_FAILURE_PREFIXES) or any(
            substring in line for substring in _WORLD_FAILURE_SUBSTRINGS
        ):
            return OutcomeBucket.WORLD_FAILURE

    for line in lines:
        if any(line.startswith(prefix) for prefix in _OBVIOUS_FAILURE_PREFIXES):
            return OutcomeBucket.PARSER_FAILURE

    for line in lines:
        if line in _INVENTORY_CHANGE_LINES or line.endswith(_INVENTORY_CHANGE_SUFFIX):
            return OutcomeBucket.INVENTORY_CHANGE

    for line in lines:
        if line in _OBVIOUS_SUCCESS_LINES or any(line.startswith(prefix) for prefix in _SUCCESS_PREFIXES):
            return OutcomeBucket.SUCCESS

    command = pair.command_text.strip().lower()
    if command in _META_COMMANDS:
        return OutcomeBucket.META_OR_FLOYD_CONTROL
    if command in _MOVEMENT_COMMANDS or command.startswith(_MOVEMENT_PREFIXES):
        return OutcomeBucket.LOCATION_CHANGE
    if (command in _EXAMINE_OR_LOOK_COMMANDS or command.startswith(_EXAMINE_OR_LOOK_PREFIXES)) and any(
        line != ">" for line in lines
    ):
        # The ">" guard excludes a bare leftover prompt marker (see
        # _result_lines' docstring) from counting as "prose was returned" --
        # that's not a description, just a rendering artifact.
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
