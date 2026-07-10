# Interaction Type: Give / Show Object To Actor

## Summary

`give` and `show` present or transfer an object to an in-world actor. They target the same kind of actor as `ask`/`tell`/directed-NPC-command, but they are object-transfer commands, not conversation.

Common command shapes:

    give OBJECT to ACTOR
    give ACTOR OBJECT
    show OBJECT to ACTOR
    show ACTOR OBJECT

This corpus has a real example of `give`. It does not yet have an observed `show` example -- `show` is documented here by shape/analogy only (same target-actor grammar as `give`), not from a canonical transcript quote. Do not treat the `show` guidance below as corpus-verified until a real example is found.

## Canonical Example

Input:

    > give peyote to raven

Output:

    The raven doesn't seem interested.

    The raven shifts slightly on the bust of Pallas, with a soft 'chink'.

    >

## Classification

    interaction_type: npc_object_transfer
    command_family: npc
    world_model_relevant: true
    puzzle_relevant: possibly
    npc_relevant: true
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: npc/give

## Common Input Forms

Give with `to`:

    give peyote to raven
    give key to guard

Give without `to`:

    give raven peyote
    give guard key

Show (unattested in this corpus, documented by analogy to give):

    show key to raven
    show raven key

## Normalize These Shapes

Give with `to`:

    give OBJECT to ACTOR

Example:

    give peyote to raven

Extract:

    object: peyote
    recipient: raven

Give without `to`:

    give ACTOR OBJECT

Example:

    give raven peyote

Extract:

    object: peyote
    recipient: raven

## Recognize This Type By

The command begins with `give` or `show`, and names both an object and an actor.

Common response patterns:

    The raven doesn't seem interested.
    The guard accepts the key.
    He refuses to take it.
    She examines it and hands it back.

## What To Mine

Give/show responses are useful for extracting:

- which objects an NPC will accept or reject
- puzzle-relevant gift requirements
- NPC preferences
- inventory changes caused by acceptance
- NPC reactions that aren't acceptance/rejection at all (e.g. "shifts slightly ... with a soft 'chink'" -- ambiguous, may or may not signal anything)

From this example:

    peyote:
      given_to: raven
      result: rejected_or_uninterested

    raven:
      npc_or_actor: true
      rejected_gifts:
        - peyote

## Giving Objects To NPCs

Giving commands attempt to transfer an object from the player to an actor.

Example:

    give peyote to raven

Possible extraction:

    command:
      verb: give
      object: peyote
      recipient: raven

    result:
      accepted: false
      inventory_changed: false
      response: raven not interested

Do not assume the object left inventory unless the output says it was accepted, taken, dropped, or removed.

## Ambient Text Inside Give Output

Example:

    The raven shifts slightly on the bust of Pallas, with a soft 'chink'.

This is game output, not chatter, but it is not clearly caused by the give command -- it may just be ambient raven behavior. Do not infer that the "chink" sound means the raven touched or examined the object unless later evidence confirms it.

## State Guidance

Give may change inventory if the object is accepted:

    gift accepted:
      object moves from player inventory to npc

    gift rejected:
      object remains with player

Only mark a world-state change when the output shows the object was actually accepted, taken, or moved.

## Puzzle Guidance

Mine:

- objects offered
- objects accepted vs. rejected
- whether a rejection implies a different object/actor/timing is needed
- whether acceptance triggers a further NPC action

A rejection may indicate the wrong object, wrong actor, wrong timing, or that the actor simply isn't interested (not every rejection is a puzzle clue).

## Do Not Confuse With

Ask:

    `ask ACTOR about TOPIC` requests information, not a transfer. See `ask.md`.

Directed NPC command:

    `ACTOR, COMMAND` delegates an action to the actor rather than offering it an object. See `npc_command.md`.

Take:

    `take OBJECT` moves an object into the player's own inventory.

Put:

    `put OBJECT in/on CONTAINER` places an object relative to a non-actor object, not an actor.

Examine:

    `x raven` describes the actor.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the command offers or presents an object to an actor, classify it as npc/give (or npc/show once a real example is observed). Extract the object, actor, and whether it was accepted. Do not assume acceptance without explicit textual confirmation.
