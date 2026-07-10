# Interaction Type: Death / Game Over / Restart Cycle

## Summary

Some command/output pairs end in a terminal game-state event such as death, loss, victory, or forced restart.

This is different from ordinary failed action output.

A death/game-over response may include ordinary-looking output first: room description, ambient events, status effects, dream text, or delayed consequences from earlier actions.

Do not assume the immediately preceding command is the sole cause of death.

## Canonical Example: Death After Prior Conditions

Input:

    > out

Output:

    Study

    Stone walls, wreathed in shadows and velvet curtains, rise into the
    gloom overhead. The old oak writing desk -- once your father's, now
    your own -- is wedged beneath the window lattice, with a velvet couch
    before it. A low fire smoulders in its ancient hearth. To the
    southeast, a bust of Pallas sits atop an arch with darkness beyond.

    A staccato rap echoes through the room.

    A bone-deep weariness seizes you, and you are unable to take another
    step. Your eyes close, you slump against the stone, and darkness
    overwhelms your mind.

    Slowly, the dream begins to darken. There are screams, echoes,
    footsteps running down nameless corridors. Your feet are cold on
    haunted stone, forever following Lenore's distant echo, forever
    pursued...

    The dream fades to reality. A confusion of images; a precipice,
    falling... and then your head strikes stone, and reality ends.

    It is a dangerous place, this tower, to dream alone.

        *** You have died ***

    Would you like to RESTART, RESTORE a saved game or QUIT?

    >

## Canonical Example: Restart After Death

Input:

    > restart

Output:

    NEVERMORE
    An Interactive Gothic
    by Nate Cull. 2000. Type ABOUT for instructions.
    Release 10 / Serial number 000928 / Inform v6.21 Library 6/10

    Study (on the velvet couch)
    Stone walls, wreathed in shadows and velvet curtains, rise into the
    gloom overhead. The old oak writing desk -- once your father's, now
    your own -- is wedged beneath the window lattice, with a velvet couch
    before it. A low fire smoulders in its ancient hearth. To the
    southeast, a bust of Pallas sits atop an arch with darkness beyond.

    >

## Classification: Death / Game Over

    interaction_type: terminal_game_state
    command_family: varies
    world_model_relevant: true
    puzzle_relevant: true
    state_change_expected: true
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: terminal/death

## Classification: Restart

    interaction_type: restart_game
    command_family: meta
    world_model_relevant: false
    puzzle_relevant: false
    state_change_expected: true
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: meta/restart

## Recognize Death / Game Over By

Strong markers:

    *** You have died ***
    You have died
    You are dead
    Game over
    You have lost
    You have failed
    The End

Post-death prompt markers:

    Would you like to RESTART, RESTORE a saved game or QUIT?
    RESTART, RESTORE or QUIT?
    Press any key to restart
    Restore a saved game?

## What To Mine From Death

Useful for extracting:

- terminal game states
- losing conditions
- danger states
- delayed consequences
- status-effect consequences
- unsafe locations or actions
- puzzle failure conditions
- restart/restore/quit handling

From this example:

    terminal_event:
      type: death
      marker: "*** You have died ***"

    immediate_command:
      surface: out
      command_family: movement_or_exit
      direct_cause_of_death: uncertain

    observed_conditions:
      - bone-deep weariness
      - unable to take another step
      - dream overtakes player
      - fall or dream/fall imagery
      - dangerous to dream alone in the tower

    known_or_likely_prior_cause:
      - opium use
      - wandering after opium use
      - sleep/dream state away from safety

    game_over_options:
      - RESTART
      - RESTORE
      - QUIT

## Do Not Over-Attribute Cause

The command immediately before death is not always the true cause.

In this example, the surface command is:

    out

But the death likely comes from a prior chain:

    player used opium
    player wandered around
    drug/sleep/weariness effect advanced
    player collapsed/dreamed in an unsafe place
    death occurred

Correct extraction:

    immediate_trigger_command: out
    terminal_state: death
    causal_link_to_immediate_command: uncertain
    possible_prior_causes:
      - opium
      - dream state
      - exhaustion/weariness
      - unsafe place to sleep/dream

Incorrect extraction:

    out:
      always_causes_death: true

## Split The Output Into Layers

This example contains multiple output layers.

Layer 1: room/location output

    Study
    Stone walls, wreathed in shadows...

Layer 2: ambient event

    A staccato rap echoes through the room.

Layer 3: status consequence

    A bone-deep weariness seizes you...

Layer 4: dream/death narration

    Slowly, the dream begins to darken...

Layer 5: terminal marker

    *** You have died ***

Layer 6: post-game menu

    Would you like to RESTART, RESTORE a saved game or QUIT?

Do not merge all of these into a room description.

## Restart Command

After death, the player may type:

    restart

This is a meta command.

It resets the game to the beginning or a starting state.

It is not an in-world action.

It is not movement.

It is not room discovery in the ordinary playthrough sense, although the resulting starting room description can be mined as the initial room state.

## What To Mine From Restart

Useful for:

- game title
- author
- release/version metadata
- starting room
- starting player position
- initial visible scenery
- reset behavior

From this example:

    game:
      title: NEVERMORE
      subtitle: An Interactive Gothic
      author: Nate Cull
      release: 10
      serial: 000928
      system: Inform v6.21 Library 6/10

    restart_result:
      game_state_reset: true
      starting_room: Study
      starting_position: on the velvet couch

    initial_room:
      name: Study
      visible_objects:
        - velvet curtains
        - old oak writing desk
        - window lattice
        - velvet couch
        - hearth
        - bust of Pallas
        - arch

## Death Prompt Commands

After death, these commands may be valid in the post-game prompt:

    restart
    restore
    quit

These should be classified as post-game meta commands.

They are not ordinary in-world commands while the game is waiting at the death prompt.

## State Guidance

Death:

    state_change: true
    player_alive: false
    game_continuable_without_restart_or_restore: false
    post_game_prompt_active: true

Restart:

    state_change: true
    game_state_reset: true
    player_alive: true
    post_game_prompt_active: false
    inventory_reset: likely
    world_state_reset: likely

Do not assume exact inventory/world reset details unless later output confirms them.

## Relationship To Movement

The death-producing command may be a movement command.

Example:

    > out

If the output includes a room heading before death, it may mean the movement or exit command succeeded first, then a delayed death condition fired.

Possible extraction:

    command: out
    movement_result: maybe_successful
    location_after_or_current: Study
    terminal_event_after_command: death

Use caution if the previous location is unknown.

## Relationship To Status Effects

Death may be caused by accumulated or delayed status effects.

Common status-effect clues:

    weariness
    sleep
    dream
    poison
    hunger
    thirst
    bleeding
    darkness
    drowning
    falling
    drug effects
    exhaustion

In this example:

    opium/dream/weariness chain appears more important than the literal `out` command.

## Do Not Confuse With

Failed movement:

    The player is blocked but remains alive.

Recognized wrong action:

    The command fails, but play continues.

Ambient narration:

    Atmospheric text does not itself imply death unless terminal markers appear.

Room description:

    Room prose before death is not the whole interaction type.

Quit:

    Quit asks whether to end the session; death is an in-game terminal state.

Restart:

    Restart resets the game after death or by player choice.

Human chatter:

    Transcript-side comments are not game output.

## Rule Of Thumb

If output contains `*** You have died ***` or an equivalent terminal marker, classify the interaction as terminal/death, regardless of the command that came before it.

Record the immediate command, but do not assume it was the root cause.

If the player then types `restart`, classify that as meta/restart and treat the following banner plus room description as the reset starting state.