# Interaction Type: Unlock / Unlock Object With Instrument

## Summary

The `unlock` command attempts to unlock an in-world object, usually using another object as a key, tool, or instrument.

The common command shape is:

    unlock TARGET with INSTRUMENT

This is highly useful for puzzle and world-state mining because it identifies locked objects, keys/tools, required object relationships, and state changes.

## Canonical Example

Input:

    > unlock door with key

Output:

    You unlock the wooden door.

    The raven shifts its grip on the portrait.

    >

## Classification

    interaction_type: unlock_action
    command_family: unlock
    world_model_relevant: true
    puzzle_relevant: true
    state_change_expected: usually
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: action/unlock-with

## Common Input Forms

Commands in this family include:

    unlock door
    unlock door with key
    unlock wooden door with key
    unlock chest with brass key
    unlock gate with iron key
    unlock box with small key
    use key on door
    use key with door

The most explicit form is:

    unlock X with Y

Where:

    X = locked target
    Y = key, tool, or unlocking instrument

## Recognize This Type By

The player command usually contains:

    unlock

Often with:

    with

The response may indicate:

- the target was unlocked
- the target is already unlocked
- the key/tool does not fit
- the player lacks the needed key/tool
- the target is not locked
- the target cannot be unlocked
- the command succeeds but does not open the object
- the command changes access to a room, passage, container, or object

## What To Mine

Unlock responses are useful for extracting:

- lockable objects
- locked/unlocked state
- state transitions
- required keys or tools
- object relationships
- puzzle dependencies
- doors/gates/containers
- access gating
- successful versus failed unlock attempts

From this example:

    command:
      verb: unlock
      target: door
      instrument: key

    wooden door:
      lockable: true
      state_after_command:
        locked: false
        unlocked: true

    key:
      unlocks:
        - wooden door

    puzzle_relation:
      key required_or_sufficient_for: wooden door

## Successful Unlock

A successful unlock usually directly says the target has been unlocked.

Example:

    You unlock the wooden door.

Possible extraction:

    result: success
    state_change: true
    target: wooden door
    state_before:
      locked: likely_true
    state_after:
      locked: false
      unlocked: true

Do not automatically mark the door as open.

Unlocked and open are different states.

Possible state after this command:

    wooden door:
      locked: false
      open: unknown

## Target Versus Instrument

In the command:

    unlock door with key

The target is:

    door

The instrument is:

    key

Do not classify both as equal targets.

Possible extraction:

    action:
      verb: unlock
      target: door
      instrument: key

## Ambient Text Inside Unlock Output

Unlock output may include unrelated ambient narration after the action result.

Example:

    The raven shifts its grip on the portrait.

This is game output, not chatter.

However, it has nothing to do with the unlock action itself unless later evidence proves otherwise.

Separate it from the unlock result.

Correct split:

    action_result:
      You unlock the wooden door.

    ambient_event:
      The raven shifts its grip on the portrait.

Incorrect extraction:

    wooden door:
      raven shifts grip on portrait

## State Guidance

Unlock commands usually change lock state when successful.

They do not necessarily change open/closed state.

Example:

    You unlock the wooden door.

Means:

    wooden door:
      locked: false

Does not necessarily mean:

    wooden door:
      open: true

A later command may still be needed:

    open door

## Failed Unlock

Failed unlock responses are still useful.

Possible outputs:

    That doesn't seem to fit the lock.
    You don't have the key.
    The door is already unlocked.
    The door has no lock.
    You can't unlock that.
    You'll need a key.

Classify these as unlock attempts.

Possible extraction:

    command: unlock door with key
    result: failed
    state_change: false
    reason: key_does_not_fit

or:

    command: unlock door
    result: missing_instrument
    required_tool: key

## Puzzle Guidance

Unlock interactions are usually puzzle-relevant because they often express access control.

Mine:

- what blocks progress
- what object unlocks what
- whether the player had the right tool
- whether unlocking alone is enough
- whether another action is needed afterward

Important distinction:

    unlock door with key

may enable:

    open door

but does not always perform it.

## Do Not Confuse With

Open:

    `open door` changes or checks open/closed state.

Unlock:

    `unlock door with key` changes or checks locked/unlocked state.

Examine:

    `x door` describes the door.

Movement:

    `north`, `enter door`, or `go through door` attempts travel.

Use:

    `use key on door` may resolve to unlock behavior, but classify by response.

Ambient events:

    Raven movement, tapping, drafts, and mood text are game output but not part of the unlock action.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the player types `unlock X with Y`, classify the pair as action/unlock-with.

Extract the target, instrument, result, and lock-state change.

Split off any unrelated atmospheric or NPC text that appears after the unlock result.