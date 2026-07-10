# Interaction Type: Decaying Player Status Effect

## Summary

Some actions introduce player state that isn't a simple permanent flip (like a door going from closed to open) but instead decays or resolves gradually across several subsequent turns, independent of what the player does in those turns.

This doesn't need a new `OutcomeBucket` value -- each individual pair below already classifies correctly under the existing scheme. It's a cross-pair pattern worth recording as design evidence, the same way `solvable_blocked_action.md` records a different cross-pair pattern.

## Canonical Example

Source: *Nevermore* by Nate Cull, ClubFloyd session 2007-09-01 (`source_id: 20070901-nevermore`).

Pair #9:

    > sniff coca

    You inhale a quantity of coca powder.

    A sense of raw alertness rushes through your nerves, setting them all
    on edge.

A full turn later, pair #10 (see also doc/annotated_screenshots/floyd_marked_commands.png, which is where this was first spotted):

    > x me

    You look like a gentleman of ease, but that is not how you feel.

    A staccato rap echoes through the room.

    The coca rush fades, but the sense of alertness remains.

## Classification Note

Pair #9 is `success` (see `sniff.md`); pair #10 is `success` too (see `look_or_examine.md`'s `x me` treatment). Neither pair is individually mis-classified. The pattern only shows up when reading the two pairs together: the "coca rush" introduced by pair #9 is still resolving, unprompted, in pair #10's ambient text -- the player didn't do anything coca-related in between (`x me` is an unrelated examine), yet the game continues narrating the effect's decay.

## Twip Signal

This is a different kind of world-state than anything else documented so far in this project: not an object property (open/closed, locked/unlocked) and not inventory membership, but a *time-decaying player status* that the game tracks and narrates on its own schedule, independent of player action.

A Twip world model that only tracks discrete object/inventory state would miss this entirely -- it would see two unrelated `success` pairs and no reason to connect them. Representing this properly needs at least: (a) an event that starts a timed/decaying effect, and (b) a way to recognize follow-up narration (possibly attached to an unrelated command, as here) as reporting on that same effect's progress rather than as fresh, disconnected ambient text.

See also `combat_loop_annotated.png`'s HP tracking (`doc/classification/examples/turn_based_combat.md`) for a related but distinct case: HP is *numeric* state that updates every turn regardless of command relevance, whereas this coca-rush effect is a *qualitative* state (present vs. faded) that resolves over a small, seemingly fixed number of turns without being tied to a turn-counter visible in the text.

## Rule Of Thumb

When mining ambient text attached to an otherwise-unrelated command, check whether it's actually progress-narration for an effect introduced by an earlier command, rather than assuming all ambient text is independent flavor. Don't invent a new outcome bucket for this -- it's a relationship between two already-correctly-classified pairs, not a new classification of either one.

## Do Not Confuse With

Ambient text in general (look_or_examine.md, unlock.md, open_close.md, etc.):

    Most ambient text (raven behavior, curtains, weather) is genuinely independent flavor with no state to track. Only treat ambient text as effect-progress narration when it explicitly references an effect introduced by an earlier, identifiable command (here, "the coca rush" unambiguously refers back to pair #9's "sniff coca").

Turn-based combat HP (`turn_based_combat.md`):

    Numeric, updates every turn, tied to command-vs-parser-failure rather than elapsed real narrative time.

`solvable_blocked_action.md`:

    A different cross-pair pattern (a blocked goal that was already solvable when first attempted), not a status effect at all.
