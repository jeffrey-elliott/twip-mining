# Interaction Type: Directed NPC Command

## Summary

A directed NPC command addresses an actor by name and delegates an action to them, rather than the player performing the action directly.

The shape is:

    ACTOR, COMMAND

This is distinct from ask/tell (conversation) and give/show (object transfer): the player is instructing the actor to act.

## Canonical Example

Input:

    > raven, get object

Output:

    The raven has better things to do.

    The raven flutters into the air, circling the rock stairs, then dives
    for the tiny glittering object. It rises, circles, and with a
    self-satisfied flurry returns to your side, dropping a small silver key
    at your feet.

    >

## Classification

    interaction_type: npc_command
    command_family: npc
    world_model_relevant: true
    puzzle_relevant: true
    npc_relevant: true
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: npc/command

## Common Input Forms

    raven, get object
    guard, open door
    robot, take box
    dog, fetch stick

## Parse Shape

    ACTOR, COMMAND

Example:

    raven, get object

Extract:

    actor: raven
    delegated_command: get object

## Recognize This Type By

The command begins with an actor name followed by a comma.

The response may show refusal:

    The raven has better things to do.

or obedience:

    The raven ... dropping a small silver key at your feet.

or both together (see "Mixed Refusal And Action" below).

## What To Mine

Directed NPC commands are useful for extracting:

- which delegated actions an actor will perform
- which delegated actions an actor refuses
- objects an NPC can manipulate, fetch, or deliver
- NPC location changes caused by the command
- puzzle-relevant delegation (an actor doing something the player cannot do directly)

From this example:

    raven:
      npc_or_actor: true
      commanded_actions_attempted:
        - get object
      commanded_action_result: refused_then_acted (see below)

    small silver key:
      appears_or_is_delivered_after:
        command: raven, get object
      final_location: at player feet
      causal_link_to_command: uncertain

## Mixed Refusal And Action

Some outputs contain an apparent refusal followed by an actor event that looks like the actor complying anyway. Handle this cautiously -- don't assume the surface refusal is the whole story, and don't assume the actor obeyed just because something happened next.

Example:

    The raven has better things to do.

    The raven flutters into the air...
    ...dropping a small silver key at your feet.

Possible split:

    npc_command_result:
      actor: raven
      delegated_command: get object
      direct_response: refusal_or_dismissal
      text: The raven has better things to do.

    npc_or_ambient_event:
      actor: raven
      action: retrieves tiny glittering object
      result: drops small silver key at player's feet
      causal_link_to_command: uncertain

Do not automatically assume the raven obeyed the command if the direct response says it refused. Do record that a key appeared or moved to the player's feet regardless -- that fact stands on its own even if its cause is ambiguous.

## Ambient Text Inside NPC Command Output

Directed-command output may include unrelated ambient narration.

Example:

    The curtains billow gently in the draft.

Some raven behavior may be a response to the command; some may be ambient. Use caution and only infer causality when the response clearly links the event to the command.

## State Guidance

Directed commands may cause the actor to move objects, open things, fetch items, or refuse.

Possible state changes:

    npc fetches item:
      object moves from remote/source location to player location

    npc refuses:
      no state change from the command itself, though a follow-on ambient
      event may still change state (see "Mixed Refusal And Action")

## Puzzle Guidance

Mine:

- commands the NPC refuses
- commands the NPC obeys
- objects NPCs can manipulate that the player cannot reach directly
- objects NPCs reveal or deliver
- NPC location changes

A refusal may indicate the wrong command, wrong timing, missing precondition, or that the actor is simply not commandable for that action.

## Do Not Confuse With

Ask:

    `ask ACTOR about TOPIC` requests information. See `ask.md`.

Give/Show:

    `give OBJECT to ACTOR` / `show OBJECT to ACTOR` offer an object rather than delegate an action. See `give.md`.

Bare command:

    A command with no leading `ACTOR,` prefix is the player acting directly, not delegating.

Examine:

    `x raven` describes the actor.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the command addresses an actor by name followed by a comma and a delegated action, classify it as npc/command. Extract the actor, the delegated command, whether it was refused or obeyed, and any resulting state change -- watch for refusal text followed by an action that happens anyway.
