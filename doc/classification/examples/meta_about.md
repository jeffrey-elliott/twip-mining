# Interaction Type: About / Informational Metadata

## Summary

The `about` command returns out-of-world information about the game.

This is a real command/output pair, but it is not an in-world action. It should usually be excluded from puzzle, object, room, and affordance mining.

## Canonical Example

Input:

    > about

Output begins:

    NEVERMORE is a work of Interactive Fiction by Nate Cull
    (culln@xtra.co.nz), written for the 2000 IF Competition,
    and based very loosely on the poem "The Raven" by Edgar Allan Poe.

Output ends:

    Dedicated to: Alex. Want corknut! Awwk!

    >

## Classification

    interaction_type: informational_metadata
    command_family: meta
    world_model_relevant: false
    puzzle_relevant: false
    state_change_expected: false
    transcript_noise: false
    keep_as_command_pair: true
    short_label: meta/about

## Recognize This Type By

The output may include:

- game title
- author
- credits
- copyright or license text
- competition or release information
- version/archive information
- help instructions
- dedication
- implementation notes

Common commands include:

    about
    credits
    info
    version
    license
    help

## How To Treat It

This is a valid player command and a valid game response.

Do not classify it as chatter.

Do not treat it as in-world narration.

Do not mine it as:

- object description
- room description
- puzzle response
- scenery discovery
- affordance evidence
- state transition
- success/failure interaction

## Mining Guidance

Useful for:

- game metadata
- author/title/source extraction
- command taxonomy
- identifying meta-command behavior

Not useful for:

- world modeling
- puzzle modeling
- room graph construction
- object affordance extraction
- NPC behavior
- inventory or state changes

## Rule Of Thumb

If the command asks the game about the game itself, classify it as metadata unless the response clearly changes in-world state.