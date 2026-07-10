# Interaction Type: Open / Opening An Object

## Summary

The `open` command attempts to open an in-world object, passage, container, cover, door, window, or similar thing.

The command shape is:

    open TARGET

This is usually world-model relevant because it can reveal whether something is openable, already open, permanently open, blocked, locked, or connected to another object.

## Canonical Examples

Input:

    > open window

Output:

    You swing wide the shutters, letting the cold night air gust into the
    room.

    A staccato rap echoes through the room.

    The curtains move softly, caressed by the breeze.

    >

Input:

    > open door

Output:

    The archway is open, and will remain so.

    A quiet knocking reverberates through the walls.

    >

Input:

    > open window

Output:

    That's already open.

    Your surroundings shift weirdly; a vision forms itself before your
    eyes.

    The room is much larger; or you are much younger. Your father sits at
    the writing desk, poring over obscure books. His hair is grey, his face
    lined with care. The purple curtains, vast and shadowy, billow above
    you in a draft from the window; the gap between them and the floor
    seems cavernous. You toddle toward the gap. Somewhere, a raven caws...

    The visionary sense fades, and normal sight returns.

    A dull, dark weariness drifts over you.

    >

## Classification

    interaction_type: open_action
    command_family: open
    world_model_relevant: true
    puzzle_relevant: possibly
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: action/open

## Common Input Forms

Commands in this family include:

    open door
    open window
    open shutters
    open curtains
    open box
    open sachet
    open book
    open drawer
    open gate
    open archway

The basic command pattern is:

    open X

## Recognize This Type By

The player command starts with `open`, followed by a target noun or noun phrase.

The response may indicate:

- the target opens successfully
- the target is already open
- the target cannot be opened
- the target is locked
- the target is permanently open
- another related object is actually opened
- opening causes environmental changes
- opening reveals or enables something
- opening triggers narration, memory, or vision text

## What To Mine

Open responses are useful for extracting:

- openable objects
- current open/closed state
- state changes
- implied object relationships
- passages and exits
- blocked or locked conditions
- environmental effects
- puzzle gating
- repeated-action behavior

From these examples:

    window:
      openable: true
      command_target: true
      state_after_first_open: open
      repeated_open_response: That's already open.

    shutters:
      affected_by_command:
        command: open window
      state_after_command: open
      relationship:
        associated_with: window

    door:
      command_target: true
      response_object: archway
      state_observed: open
      note: door may be represented by or described as an archway

    archway:
      state_observed: open
      permanence: will remain open

    curtains:
      affected_by_environment: true
      moved_by: breeze from opened window
      note: mentioned in output, but not the command target in these examples

## Successful Open

A successful open usually includes prose showing the object has changed state.

Example:

    You swing wide the shutters, letting the cold night air gust into the room.

This should be treated as a state-changing action.

Possible extraction:

    command: open window
    result: success
    state_change: true
    target_state_after: open
    affected_object: shutters
    environmental_effect:
      - cold night air enters room
      - curtains move in breeze

## Already Open

An open command may be valid even when it does not change state.

Example:

    That's already open.

This should still be classified as an open interaction.

Possible extraction:

    command: open window
    result: already_open
    state_change: false
    observed_state:
      window: open

## Permanently Or Irreversibly Open

Some responses indicate that an object is open and will stay open.

Example:

    The archway is open, and will remain so.

Possible extraction:

    command: open door
    result: already_or_permanently_open
    state_change: false
    observed_state:
      archway: open
    permanence:
      remains_open: true

## Related Object Mapping

Do not assume the command target and affected object are always identical.

Example:

    > open window

    You swing wide the shutters...

Here the player typed `window`, but the game describes opening `shutters`.

Possible extraction:

    command_target: window
    affected_object: shutters
    relation:
      shutters cover or are attached to window

This is important for parser and world-model mining.

## Ambient Text Inside Open Output

An open response may include unrelated or semi-related ambient narration after the action result.

Examples:

    A staccato rap echoes through the room.

    A quiet knocking reverberates through the walls.

These lines are game output, not chatter.

However, they should usually be classified separately as ambient event text, not as the stable result of opening the object.

## Vision Or Memory Text After Open

Sometimes an open command is followed by a vision, memory, dream, flashback, or other major narrative event.

Example:

    Your surroundings shift weirdly; a vision forms itself before your eyes.

This is still game output.

It may or may not be caused by the open command. Treat it carefully:

    open_result:
      That's already open.

    narrative_event:
      type: vision_or_memory
      triggered_after_command: open window
      causal_link: uncertain

Do not merge the whole vision into the window's object description.

## How To Treat It

This is a valid player command and valid game response.

Do not classify it as chatter.

Do not discard it because the object is already open.

Do not assume every line after the command describes the target object.

Do separate:

    Action result:
      You swing wide the shutters...

    State observation:
      That's already open.

    Ambient event:
      A quiet knocking reverberates through the walls.

    Narrative event:
      Your surroundings shift weirdly; a vision forms itself before your eyes.

## Do Not Confuse With

Examine responses:

    These describe an object in detail, usually after `x` or `examine`.

Room descriptions:

    These describe the current location as a whole, usually after `look` or movement.

Meta commands:

    These describe the game, help system, version, author, or credits.

Human chatter:

    These are transcript-side comments from players, not game output.

## Rule Of Thumb

If the player types `open X`, classify the pair as action/open even when the result is “already open,” “locked,” “cannot open,” or when the game describes a related object opening instead of the literal target.