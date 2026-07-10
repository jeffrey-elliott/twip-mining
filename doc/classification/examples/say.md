# Interaction Type: Say / Spoken Text

## Summary

The `say` command makes the player character speak.

It may be directed at no one, at the player character, at an NPC, or at a topic/object. Depending on the game, `say` can behave like conversation, magic-word use, password entry, puzzle input, or simple flavor.

Common command shapes:

    say TEXT
    say TEXT to ACTOR
    say to ACTOR TEXT
    say TEXT about TOPIC
    say about TOPIC to ACTOR

## Canonical Example

Input:

    > say Lenore

Output:

    (to yourself)
    There is no reply.

    There is silence for a moment; then the soft rapping returns.

    >

## Classification

    interaction_type: say_action
    command_family: speech
    world_model_relevant: possibly
    puzzle_relevant: possibly
    npc_relevant: possibly
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: speech/say

## Common Input Forms

Basic speech:

    say Lenore
    say hello
    say nevermore
    say password

Speech to an actor:

    say hello to raven
    say Lenore to raven
    say password to guard

Actor-first speech:

    say to raven hello
    say to guard password

Topic-like speech:

    say Lenore about raven
    say about Lenore to raven

Some games may also support:

    speak
    speak to raven
    talk to raven
    answer Lenore
    shout Lenore
    whisper Lenore

Classify by response.

## Recognize This Type By

The player command begins with:

    say

The output may show:

- who the speech is directed to
- whether anyone replies
- whether the spoken word has an effect
- whether an NPC responds
- whether the game treats the word as a password, spell, name, or topic

Common response patterns:

    (to yourself)
    There is no reply.
    You say, "..."
    The guard ignores you.
    The raven caws.
    Nothing happens.
    The word echoes.
    The door opens.

## What To Mine

Useful for extracting:

- spoken words or phrases
- possible passwords
- possible names with significance
- NPC conversation attempts
- actor-directed speech
- failed speech attempts
- magic or ritual language
- puzzle-relevant utterances

From this example:

    command:
      verb: say
      spoken_text: Lenore
      addressee: yourself

    result:
      reply: none
      state_change: false

    possible_relevance:
      Lenore may be a meaningful name or topic, but this command did not produce a reply.

## Speaking To Yourself

If the game says:

    (to yourself)

then the speech was not directed at an NPC.

Possible extraction:

    addressee: self
    npc_interaction: false
    reply: none

Do not treat this as conversation with Lenore unless the output shows Lenore is present or responding.

## Speech Directed At An NPC

For:

    say hello to raven

extract:

    command:
      verb: say
      spoken_text: hello
      addressee: raven

If the NPC responds, classify it as both speech and NPC interaction:

    interaction_type: say_action
    npc_relevant: true
    actor: raven

## Say Versus Ask

`ask` usually has a topic and an actor:

    ask raven about key

`say` usually has spoken text:

    say key to raven

These may overlap, but they are not identical.

Use the surface command and response to classify.

## Say Versus Magic Word

A bare command like:

    xyzzy

may be a magic-word command.

But:

    say xyzzy

is a speech command that may invoke magic if the game supports spoken magic.

Possible extraction:

    surface_command: say xyzzy
    command_family: speech
    possible_magic_word: xyzzy
    magic_effect: only_if_response_shows_it

## State Guidance

Most `say` commands do not change physical world state.

They may still reveal:

- whether a word is recognized
- whether an NPC will answer
- whether a password works
- whether a ritual phrase matters
- whether the player is speaking to self or someone else

Possible successful puzzle state:

    command: say password to door
    result: door opens
    state_change: true

Possible failed speech state:

    command: say Lenore
    result: no reply
    state_change: false

## Ambient Text Inside Say Output

Say output may include unrelated ambient narration.

Example:

    There is silence for a moment; then the soft rapping returns.

This is game output, not chatter.

However, it should usually be split from the speech result.

Correct split:

    speech_result:
      (to yourself)
      There is no reply.

    ambient_event:
      There is silence for a moment; then the soft rapping returns.

Incorrect extraction:

    Lenore:
      causes soft rapping

Only infer causality if repeated evidence supports it.

## Do Not Confuse With

Ask/tell:

    These usually address an actor about a topic.

NPC command:

    `raven, get object` asks an actor to perform an action.

Magic word:

    A bare word like `xyzzy` may be special even without `say`.

Unknown command:

    Parser does not understand the input.

Ambient events:

    Tapping, curtains, raven behavior, weather, and weariness may occur after the speech result but are not automatically caused by it.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the player types `say X`, classify it as speech/say.

Extract the spoken text, addressee if present, response, and any state change.

If the output says “to yourself,” do not treat it as NPC conversation.
