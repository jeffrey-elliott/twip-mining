# Interaction Type: Again / Repeat Previous Command

## Summary

The `again` command repeats the last executed command, if the game can resolve it.

The common short form is `g`.

`again` is not a normal in-world action by itself. It is a command wrapper.

To classify an `again` interaction, keep both:

    surface_command: g
    resolved_command: previous command
    resolved_interaction_type: previous interaction type

For example, if the previous command was `read pharmacopia`, then `g` should be treated as another `read pharmacopia`.

## Canonical Examples

Previous command:

    > read pharmacopia

Then:

    > g

Output:

    You hunt feverishly through the pages of Adams' Pharmacopia, and
    discover:

    "The leaf of the coca plant is a mild stimulant and is most effective
    when prepared as a herbal tonic for the refreshment of body and mind
    during times of great fatigue. However, excessive use without pause for
    recuperation of stamina may cause mental or bodily collapse."

    The raven eyes you balefully.

    >

Then:

    > g

Output:

    You hunt feverishly through the pages of Adams' Pharmacopia, and
    discover:

    "Opium is beneficial generally as an hypnotic and sedative; it induces
    a state of sleepfulness and promotes vivid and imaginative dreams. It
    has few side effects beyond the occasional tendency toward
    hallucinations and sleepwalking, though care should be taken not to
    prescribe it for long periods. In times of extreme stress and panic it
    can be an essential restorative to calm the mind."

    The raven caws. "Nevermore!"

    The curtains billow gently in the draft.

    >

## Classification

    interaction_type: repeat_previous_command
    command_family: again
    world_model_relevant: depends_on_resolved_command
    puzzle_relevant: depends_on_resolved_command
    state_change_expected: depends_on_resolved_command
    state_observation_expected: depends_on_resolved_command
    transcript_noise: false
    keep_as_command_pair: true
    short_label: command/again

## Common Input Forms

Commands in this family include:

    again
    g

Normalize these to:

    again

But also resolve them to the previous executable command.

## Recognize This Type By

The player command is exactly:

    g

or:

    again

The output will usually resemble the result of the previous command family.

For example:

    > read pharmacopia
    > g

The `g` output should be interpreted as another read of `pharmacopia`.

## What To Mine

Useful for:

- repeated command behavior
- repeated-read sequences
- retry behavior
- repeated failed actions
- action loops
- state changes caused by repeated actions
- commands whose output changes across repetitions

For each `again` command, mine two layers:

    surface_command:
      command: g
      normalized: again

    resolved_command:
      command: read pharmacopia
      interaction_type: read_text

## Resolution Rule

`again` should inherit the most recent command that the game accepted as executable.

Example:

    previous_executable_command: read pharmacopia
    current_surface_command: g
    resolved_command: read pharmacopia
    resolved_interaction_type: read_text

Do not classify the output as a new unknown command just because the input is `g`.

## Repeated Output May Differ

The repeated command may return different output.

This does not mean `g` is a different command.

In this example, repeated `g` commands continue reading Adams' Pharmacopia and reveal different entries.

Possible extraction:

    command_sequence:
      - read pharmacopia
      - read pharmacopia
      - g resolved as read pharmacopia
      - g resolved as read pharmacopia

    repeated_read_entries:
      - hemp / hasheesh
      - peyote
      - coca
      - opium

## State Guidance

The state behavior depends on the resolved command.

If `g` repeats `read pharmacopia`, then apply read-command state guidance.

If `g` repeats `open door`, then apply open-command state guidance.

If `g` repeats `take lamp`, then apply take-command state guidance.

Generic extraction:

    surface_command: g
    normalized_command: again
    resolved_command: previous executable command
    state_change_expected: inherited_from_resolved_command

## Failure Cases

Sometimes `again` may fail.

Possible outputs:

    You can hardly repeat that.
    You haven't done anything yet.
    That cannot be repeated.
    Please give a command first.

These should still be classified as command/again, but with a failed repeat result.

Possible extraction:

    command: again
    result: cannot_repeat
    resolved_command: none

## Ambient Text Inside Again Output

Because `again` repeats another command, its output may include ambient narration.

Examples:

    The raven eyes you balefully.

    The curtains billow gently in the draft.

These lines are game output, not chatter.

Classify them separately as ambient event text, not as part of the repeated command's stable object data.

## How To Treat It

This is a valid player command and valid game response.

Do not classify `g` as chatter.

Do not mine `g` as its own in-world action.

Do resolve `g` to the prior executable command before classifying the output.

Do keep the surface command for transcript fidelity.

## Do Not Confuse With

A literal object named `g`:

    Very rare. Only consider this if the game clearly treats `g` as a noun.

Quit:

    In some contexts `q` means quit, but `g` means again.

Movement abbreviations:

    Direction shortcuts are usually n, s, e, w, u, d, not g.

Human chatter:

    Transcript-side human comments are not game commands.

## Rule Of Thumb

If the player types `g` or `again`, classify the surface command as command/again, then resolve it to the previous executable command and classify the actual output according to that resolved command.