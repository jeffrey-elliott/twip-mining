# Interaction Type: Blocked Action With An Already-Available Solution

## Summary

Sometimes a player pursues one underlying goal (get through a door, reach a
room) across several command/result pairs, where each individual pair is a
correctly recognized action that is refused or granted for a genuine
world-state reason -- but the player already held everything needed to
resolve the block *before* the sequence started.

This is not a parser defect and not a single mis-classified pair. It is a
pattern visible only across several consecutive pairs sharing the same
target/goal, where the same world_failure resolves after some number of
intervening successful commands.

## Canonical Example

Source: *Nevermore* by Nate Cull, ClubFloyd session 2007-09-01.
`source_id: 20070901-nevermore`
`https://allthingsjacq.com/intfic_clubfloyd_20070901.html`

Established earlier in the same transcript, pairs #97-99: the raven fetches
an object, the player takes it, and examines it --

    > raven, get object
    ... self-satisfied flurry returns to your side, dropping a small silver key ...

    > get key

    > x key
    It is the small silver key to your laboratory, that you threw away last ...

-- so the key needed below is already in inventory well before the door
sequence starts.

Pairs #115-120:

    > e
    The wooden door is closed, and bars your way.
    The raven caws. "Nevermore!"

    > open door
    It seems to be locked.
    The raven preens its feathers.

    > unlock door with key
    You unlock the wooden door.
    The raven shifts its grip on the portrait.

    > e
    The wooden door is closed, and bars your way.
    The raven eyes you balefully.

    > open door
    You open the wooden door.
    The raven screeches discordantly.

    > e
    Laboratory
    The place of your secret labor and craft ...

## Classification Note

Each pair above already has a correct, individually-defensible bucket under
the existing scheme:

    #115  e                    -> world_failure   (movement blocked, door closed)
    #116  open door            -> world_failure   (locked)
    #117  unlock door with key -> success
    #118  e                    -> world_failure   (still closed -- unlocking a
                                                    door does not open it; see
                                                    unlock.md's "State Guidance")
    #119  open door            -> success
    #120  e                    -> location_change (the only pair where the
                                                    room actually changes)

None of these are `parser_failure`/unknown -- the parser understood every
command. This doc is not proposing a new `OutcomeBucket` value for any one
pair, and per-pair bucket correctness is a separate concern from what
follows.

(Separately, `classify.py`'s `_MOVEMENT_COMMANDS` fallback currently
mis-lands #115/#118 in `location_change` rather than `world_failure`,
because `_WORLD_FAILURE_PREFIXES`' exact-prefix matching doesn't survive the
inserted object name -- "the wooden door is closed" vs. "the door is
closed". That's a real bug, but it's a per-pair rule-matching fix, tracked
independently of the cross-pair pattern this doc describes.)

## The Gap: No Category For "Same Goal, Blocked Pending A Prerequisite The Player Already Had"

What the outcome-bucket vocabulary has no way to say is that #115, #116,
#118 are not independent events -- they are the *same* attempted goal
(reach the room to the east), and the block was already solvable at the
moment it first appeared, because the player was carrying the key the
whole time.

This is a different shape than `special_blocked_move.md`'s hazard-blocked
movement (darkness, danger), where no solution is available yet. Here the
solution was available before the first failure.

Whether this deserves a distinct bucket, a pair-sequence-level annotation
(e.g. linking #115/#116/#118 to the #117/#119 pairs that resolve them), or
some other representation is an open question -- not resolved by this doc.
Flagging it here so it isn't lost, without forcing a premature schema
decision.

## Twip Signal

This is design evidence about Twip, not a defect in *Nevermore*'s parser or
in this project's classification pipeline. Nevermore behaves exactly as an
Inform game should: it will not implicitly unlock or open a door for the
player, and a human player is expected to work through the closed-door /
locked / unlock / still-closed / open sequence themselves, which they did.

But Twip's design goals differ from a bare Inform parser's. Given (a) a key
already in inventory, and (b) a door already known (or trivially
discoverable) to be locked, a benevolent Twip planner could act on already-
available state to collapse the sequence -- e.g. sequencing `unlock door
with key` -> `open door` -> `e` on the player's behalf, or at least
surfacing "you have a key for this" -- instead of the player re-discovering
the same blocker twice across five turns.

## Rule Of Thumb

Classify each pair in a sequence like this individually and correctly --
don't invent a new bucket per pair just because it's part of a larger
blocked-then-resolved arc. Separately, when mining these transcripts for
Twip signal, watch for clusters of repeated commands toward the same
target/direction with an intervening resolving command (unlock, take, turn
on a light, etc.) -- that cluster, not any single pair in it, is the
design-evidence unit worth recording.

## Do Not Confuse With

Hazard-blocked movement (`special_blocked_move.md`):
    No solution exists yet at the time of the block (darkness, danger,
    missing tool not yet found). Contrast with this doc, where the
    solution was already in hand.

Individual `world_failure`/`success` classification:
    Already correct per-pair under the existing rule tier (aside from the
    `_MOVEMENT_COMMANDS` prefix-matching bug noted above). This doc is
    about the cross-pair pattern, not about re-bucketing any single pair.
