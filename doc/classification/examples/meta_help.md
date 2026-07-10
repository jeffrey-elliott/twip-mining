# Interaction Type: Help / Meta Help Or Hint Gateway

## Summary

The `help` command is a meta command.

It asks the game for out-of-world assistance, instructions, or guidance. In some games, `help` is a synonym for `hint`. In other games, `help` explains commands, controls, story setup, hint policy, or how to access the hint system.

Classify based on the response, not only the command.

## Canonical Example

Input:

    > help

Output:

    [Warning: It is recognized that the temptation for help may at times be
    so exceedingly strong that you might fetch hints prematurely.
    Therefore, you may at any time during the story type HINTS OFF, and
    this will disallow the seeking out of help for the present session of
    the story. If you still want a hint now, indicate HINT.]

    >

## Classification

    interaction_type: help_meta
    command_family: meta
    world_model_relevant: false
    puzzle_relevant: possibly
    state_change_expected: false
    state_observation_expected: false
    transcript_noise: false
    keep_as_command_pair: true
    short_label: meta/help

## Common Input Forms

Commands in this family include:

    help
    ?

Related commands may include:

    hint
    hints
    info
    instructions
    commands
    about

Do not automatically merge all of these. Classify based on the output.

## Recognize This Type By

The output may include:

- command instructions
- gameplay instructions
- parser guidance
- hint-system instructions
- spoiler warnings
- session-control advice
- out-of-world explanation
- references to commands the player may type
- bracketed system-style text

Common phrases:

    type HINT
    type HINTS OFF
    If you still want a hint
    For help
    You may type
    Commands are
    Instructions

## What To Mine

Useful for:

- command taxonomy
- parser command discovery
- meta-command behavior
- hint-system behavior
- help-system behavior
- session options

From this example:

    discovered_commands:
      - HINTS OFF
      - HINT

    help_behavior:
      help_command_shows_hint_warning: true
      help_does_not_directly_show_hint: true
      hint_confirmation_or_redirect: true

## What Not To Mine

Do not mine help output as:

- in-world narration
- room description
- object description
- puzzle state
- player knowledge acquired in-world
- inventory state
- NPC dialogue
- environmental event

The text is addressed to the player, not experienced by the player character.

## Relationship To Hint

Sometimes `help` and `hint` are equivalent.

Sometimes `help` points to `hint`.

In this example, `help` does not directly reveal a puzzle hint. It warns the player about premature hints and tells them to type `HINT` if they still want one.

Possible extraction:

    command: help
    result: hint_warning
    directs_to:
      - HINT
      - HINTS OFF

This is not the same as a hint menu.

Compare:

    > hint

    Nevermore Hints
    N = next subject
    RETURN = read subject

That should be classified as:

    meta/hint-menu

But:

    > help

    If you still want a hint now, indicate HINT.

Should be classified as:

    meta/help

or more specifically:

    meta/help-hint-gateway

## State Guidance

The `help` command usually does not change world state.

It may reveal available meta commands.

It may describe a possible future state change:

    HINTS OFF

But unless the player actually types `HINTS OFF`, do not mark hints as disabled.

Possible extraction:

    state_change: false
    available_meta_action:
      command: HINTS OFF
      effect_if_used: disables help/hints for current session

## Bracketed System Text

Help output may appear in brackets:

    [Warning: ...]

This is still game output.

Do not treat it as human chatter.

Bracketed text often indicates system/meta narration rather than in-world narration.

## Do Not Confuse With

Hint menu:

    A hint menu lists puzzle topics or gives spoiler guidance.

About/credits/version:

    These describe the game, author, release, license, or credits.

Quit confirmation:

    This asks whether the player wants to quit.

Inventory:

    This lists carried or worn items.

Room description:

    This describes the current location.

Human chatter:

    These are transcript-side comments from players, not game output.

## Rule Of Thumb

If the player types `help` and the game responds with instructions, warnings, command guidance, or directions to the hint system, classify it as meta/help.

If `help` directly opens a hint menu or gives puzzle hints, classify it as meta/hint-menu or meta/hint-content instead.