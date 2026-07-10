# Interaction Type: Quit / Quit Confirmation

## Summary

The `quit` command is a meta command that asks to end the game session.

It usually does not immediately quit. Instead, it prompts the player for confirmation.

The short form `q` may also mean `quit`, but only classify it this way when the output behaves like quit.

## Canonical Example

Input:

    > quit

Output:

    Are you sure you want to quit?

## Possible Short Form

Input:

    > q

Expected quit-style output:

    Are you sure you want to quit?

However, do not assume every `q` command is quit unless the response confirms it.

If `q` returns a room description, object description, movement result, or other in-world text, classify the pair according to the output instead.

## Classification

    interaction_type: quit_confirmation
    command_family: meta
    world_model_relevant: false
    puzzle_relevant: false
    state_change_expected: pending_confirmation
    state_observation_expected: false
    transcript_noise: false
    keep_as_command_pair: true
    short_label: meta/quit-confirmation

## Common Input Forms

Commands in this family include:

    quit
    q

Normalize these to:

    quit

Only normalize `q` to `quit` when the response is quit-like.

## Recognize This Type By

The output usually asks for confirmation:

    Are you sure you want to quit?

Other possible confirmation forms:

    Do you really want to quit?
    Please answer yes or no.
    Are you sure?

The key feature is that the game is asking whether the player intends to end the session.

## What To Mine

Useful for:

- command taxonomy
- identifying meta-command behavior
- recognizing session-control commands
- separating game controls from in-world actions

Not useful for:

- object descriptions
- room descriptions
- inventory state
- puzzle modeling
- world state
- affordance extraction
- NPC behavior

## State Guidance

The initial quit command usually does not end the game by itself.

It creates a pending confirmation state.

Possible extraction:

    command: quit
    result: confirmation_requested
    pending_confirmation: true
    game_ended: false

A later answer such as `yes` may actually end the session.

## Do Not Treat As Chatter

Quit prompts are game output, not transcript chatter.

Even though they are out-of-world, they are still valid command/output pairs.

## Do Not Confuse With

Room descriptions:

    These describe the current location and visible objects.

Examine responses:

    These describe a specific in-world target.

Inventory listings:

    These list carried or worn items.

Human chatter:

    These are player comments outside the game channel.

Mispaired interactions:

    If the command appears to be `q` but the output is a room description, do not force it into quit classification.

## Special Caution For `q`

The command `q` is ambiguous in mined transcripts.

If the output is:

    Are you sure you want to quit?

classify it as:

    meta/quit-confirmation

If the output is a room description such as:

    Study
    Stone walls, wreathed in shadows and velvet curtains...

then classify it as a room description or transcript-pairing issue, not as quit.

## Rule Of Thumb

If the player types `quit` or `q` and the game asks for confirmation before ending the session, classify it as meta/quit-confirmation.

If `q` produces ordinary in-world prose, do not assume it means quit.