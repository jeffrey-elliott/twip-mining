# Interaction Type: Turn-Based Combat / Minigame With Numeric State

## Summary

Some games embed a turn-based combat or contest minigame where the game tracks numeric state (hit points) for the player and an opponent, updating turn-by-turn after any *understood* command -- not just combat-specific ones.

Like `solvable_blocked_action.md` and `decaying_status_effect.md`, this doesn't require a new `OutcomeBucket` value. Every individual pair below classifies correctly today. This is cross-pair, numeric world-state evidence worth recording for Twip's design, not a classifier gap.

## Canonical Example

Source: *The Day I Shot Hitler* by Taleslinger, a "New Year's Speed(s)" ClubFloyd session (see `doc/annotated_screenshots/combat_loop_annotated.png`) -- a dance-combat minigame against Hitler.

    > get hitler's moustache
    That seems to be a part of Hitler.
    Hitler gets two steps into a quite passable conga before remembering
    himself. He quickly pretends that he was just invading Poland.
    Your HP: 10
    Hitler's HP: 8

    > rumba
    You bust out a phat rumba. Hitler screams in agony at your
    degenerate-art stylez!
    Hitler gets two steps into a quite passable time warp before
    remembering himself. He quickly pretends that he was just demonstrating
    the natural inferiority of non-Aryan dances.
    Your HP: 10
    Hitler's HP: 7

    > x my moustache
    You see nothing special about your moustache.
    Hitler gets two steps into a quite passable twist before remembering
    himself. He quickly pretends that he was just readjusting his testicle.
    Your HP: 9
    Hitler's HP: 6

    > twist
    (Hitler)
    That would be less than courteous.
    Hitler makes a half-hearted attempt at a sword dance. Whatever.
    Your HP: 9
    Hitler's HP: 6

    > samba
    That noun did not make sense in this context.

    > watusi
    That noun did not make sense in this context.

    > pull hitler's moustache
    Nothing obvious happens.
    With a flourish, Hitler breaks into a Cossack dance - but he has failed
    to anticipate the rich, authentic proletarian traditions associated
    with the form! Your pinko heart swells with pride - and hit points.

    > minuet
    Not sure what good it'll do, you attempt a lacklustre minuet. The
    judges give you a total score of four point three, and Hitler sneers.
    Hitler gets two steps into a quite passable mashed potato before
    remembering himself. He quickly pretends that he was just warming up.
    Your HP: 11
    Hitler's HP: 6

## Classification Note

`get hitler's moustache`, `rumba`, and `x my moustache` are each `success` (the last one via `_EXAMINE_OR_LOOK_COMMANDS`). `twist` here is `world_failure` ("that would be less than courteous" -- a polite-refusal phrasing, the same family as the already-covered "violence isn't the answer to this one"). `samba`/`watusi` are each `parser_failure`, already covered by `"that noun did not make sense in this context"`. `pull hitler's moustache` is `world_failure` (`"nothing obvious happens"`, now covered -- see the module docstring's note on that phrase). No pair here is mis-classified.

## Twip Signal

The pattern only appears across pairs: **every command the parser understood -- combat move, refused, or object-directed -- advances a turn (an enemy counter-move is narrated); every command the parser rejected does not.** `x my moustache` (an examine) and `twist` (a refused/world_failure action) both still cost a turn and trigger Hitler's counter-dance, exactly like `rumba` does. `samba`/`watusi` (genuine parser failures) produce no enemy counter-move and no HP line at all.

This contradicts an assumption baked into `look_or_examine.md` ("state_change_expected: usually_false" for examine) -- in this specific turn-based-minigame context, understood commands are turn-consuming regardless of their own subject matter, because the state being advanced is "whose turn is it," not the examined object.

Two things this example rules out, worth being precise about rather than overclaiming a stricter pattern:

- **HP doesn't necessarily change every turn.** `twist` costs a turn (Hitler dances) but Your HP/Hitler's HP are identical before and after (9/6 -> 9/6). Turn-advancement and HP-change are related but not the same event.
- **The explicit "Your HP: N" / "Hitler's HP: N" lines aren't printed on every successful turn either.** `pull hitler's moustache`'s turn only narrates the effect in prose ("Your pinko heart swells with pride - and hit points") with no accompanying numeric status line. Don't assume every turn is machine-parseable via that strict format -- check for it, don't rely on it always being there.

The HP values are also a new *kind* of state for this project to model: numeric and bidirectional (Your HP goes from 9 to 11 after `minuet` -- it isn't monotonically decreasing), printed in an ad hoc format baked directly into ordinary `game_output` blocks rather than announced through any special formatting, and not guaranteed to appear every turn.

## What To Mine

- the "Your HP: N" / "Hitler's HP: N" line format, when present, extractable via a strict regex per turn
- which commands are recognized combat moves (rumba, breakdance, conga, twist, minuet, hornpipe, ...) vs. object-directed commands that still cost a turn but have no combat effect of their own
- the gating rule: parser-understood -> turn advances (even if refused or no-effect); parser-failure -> turn doesn't
- that HP-line presence and HP-value change are each independent of "did a turn happen" -- check per pair, don't assume

## Recognized-But-No-Effect Or Refused Commands Still Cost A Turn

Object-directed commands aimed at Hitler's moustache (`get hitler's moustache`, `x my moustache`, `pull hitler's moustache`) and the politely-refused `twist` all still cost a combat turn even though none of them land a combat blow. Don't assume "no narrative effect" or "refused" implies "no state change" inside a turn-based minigame like this one -- the turn itself is the state change.

## Do Not Confuse With

Ordinary examine (`look_or_examine.md`):

    Outside a turn-based minigame context, examine is genuinely usually state-neutral. This exception is scoped to games/segments with an active HP-tracking combat loop, not a general revision to that assumption.

Decaying status effects (`decaying_status_effect.md`):

    HP here is numeric, bidirectional, and tied to turn-consumption (parser success), not printed on a guaranteed schedule; the coca-rush effect there is qualitative and resolves on its own narrative schedule over real elapsed turns, independent of what command triggers each turn.

Parser failures not advancing a turn:

    This is the clean, useful part of the pattern -- already consistent with treating `"that noun did not make sense in this context"` as `parser_failure` with no other side effects assumed.

## Rule Of Thumb

Inside a detected turn-based combat/contest loop (recognizable by recurring "Your HP: N" / "$OPPONENT's HP: N" lines somewhere in the segment), treat every parser-understood command as turn-consuming regardless of whether it was combat-relevant, refused, or had no effect. Don't assume HP changes or an explicit status line on every such turn -- check each pair's own text. Treat parser failures as free (no turn cost, no HP change, no status line) exactly as elsewhere.
