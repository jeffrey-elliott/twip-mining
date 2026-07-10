# Interaction Type: Parser Disambiguation / Clarify Ambiguous Target

## Summary

Parser disambiguation happens when the game understands the command shape but cannot determine which matching object the player means.

The game asks a follow-up question, usually listing possible targets.

The player's next input may be a fragment, not a full command. That fragment should be used to complete the pending command.

## Canonical Example

Input:

    > x opium

Output:

    Which do you mean, opium resin or the opium pipe?

    >

Follow-up input:

    > resin

Resolved command:

    > x opium resin

Output:

    A black wad of opium resin for smoking, prepared to a closely-guarded
    Tong formula for maximum potency and speed.

    >

## Classification

    interaction_type: parser_disambiguation
    command_family: parser
    world_model_relevant: true
    puzzle_relevant: possibly
    state_change_expected: pending_resolution
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: parser/disambiguation

## Common Input Forms That Trigger Disambiguation

Any command with an ambiguous noun may trigger this:

    x opium
    examine book
    take key
    open door
    read paper
    give ring to raven
    unlock door with key
    put powder in pipe

The ambiguity is usually in the target noun, but it can also occur in an instrument, recipient, container, or topic.

## Recognize This Type By

The output asks which object the player meant.

Common phrases:

    Which do you mean
    Which one do you mean
    Which do you want
    Do you mean
    Did you mean
    Please be more specific

The output usually lists two or more possible matches:

    opium resin
    opium pipe

## What To Mine

Disambiguation is useful for extracting:

- ambiguous noun aliases
- object names
- parser-recognized objects
- possible object groups
- noun-to-object mappings
- pending command state
- resolved command reconstruction

From this example:

    ambiguous_input:
      surface_command: x opium
      verb: examine
      ambiguous_noun: opium

    candidates:
      - opium resin
      - opium pipe

    follow_up:
      surface_input: resin
      resolves_to: opium resin

    reconstructed_command:
      verb: examine
      target: opium resin

## Follow-Up Inputs Are Often Fragments

After a disambiguation question, the player's next input may not be a full command.

Example:

    > resin

This should not be classified as an unknown command.

It is a clarification answer to the previous parser question.

Correct:

    pending_command:
      verb: examine
      ambiguous_target: opium
      candidates:
        - opium resin
        - opium pipe

    clarification:
      input: resin
      selected_candidate: opium resin

    resolved_command:
      examine opium resin

Incorrect:

    command: resin
    result: unknown command

## Preserve Surface And Resolved Forms

Keep both the literal transcript input and the reconstructed command.

Example:

    surface_input: resin
    resolved_input: x opium resin
    inherited_verb: examine
    selected_target: opium resin

This is important because the transcript says `resin`, but the game is really continuing `x opium`.

## Classification Of The Final Output

Once the ambiguity is resolved, classify the resulting output according to the original command.

In this example, the resolved command is:

    x opium resin

So the final output should also be classified as:

    examine/object-description

Possible extraction:

    interaction_type: examine_description
    target: opium resin
    description:
      A black wad of opium resin for smoking...

## State Guidance

The disambiguation prompt itself usually does not change world state.

It creates a pending parser state:

    parser_state:
      awaiting_disambiguation: true
      pending_command: x opium
      candidates:
        - opium resin
        - opium pipe

The clarification resolves the parser state:

    parser_state:
      awaiting_disambiguation: false
      selected_target: opium resin

The resolved command may then observe or change state depending on its verb.

## Ambiguous Target Evidence

Disambiguation proves that the game recognizes multiple objects matching the ambiguous word.

Example:

    Which do you mean, opium resin or the opium pipe?

This is strong evidence for both objects:

    opium resin:
      recognized_object: true
      aliases:
        - opium
        - resin

    opium pipe:
      recognized_object: true
      aliases:
        - opium
        - pipe

Use caution: the shared word `opium` is an ambiguous noun, not necessarily a unique object.

## Do Not Confuse With

Unknown command:

    The parser does not understand the input at all.

Failed action:

    The command is understood but cannot be performed.

Examine:

    The resolved command may be examine, but the disambiguation prompt itself is parser behavior.

Human chatter:

    Transcript-side comments are not game output.

## Rule Of Thumb

If the game asks “Which do you mean?” and lists possible objects, classify that pair as parser/disambiguation.

Treat the next short input as a clarification if it matches one of the listed options.

Then reconstruct and classify the resolved command using the original verb and the selected target.