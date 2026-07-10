# Interaction Type: Open / Close Reversible Object State

## Summary

Some objects support paired `open` and `close` actions.

These commands change or check an object's open/closed state.

Common command shapes:

    open TARGET
    close TARGET
    shut TARGET

This interaction type is world-model relevant because it identifies objects with reversible state.

## Canonical Examples

Input:

    > open gate

Output:

    You unbolt the great iron gate and swing it slowly open, revealing the
    night outside.

    >

Input:

    > close gate

Output:

    You pull the great iron gate to and bolt it carefully.

    The raven screeches discordantly.

    >

## Classification

    interaction_type: open_close_state_action
    command_family: open_close
    world_model_relevant: true
    puzzle_relevant: possibly
    state_change_expected: usually
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: action/open-close-state

## Common Input Forms

Open commands:

    open gate
    open door
    open window
    open box
    open drawer
    open curtains
    open shutters

Close commands:

    close gate
    close door
    close window
    close box
    close drawer
    close curtains
    close shutters
    shut gate
    shut door
    shut window

Normalize:

    shut X -> close X

## Recognize This Type By

The command starts with:

    open

or:

    close

or:

    shut

The response indicates that the target's open/closed state changes or is checked.

Common successful open language:

    You open...
    You swing ... open.
    You pull ... open.
    You unbolt ... and swing it open.
    It opens.

Common successful close language:

    You close...
    You shut...
    You pull ... to.
    You bolt it carefully.
    It closes.

Common already-state language:

    That's already open.
    It's already closed.
    The gate is already shut.

## What To Mine

Useful for extracting:

- openable/closeable objects
- reversible state
- current open/closed state
- access changes
- revealed areas
- environmental effects
- puzzle gates
- whether an object can block or reveal an exit

From the examples:

    great iron gate:
      openable: true
      closeable: true
      state_model:
        open: boolean
      open_result:
        state_after: open
        reveals:
          - night outside
      close_result:
        state_after: closed

## Open And Close As Paired Evidence

If both `open TARGET` and `close TARGET` work, the object likely has a reversible open/closed state.

Example:

    open gate -> gate becomes open
    close gate -> gate becomes closed

Possible extraction:

    object: great iron gate
    supports_actions:
      - open
      - close
    reversible_state:
      open_closed: true

## Do Not Over-Model Descriptive Mechanisms

The response may mention a bolt, latch, handle, hinge, lock, or other mechanism.

Example:

    You unbolt the great iron gate and swing it slowly open...

    You pull the great iron gate to and bolt it carefully.

This suggests the gate has a bolt in the prose.

It does not prove that `bolt`, `unbolt`, or `latch` is implemented as a separate object or command.

Correct extraction:

    great iron gate:
      openable: true
      closeable: true
      described_mechanism:
        - bolt

Incorrect extraction without more evidence:

    bolt:
      implemented_object: true
      separately_takeable: true
      separately_openable: true
      command_supported:
        - bolt gate
        - unbolt gate

Only model the bolt as an implemented object if later commands prove it:

    x bolt
    unbolt gate
    lock gate
    unlock gate
    open bolt
    close bolt

## Open May Include Implied Unlocking Or Unbolting

Some games combine mechanism manipulation into the open/close prose.

Example:

    You unbolt the great iron gate and swing it slowly open...

This may mean:

    command: open gate
    result: success
    state_after:
      gate_open: true

It does not necessarily mean the player separately unlocked the gate.

Do not infer:

    gate_locked_before: true

unless the text or prior failed commands establish that.

## Close May Include Implied Bolting

Example:

    You pull the great iron gate to and bolt it carefully.

This means the gate is closed.

It may also suggest the gate is secured, but be cautious.

Possible extraction:

    gate:
      state_after:
        open: false
        closed: true
      described_as_bolted: true

Do not automatically infer:

    locked: true

unless the game later treats it as locked.

## State Guidance

Successful open:

    state_change: true
    target_state_after: open

Successful close:

    state_change: true
    target_state_after: closed

Already open:

    state_change: false
    observed_state: open

Already closed:

    state_change: false
    observed_state: closed

## Ambient Text Inside Close Output

Open and close responses may include unrelated ambient narration.

Example:

    The raven screeches discordantly.

This is game output, not chatter.

However, it should usually be split from the gate's stable state result.

Correct split:

    action_result:
      You pull the great iron gate to and bolt it carefully.

    ambient_event:
      The raven screeches discordantly.

Incorrect extraction:

    gate:
      causes raven screech

Only infer causality if repeated evidence supports it.

## Relationship To Movement

Opening a gate, door, hatch, or window may reveal or enable movement.

Example:

    revealing the night outside

Possible extraction:

    gate:
      state_after: open
      may_reveal_or_enable_access_to:
        - outside
        - night outside

But do not create a confirmed room edge unless movement later proves it.

Confirmed movement would require something like:

    > out
    > go through gate
    > north

followed by a destination room.

## Relationship To Unlock

Open/close and lock/unlock are different state dimensions.

Possible dimensions:

    open_closed:
      open: true or false

    locked_unlocked:
      locked: true or false

This example proves open/closed behavior.

It does not by itself prove a lock/unlock mechanic.

## Failed Open Or Close

Failed forms are still useful.

Possible failed open responses:

    It is locked.
    It is bolted shut.
    You cannot open that.
    It refuses to move.

Possible failed close responses:

    That's already closed.
    You can't close that.
    It won't stay closed.
    There is nothing to close.

Classify these as open/close attempts with failed or already-state results.

## Do Not Confuse With

Unlock:

    Changes locked/unlocked state.

Open:

    Changes open/closed state.

Close:

    Changes open/closed state in the opposite direction.

Movement:

    Moves the player through an exit or into another room.

Examine:

    Describes the object.

Ambient events:

    Raven behavior, tapping, drafts, and mood text are game output but not part of the open/close state unless clearly linked.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If `open X` and `close X` both work, classify the target as having reversible open/closed state.

Extract the state changes, but do not assume every mechanism mentioned in the prose is separately implemented as an object or command.