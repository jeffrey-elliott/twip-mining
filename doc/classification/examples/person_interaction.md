# Interaction Type: NPC / Person Interaction

## Summary

NPC/person interactions are commands directed at an in-world actor rather than a passive object.

The actor may be a person, animal, creature, robot, spirit, or other entity the game treats as capable of responding, refusing, accepting, moving, speaking, or being commanded.

In these examples, the raven functions as an NPC/person-like actor.

Common command shapes include:

    ask ACTOR about TOPIC
    ask ACTOR TOPIC
    tell ACTOR about TOPIC
    give OBJECT to ACTOR
    give ACTOR OBJECT
    show OBJECT to ACTOR
    ACTOR, COMMAND

These interactions are often puzzle-relevant, even when the actor refuses or gives no reply.

## Canonical Examples

Input:

    > ask raven about lenore

Output:

    There is no reply.

    The raven watches you silently from the bust of Pallas.

    The curtains billow gently in the draft.

    >

Input:

    > give peyote to raven

Output:

    The raven doesn't seem interested.

    The raven shifts slightly on the bust of Pallas, with a soft 'chink'.

    >

Input:

    > ask raven about key

Output:

    There is no reply.

    The raven caws. "Nevermore!"

    The curtains move softly, caressed by the breeze.

    >

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

    interaction_type: npc_interaction
    command_family: npc
    world_model_relevant: true
    puzzle_relevant: possibly
    npc_relevant: true
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: npc/interaction

## Common Input Forms

Conversation commands:

    ask raven about lenore
    ask raven about key
    ask guard about boat
    tell guard about password
    talk to raven
    talk to guard

Giving or showing commands:

    give peyote to raven
    give raven peyote
    show key to raven
    show raven key

Directed NPC commands:

    raven, get object
    guard, open door
    robot, take box
    dog, fetch stick

## Normalize These Shapes

Ask with topic:

    ask ACTOR about TOPIC

Example:

    ask raven about key

Extract:

    actor: raven
    topic: key

Ask without explicit `about`:

    ask ACTOR TOPIC

Example:

    ask raven key

Treat as likely equivalent to:

    ask raven about key

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

Directed command:

    ACTOR, COMMAND

Example:

    raven, get object

Extract:

    actor: raven
    delegated_command: get object

## Recognize This Type By

The command includes an actor/NPC as the target, recipient, or addressee.

Common signs:

- command begins with `ask`, `tell`, `give`, `show`, or `talk`
- command contains `to ACTOR`
- command contains `about TOPIC`
- command begins with an actor name followed by a comma
- output mentions whether the actor replies, refuses, accepts, ignores, moves, speaks, or reacts

Common response patterns:

    There is no reply.
    The raven doesn't seem interested.
    The raven has better things to do.
    The guard refuses.
    The robot obeys.
    The dog fetches the stick.
    "Nevermore!"

## What To Mine

NPC interactions are useful for extracting:

- NPC names
- NPC topics
- accepted and rejected gifts
- possible conversation topics
- commanded actions
- NPC refusals
- NPC movement
- NPC inventory effects
- puzzle-relevant social actions
- actor/object relationships
- evidence that an entity is animate or actor-like

From these examples:

    raven:
      npc_or_actor: true
      conversation_topics_attempted:
        - lenore
        - key
      ask_response:
        no_reply: true
      rejected_gifts:
        - peyote
      commanded_actions_attempted:
        - get object

    peyote:
      given_to: raven
      result: rejected_or_uninterested

    small silver key:
      appears_or_is_delivered_after:
        command: raven, get object
      final_location: at player feet
      causal_link_to_command: uncertain

## Conversation: Ask / Tell

Conversation commands usually query an actor about a topic.

Example:

    ask raven about lenore

Possible extraction:

    command:
      verb: ask
      actor: raven
      topic: lenore

    result:
      reply: none
      state_change: false

A no-reply response is still useful.

It means the command was understood, the raven is a valid interaction target, and the topic was attempted.

Do not discard failed or silent conversation attempts.

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

## Directed NPC Commands

A command like this addresses the actor directly:

    raven, get object

This means the player is asking the raven to perform `get object`.

Possible extraction:

    surface_command: raven, get object
    actor: raven
    delegated_command: get object
    interaction_type: npc_command

The response may show refusal:

    The raven has better things to do.

or obedience:

    The raven ... dropping a small silver key at your feet.

When both appear, split the response carefully.

## Mixed Refusal And Action

Some outputs contain an apparent refusal followed by an actor event.

Example:

    The raven has better things to do.

    The raven flutters into the air...
    ...dropping a small silver key at your feet.

This should be handled cautiously.

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

Do not automatically assume the raven obeyed the command if the direct response says it refused.

Do record that a key appeared or moved to the player's feet.

## Ambient Text Inside NPC Output

NPC interaction output may include unrelated ambient narration.

Examples:

    The curtains billow gently in the draft.

    The raven watches you silently from the bust of Pallas.

Some raven behavior may be a response. Some may be ambient.

Use caution.

Correct split:

    interaction_result:
      There is no reply.

    npc_state_or_ambient_event:
      The raven watches you silently from the bust of Pallas.

    ambient_environment:
      The curtains billow gently in the draft.

Incorrect extraction:

    topic: lenore
    causes curtains to billow

Only infer causality when the response clearly links the event to the command.

## State Guidance

NPC interactions may or may not change state.

Ask/tell usually reveal response behavior but often do not change world state.

Give may change inventory if accepted.

Directed commands may cause the actor to move objects, open things, fetch items, or refuse.

Possible state changes:

    gift accepted:
      object moves from player inventory to npc

    gift rejected:
      object remains with player

    npc fetches item:
      object moves from remote/source location to player location

    no reply:
      no clear state change

## Puzzle Guidance

NPC interactions can be puzzle-relevant even when they fail.

Mine:

- topics the player tried
- gifts rejected or accepted
- commands the NPC refuses
- commands the NPC obeys
- objects NPCs can manipulate
- objects NPCs reveal or deliver
- NPC location changes
- repeated NPC catchphrases
- clues embedded in NPC reactions

A refusal may indicate the wrong object, wrong topic, wrong timing, missing precondition, or that the actor is not commandable.

## Do Not Confuse With

Examine:

    `x raven` describes the actor.

Inventory:

    `i` lists carried items.

Take:

    `take raven` attempts to take the actor/object.

Read:

    `read book` reads text from an object.

Ambient events:

    NPC movement or bird behavior may occur independently of the player's command.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the command addresses, asks, tells, gives to, shows to, or commands an in-world actor, classify it as npc/interaction.

Extract the actor, topic or object, result, and any state change.

Split unrelated ambient narration from the actual NPC interaction result.