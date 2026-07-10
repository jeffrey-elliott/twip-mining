# Interaction Type: Listen / Ambient Sound

## Summary

The `listen` command asks the game for ambient/sound information about the current location, rather than visual detail.

The command shape is almost always bare:

    listen

Unlike `examine`, it's not usually directed at a specific object (`listen to X` is a related but distinct targeted form -- see uncle_zarf_pd.md's "LISTEN TO object"; no real example of that targeted form has been seen in this corpus yet).

## Canonical Examples

Input:

    > listen

Output:

    It is hard to pinpoint the sound; it seems to shift as you listen.

    A quiet knocking reverberates through the walls.

    >

Input (same command, later in the same transcript, different ambient text):

    > listen

Output:

    It is hard to pinpoint the sound; it seems to shift as you listen.

    The curtains move softly, caressed by the breeze.

    >

## Classification

    interaction_type: listen_action
    command_family: listen
    world_model_relevant: possibly
    puzzle_relevant: possibly
    state_change_expected: false
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: sense/listen

## Common Input Forms

    listen

Per uncle_zarf_pd.md's taxonomy, a targeted form also exists in principle:

    listen to radio

but this corpus has no real example of it yet -- don't assume its response shape from the bare form above.

## Recognize This Type By

The command is exactly `listen` (no object).

The response describes an ambient sound rather than a visual scene, and often repeats a stable "can't pinpoint it" framing line even as the specific ambient detail after it varies turn to turn.

## What To Mine

Listen responses are useful for extracting:

- recurring ambient sound motifs (here, a mysterious knocking/tapping tied to the game's raven/Poe theme)
- whether the sound's description changes across repeated listens (it does here -- the framing sentence is stable, the second line varies)
- puzzle-relevant sound clues

From these examples:

    ambient_sound:
      framing_line: "It is hard to pinpoint the sound; it seems to shift as you listen."
      observed_variants:
        - "A quiet knocking reverberates through the walls."
        - "The curtains move softly, caressed by the breeze."
      state_change: false

## Repeated Listen With Varying Ambient Text

Both canonical examples above are the *same* command ("listen") at two different points in the transcript. The stable first line ("It is hard to pinpoint the sound...") is a fixed framing response; the line after it varies. This is the same shape as look_or_examine.md's "Ambient Text Inside Examine Output" -- don't fold the varying ambient line into a claim about a fixed, stable world-state fact.

## Do Not Confuse With

Examine:

    `x object`/`examine object` describes a specific visual target. See look_or_examine.md.

Search:

    `search object` is a more active attempt to find something in/on an object. See search.md.

Listen to (targeted form):

    `listen to X` -- documented by uncle_zarf_pd.md's taxonomy, but unattested in this corpus. Don't assume it behaves like bare `listen`.

## Rule Of Thumb

If the player types bare `listen` and the game responds with ambient sound description rather than a room/object description, classify it as sense/listen. Expect the response to vary across repeated calls even when nothing else in the world has changed.
