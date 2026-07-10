# Interaction Type: Magic Word / Easter Egg Command

## Summary

Some interactive fiction games recognize traditional magic words from earlier text adventures.

These commands may be implemented as jokes, homages, easter eggs, puzzle commands, teleport commands, or atmospheric responses.

`XYZZY` is the classic example.

Common command shape:

    MAGIC_WORD

Example:

    xyzzy

## Canonical Example

Input:

    > xyzzy

Output:

    The name of old, lost magic briefly echoes, then is gone.

    The gentle tapping sounds again.

    >

## Classification

    interaction_type: magic_word
    command_family: special_command
    world_model_relevant: possibly
    puzzle_relevant: rarely_or_game_specific
    state_change_expected: usually_false
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: special/magic-word

## Common Input Forms

Classic magic-word commands may include:

    xyzzy
    plugh
    plover

Game-specific magic words may also appear.

Do not require the command to be a normal verb phrase.

A one-word command can still be valid if the game recognizes it.

## Recognize This Type By

The command is usually a bare word with no target.

The output may mention:

- old magic
- lost magic
- echoes
- nothing happening
- a joke response
- a homage to older games
- teleportation
- spell effects
- puzzle effects

Common response patterns:

    A hollow voice says...
    Nothing happens.
    The word echoes...
    The magic has faded.
    You are transported...
    The name of old, lost magic briefly echoes...

## What To Mine

Useful for:

- recognized special commands
- easter eggs
- homage behavior
- magic vocabulary
- possible puzzle verbs
- possible teleport/spell mechanics
- command taxonomy

From this example:

    command:
      surface: xyzzy
      type: magic_word
      recognized_by_game: true

    result:
      prose_response: The name of old, lost magic briefly echoes, then is gone.
      state_change: false_or_unclear
      puzzle_effect: none_observed

## Recognized Does Not Mean Puzzle-Relevant

This response proves that the game recognizes `xyzzy`.

It does not prove that `xyzzy` solves a puzzle.

In this example, the response sounds atmospheric or referential, with no clear state change.

Possible extraction:

    xyzzy:
      recognized: true
      likely_easter_egg: true
      state_change_observed: false
      puzzle_relevance: unknown_or_low

## Magic Word Versus Unknown Command

Do not classify this as an unknown command.

An unknown command usually produces parser failure text, such as:

    I don't know the word "xyzzy".

But this output is custom prose:

    The name of old, lost magic briefly echoes, then is gone.

That means the command was understood.

## Magic Word Versus Normal Action

Do not force `xyzzy` into a verb/target structure.

Incorrect:

    verb: xyzzy
    target: none
    action_type: physical_action

Better:

    command_family: special_command
    interaction_type: magic_word
    surface_command: xyzzy

## Possible State Changes In Other Games

Some games may make magic words actually do something.

Possible effects:

    teleport player
    open passage
    reveal object
    trigger spell
    change room state
    print joke only
    do nothing

Classify by response.

If the magic word changes location, also record movement or teleportation.

If it reveals an object, record a reveal event.

If it only prints flavor text, record no clear state change.

## Ambient Text Inside Magic Word Output

Magic-word output may include unrelated ambient narration after the direct response.

Example:

    The gentle tapping sounds again.

This is game output, not chatter.

However, it should usually be split from the magic-word response.

Correct split:

    command_result:
      The name of old, lost magic briefly echoes, then is gone.

    ambient_event:
      The gentle tapping sounds again.

Incorrect extraction:

    xyzzy:
      causes_tapping: true

Only infer causality if repeated evidence supports it.

## Do Not Confuse With

Unknown command:

    Parser does not recognize the word.

Meta command:

    Commands like about, help, hint, save, restore, quit.

Movement:

    Direction commands like n, s, e, w, up, down.

Spells:

    Game-specific magic systems may use cast, say, invoke, pray, or speak.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the player types a classic or game-specific magic word and the game gives a custom response, classify it as special/magic-word.

Keep it as a valid command/output pair.

Do not assume it matters to the puzzle unless the output shows a concrete effect.