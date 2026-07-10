# Interaction Type: Ask / Ask Actor About Topic

## Summary

The `ask` command is a conversation command directed at an in-world actor.

The usual shape is:

    ask ACTOR about TOPIC

Some games also accept shorter or looser forms:

    ask ACTOR TOPIC
    ask ACTOR for OBJECT
    ask ACTOR to ACTION

In Club Floyd transcript mining, `ask` should be treated as a valid player command and game response, not as human chatter.

`ask` is often puzzle-relevant even when the actor gives no answer. A failed or silent response still proves that the command was understood, the actor was recognized, and the topic was attempted.

## Canonical Examples

Input:

    > ask raven about lenore

Output:

    There is no reply.

    The raven watches you silently from the bust of Pallas.

    The curtains billow gently in the draft.

    >

Input:

    > ask raven about key

Output:

    There is no reply.

    The raven caws. "Nevermore!"

    The curtains move softly, caressed by the breeze.

    >

## Classification

    interaction_type: ask_action
    command_family: conversation
    world_model_relevant: true
    puzzle_relevant: possibly
    npc_relevant: true
    state_change_expected: usually_false
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: conversation/ask

## Common Input Forms

Preferred form:

    ask raven about lenore
    ask raven about key
    ask guard about boat
    ask woman about letter
    ask robot about door

Possible shorter form:

    ask raven lenore
    ask raven key
    ask guard boat

Request form:

    ask raven for key
    ask guard for help
    ask woman for letter

Instruction form:

    ask raven to get key
    ask guard to open door

Not every game supports every form. Classify based on the actual response.

## Parse Shape

For the standard form:

    ask ACTOR about TOPIC

Extract:

    verb: ask
    actor: ACTOR
    preposition: about
    topic: TOPIC

Example:

    surface_command: ask raven about key
    verb: ask
    actor: raven
    topic: key

For request form:

    ask ACTOR for OBJECT

Extract:

    verb: ask
    actor: ACTOR
    preposition: for
    requested_object: OBJECT

For instruction form:

    ask ACTOR to ACTION

Extract:

    verb: ask
    actor: ACTOR
    preposition: to
    requested_action: ACTION

## Recognize This Type By

The command begins with:

    ask

The command contains an actor, usually followed by a topic or request.

The response may include:

- no reply
- an NPC answer
- an NPC refusal
- an NPC reaction
- a hint or clue
- an indication that the topic is unknown
- an indication that the actor is not present
- an indication that the actor cannot understand

Common response patterns:

    There is no reply.
    The raven caws. "Nevermore!"
    The guard says nothing.
    The woman refuses to answer.
    He doesn't know anything about that.
    You get no response.
    The robot beeps thoughtfully.

## What To Mine

Ask responses are useful for extracting:

- NPC or actor names
- possible conversation topics
- failed conversation topics
- successful conversation topics
- clues returned by NPCs
- NPC catchphrases
- whether an actor can respond
- whether an actor ignores the player
- puzzle-relevant topic attempts
- evidence that an entity is actor-like

From the examples:

    raven:
      npc_or_actor: true
      ask_topics_attempted:
        - lenore
        - key
      ask_response:
        no_reply: true
      observed_responses:
        - watches silently
        - caws Nevermore

    lenore:
      used_as_ask_topic: true
      response_from_raven: no_reply

    key:
      used_as_ask_topic: true
      response_from_raven: no_reply

## No Reply Still Matters

A response like this:

    There is no reply.

is not chatter and not an unknown-command result.

It means the game recognized the command well enough to produce an in-game response.

Possible extraction:

    command_understood: true
    actor_recognized: true
    topic_attempted: true
    reply_received: false
    state_change: false

Do not discard the interaction just because it does not produce useful dialogue.

## Actor Versus Topic

In:

    ask raven about key

The actor is:

    raven

The topic is:

    key

Do not treat `key` as the object being directly manipulated.

Do not treat `raven` as an inventory target.

Correct extraction:

    actor: raven
    topic: key

Incorrect extraction:

    target: raven key
    object_taken: key
    key_given_to_raven: true

## Ask Versus Tell

`ask` requests information from an actor.

    ask raven about key

`tell` gives information to an actor.

    tell raven about key

They may receive similar responses, but they are different conversation commands. This project has not yet observed a real `tell` example in a transcript; if one turns up, it is a distinct command from `ask` and should not be folded into this doc's rules without its own canonical example.

## Ask Versus Say

`say` speaks words, possibly to oneself or to another actor.

    say Lenore
    say Lenore to raven

`ask` queries an actor about a topic.

    ask raven about Lenore

Do not classify `say Lenore` as ask just because it contains a topic-like word.

## Ask Versus Give/Show

`give OBJECT to ACTOR` and `show OBJECT to ACTOR` present or transfer an object to an actor; they are not conversation commands even though they target the same actor. See `give.md`.

## Ask Versus NPC Command

A command like this:

    raven, get object

is a directed NPC command, not an ask command. See `npc_command.md`.

Possible classification:

    npc/command

A command like this:

    ask raven to get object

is grammatically an ask command, but semantically it may be a request for the actor to act.

Possible classification:

    primary: conversation/ask
    secondary: npc/requested-action

Classify by response where possible.

## State Guidance

Most `ask` commands do not change physical world state.

They may reveal information, confirm silence, or trigger an NPC reaction.

Typical no-reply extraction:

    state_change: false
    information_gained:
      - actor gives no reply about topic

If the NPC gives a clue:

    state_change: false
    information_gained:
      - clue text

If the NPC gives an object, moves, opens something, or changes behavior:

    state_change: true

Only mark a world-state change when the output shows one.

## Puzzle Guidance

Ask interactions can be puzzle-relevant even without an obvious success result.

Mine:

- topics the player tried
- topics that get no response
- topics that produce clues
- repeated NPC phrases
- actor-specific topic behavior
- whether a requested object/action is refused
- whether the actor's response changes after other events

A failed ask may indicate:

- wrong actor
- wrong topic
- wrong timing
- missing prior event
- actor cannot speak
- actor is not intended for conversation
- topic is relevant but not currently productive

Do not infer too much from one no-reply response.

## Ambient Text Inside Ask Output

Ask output often includes ambient or NPC-adjacent narration after the direct result.

Examples:

    The raven watches you silently from the bust of Pallas.

    The raven caws. "Nevermore!"

    The curtains billow gently in the draft.

These lines are game output, not human chatter.

However, they should usually be split from the direct ask result.

Correct split:

    ask_result:
      There is no reply.

    npc_or_ambient_event:
      The raven watches you silently from the bust of Pallas.

    environmental_ambient_event:
      The curtains billow gently in the draft.

Incorrect extraction:

    topic: lenore
    causes curtains to billow

Only infer causality if repeated evidence supports it.

## Successful Ask With Reply

A successful ask may produce dialogue or clue text.

Example pattern:

    > ask guard about boat

    "The boat leaves at midnight," the guard says.

Possible extraction:

    command: ask guard about boat
    actor: guard
    topic: boat
    reply_received: true
    clue:
      boat leaves at midnight

## Failed Ask Or Unproductive Ask

A failed or unproductive ask may still be parser-valid.

Example:

    > ask raven about key

    There is no reply.

Possible extraction:

    command: ask raven about key
    actor: raven
    topic: key
    reply_received: false
    state_change: false

Do not classify this as an unknown command.

## Actor Not Present Or Not Recognized

Possible responses:

    You can't see any raven here.
    There is no one here by that name.
    You see no such person.

Classify as an ask attempt with failed actor resolution.

Possible extraction:

    command: ask raven about key
    result: failed
    reason: actor_not_visible_or_not_present
    actor: raven
    topic: key

## Topic Not Recognized

Possible responses:

    The raven has nothing to say about that.
    The guard doesn't know anything about the key.
    That topic means nothing to him.

Classify as ask with unproductive or unknown topic.

Possible extraction:

    actor: raven
    topic: key
    result: no_useful_reply
    topic_productive: false_or_unknown

## Do Not Confuse With

Human chatter:

    Transcript-side comments from players are not game commands.

Say:

    `say X` speaks words, often to yourself unless an addressee is given.

Tell:

    `tell ACTOR about TOPIC` gives information to an actor. No real example observed yet in this corpus.

Give:

    `give OBJECT to ACTOR` attempts object transfer. See `give.md`.

Show:

    `show OBJECT to ACTOR` presents an object to an actor. See `give.md`.

Directed NPC command:

    `ACTOR, COMMAND` asks an actor to perform an action. See `npc_command.md`.

Examine:

    `x ACTOR` describes the actor.

Ambient events:

    Raven movement, curtains, tapping, and weather may occur after an ask result but are not automatically caused by it.

## Rule Of Thumb

If the player types `ask ACTOR about TOPIC`, classify the interaction as conversation/ask.

Extract the actor, topic, response, and any state or information change.

Keep no-reply interactions because they still show recognized actors, attempted topics, and conversation behavior.

Split unrelated ambient narration from the direct ask result.
