# Interaction Type: Sniff / Inhale A Substance

## Summary

The `sniff` command attempts to inhale or smell a specific substance closely, as a physical action distinct from ambient `smell` (uncle_zarf_pd.md's "SMELL object", unattested in this corpus) or `listen`.

The command shape is:

    sniff TARGET

This is world-model relevant when the target is a consumable, since it can be a state-changing action (the substance is used up) with an effect on the player (see the "Do Not Confuse With" note on temporary status effects below).

## Canonical Examples

Input:

    > x coca

Output:

    A white powder consisting of an extract of the South American coca
    leaf, which an acquaintance in Mexico has found a new process of
    refining.

    >

Input:

    > Snort coke

Output:

    [snort -> short]
    I only understood you as far as wanting to short.

    >

Input:

    > sniff coca

Output:

    You inhale a quantity of coca powder.

    A sense of raw alertness rushes through your nerves, setting them all
    on edge.

    >

Input (much later in the same transcript, after the coca has been used up):

    > sniff coca

Output:

    You can't see any such thing.

    >

## Classification

    interaction_type: sniff_action
    command_family: sniff
    world_model_relevant: true
    puzzle_relevant: possibly
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: action/sniff

## Common Input Forms

    sniff coca
    sniff TARGET

Player-attempted synonym, not understood by this game's parser:

    snort coke

## Recognize This Type By

The command begins with `sniff` (or a synonym attempt like `snort`).

The response may indicate:

- a successful inhalation with a described physical/mental effect
- a synonym-substitution parser failure (the game guesses a different verb and fails on it)
- the target no longer being present (already consumed)

## What To Mine

Sniff responses are useful for extracting:

- consumable substances and their effects
- verb synonyms the parser does and doesn't accept for the same real-world action
- whether an effect is temporary/decaying (see the status-effect note below)
- evidence that a substance is a limited, consumable resource

From these examples:

    coca:
      sniffable: true
      consumable: true
      effect_on_success: "raw alertness ... on edge"
      synonym_snort_not_understood: true
      eventually_no_longer_present: true

## Synonym Substitution Can Still Fail

`Snort coke` triggers the game's synonym-substitution mechanism ("[snort -> short]"), but the substituted verb ("short") isn't one the parser recognizes for this context, producing "I only understood you as far as wanting to short." -- already a covered `_OBVIOUS_FAILURE_PREFIXES` phrase ("i only understood you as far as").

This is a PARSER_FAILURE, not a comment on whether "snorting coke" is a valid action -- `sniff coca` (a different surface verb, same intent) succeeds moments later in the same transcript. Don't conflate "this exact wording failed" with "this action isn't implemented."

## Consumable Resource: Success Then Later Failure

The *same* command (`sniff coca`) succeeds early in the transcript and fails much later with "You can't see any such thing." -- the standard "target not found" parser_failure phrase, not a new one. This is strong evidence the coca powder is a limited, consumable resource that stops existing in the world after enough uses, not a re-examinable fixed object.

Do not treat every `sniff coca` in a transcript as interchangeable; check each pair's own result text.

## Do Not Confuse With

Examine:

    `x coca` describes the substance without consuming it. See look_or_examine.md.

Eat / Drink:

    uncle_zarf_pd.md's "Eating/Drinking Commands" section -- a related but distinct consumption family (solid food vs. liquid vs. inhaled substance).

Smell (ambient):

    `smell TARGET` (uncle_zarf_pd.md) is passive sensing; unattested in this corpus. `sniff` here is an active inhale-and-consume action.

Temporary status effects:

    A successful sniff introduces a decaying effect that later fades over subsequent turns (e.g. "The coca rush fades, but the sense of alertness remains." several turns after sniffing) -- see doc/annotated_screenshots/floyd_marked_commands.png. Model this as time-decaying player state, not a permanent world-object state change.

## Rule Of Thumb

If the player types `sniff TARGET`, classify it as action/sniff. A successful inhale both changes player status (possibly decaying over subsequent turns) and may consume the target; check later pairs for the same target failing with a standard "not found" phrase before assuming it's still there.
