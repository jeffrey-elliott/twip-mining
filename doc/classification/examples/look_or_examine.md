# Interaction Type: Examine / Object Description

## Summary

The `examine` command, often shortened to `x`, asks the game for a more detailed description of an in-world object, document, person, feature, or piece of scenery.

This is one of the most important interaction types for world mining.

An examine response usually expands the known model of the world by describing what something is, what condition it is in, what it contains, what it suggests, or what related objects are present.

## Canonical Examples

Input:

    > x desk

Output:

    A relic from Byzantine days, perhaps. It was the first piece of
    furniture you touched as a child, and the oldest you have seen in all
    your travels. Simply a slab of polished oak, with four curiously carved
    legs, and nothing more. On the desk are a paper sachet, an oil-lamp and
    Concerning Immortality.

    You hear the tapping sound again.

    >

Input:

    > x sachet

Output:

    A thin paper envelope, of the kind in which exotic substances are
    stored. The sachet is closed.

    There is silence for a moment; then the soft rapping returns.

    >

Input:

    > x immortality

Output:

    "Some Thoughts Concerning Immortality and The Means Thereof", by
    Ambrosius of Cyrene (a copy, not the original, as the pages of this
    slim volume date no earlier than the fifteenth century). A most
    difficult book, but you have returned to its pages many times; surely,
    the key to the whole process must be here, if only you could read its
    meaning.

    A staccato rap echoes through the room.

    >

## Classification

    interaction_type: examine_description
    command_family: examine
    world_model_relevant: true
    puzzle_relevant: possibly
    state_change_expected: usually_false
    transcript_noise: false
    keep_as_command_pair: true
    short_label: examine/object-description

## Common Input Forms

Commands in this family include:

    examine desk
    x desk
    look at desk
    inspect desk
    read book
    x book
    examine paper
    x me
    x him
    x her
    x it

The short command `x` should usually be normalized as `examine`.

## Recognize This Type By

The output usually contains prose describing a specific in-world target in greater detail.

Common signs:

- The input names a specific object, person, document, feature, or scenery item.
- The response gives descriptive prose rather than command help or system metadata.
- The response may reveal contained or related objects.
- The response may describe state, condition, age, material, contents, markings, text, or implied use.
- The response often ends with a prompt.
- The response may include ambient event text after the object description.

## What To Mine

Examine responses are useful for extracting:

- object descriptions
- object aliases
- object materials
- object state
- visible sub-objects
- containment clues
- readable text
- puzzle hints
- affordance hints
- room/world lore
- character knowledge
- object relationships

From this example:

    desk:
      description: Byzantine relic; polished oak slab; four carved legs
      contains:
        - paper sachet
        - oil-lamp
        - Concerning Immortality

    sachet:
      description: thin paper envelope for exotic substances
      state:
        closed: true

    Concerning Immortality:
      type: book
      title: Some Thoughts Concerning Immortality and The Means Thereof
      author: Ambrosius of Cyrene
      state:
        copy_not_original: true
      possible_hint:
        contains key to immortality process, but meaning is not yet understood

## Ambient Text Inside Examine Output

An examine response may include unrelated ambient narration after the main object description.

Examples:

    You hear the tapping sound again.

    There is silence for a moment; then the soft rapping returns.

    A staccato rap echoes through the room.

These lines are still game output, not chatter.

However, they should usually be classified separately as ambient event text, not as part of the examined object's stable description.

## How To Treat It

This is a valid player command and a valid game response.

Do not classify it as chatter.

Do not treat ambient narration as human conversation.

Do not discard the pair just because it includes prose unrelated to the examined object.

Do separate:

    Stable object description:
      A thin paper envelope, of the kind in which exotic substances are stored.
      The sachet is closed.

    Ambient event:
      There is silence for a moment; then the soft rapping returns.

## State Change Guidance

Most examine commands do not change game state.

However, an examine response can reveal state that already exists:

    The sachet is closed.

This should be treated as observed state, not necessarily as a state transition caused by the command.

Possible classification:

    state_change_expected: usually_false
    state_observation_expected: true

## Puzzle Guidance

Examine responses may be puzzle-relevant even when no action succeeds or fails.

They may reveal:

- hidden affordances
- object contents
- readable inscriptions
- locked/open/closed state
- missing parts
- suspicious details
- textual clues
- implied goals

Do not require an obvious success/failure pattern before marking an examine response as puzzle-relevant.

## Do Not Confuse With

Room descriptions:

    These describe the current location as a whole, usually after `look` or movement.

Inventory listings:

    These list what the player carries, usually after `inventory` or `i`.

Meta commands:

    These describe the game, author, help system, version, or license.

Failed interactions:

    These say the player cannot do something, does not see something, or used the wrong command.

Human chatter:

    These are transcript-side comments from players, not game output.

## Rule Of Thumb

If the player asks about a specific in-world thing and the game responds with richer prose about that thing, classify it as examine/object-description.

If extra atmospheric prose appears after the description, keep the command pair, but split the stable description from the ambient event.