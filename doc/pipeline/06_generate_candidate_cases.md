# Pass 06 - Generate candidate cases (for development)

This is where the markdown/datarecord idea fits.

## Example Success Record:

---
record_type: interaction_pattern
category: viewing
behavior_candidate: LookThroughable
outcome: success
source_id: 2009-01-25-earth-and-sky
game: Earth and Sky
played_date: 2009-01-25
command: "look through window"
normalized_verb: "look"
normalized_preposition: "through"
source_url: "..."
confidence: 0.77
---

## Evidence

Player attempts to look through a visible object. The game produces a meaningful description rather than a generic parser failure.

## Twip signal

Twip should support `look through <target>` as a first-class indirect-looking action, probably routed to a `LookThroughable` behavior.

## Notes

Check whether object state modifies the result:
- open/closed
- covered/uncovered
- broken/unbroken
- light/dark
- weather/time dependent

## Example Failure Record:

---
record_type: failure_pattern
category: parser_failure
source_id: 2015-01-04-you-were-here
command: "x obelisk"
failure_kind: unknown_abbreviation_or_target
confidence: 0.64
---

## Evidence

The command failed at parser or object-resolution level.

## Twip signal

Useful for deciding whether Twip should support abbreviation aliases such as `x` for `examine`.