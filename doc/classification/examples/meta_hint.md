# Interaction Type: Hint / Puzzle Help Menu

## Summary

The `hint` command is a meta command that opens the game's hint/help system.

It is not an in-world action. It does not describe something the player character observes directly.

However, it may be puzzle-relevant because it can reveal topics, goals, puzzle areas, or explicit solution guidance.

## Canonical Example

Input:

    > hint

Output:

    Nevermore Hints

    N = next subject                         P = previous
    RETURN = read subject                    Q = resume game

      > Beginnings
        Study
        Hall
        Drugs
        Books
        Raven
        Lightning
        Blood and Tears
        Laboratory
        Ritual
        Endgame

## Classification

    interaction_type: hint_menu
    command_family: meta
    world_model_relevant: false
    puzzle_relevant: true
    state_change_expected: meta_mode_only
    state_observation_expected: false
    transcript_noise: false
    keep_as_command_pair: true
    short_label: meta/hint-menu

## Common Input Forms

Commands in this family include:

    hint
    hints
    help

Some games may use `help` for general instructions instead of puzzle hints. Classify based on the response.

## Recognize This Type By

The response may include:

- a hint menu
- puzzle topic headings
- navigation instructions
- commands such as N, P, RETURN, Q
- progressive hint subjects
- spoiler-like solution text
- out-of-world advice to the player

Common hint-menu phrases:

    Hints
    Next subject
    Previous
    Read subject
    Resume game
    Choose a topic
    Select a hint

## What To Mine

Useful for:

- puzzle topic taxonomy
- likely puzzle areas
- game structure
- dependency hints
- solution guidance
- identifying endgame topics
- separating spoiler/meta guidance from observed world state

From this example:

    hint_topics:
      - Beginnings
      - Study
      - Hall
      - Drugs
      - Books
      - Raven
      - Lightning
      - Blood and Tears
      - Laboratory
      - Ritual
      - Endgame

    hint_menu_navigation:
      next_subject: N
      previous_subject: P
      read_subject: RETURN
      resume_game: Q

## What Not To Mine

Do not mine hint text as direct in-world observation.

Do not treat hint topics as objects seen by the player.

Do not treat hint guidance as a completed action.

Do not treat hint text as room description, object description, NPC dialogue, or environmental narration.

For example, the topic:

    Drugs

means there is probably a puzzle/topic involving drugs.

It does not mean the player currently sees drugs, carries drugs, or has solved a drug-related puzzle.

## State Guidance

The `hint` command may change the interface mode by entering a hint menu.

Possible extraction:

    command: hint
    result: hint_menu_opened
    state_change:
      meta_ui_mode: hint_menu
    world_state_change: false

This is a meta/UI state change, not an in-world state change.

## Special Caution For `Q`

Inside the hint menu, `Q` means resume game.

Example:

    Q = resume game

Do not classify this `Q` as quit.

In normal gameplay, `q` may mean quit.

Inside a hint menu, `Q` usually exits the hint system and returns to the game.

Possible extraction:

    context: hint_menu
    command: Q
    meaning: resume_game
    not_quit: true

## Puzzle Relevance

Hints are puzzle-relevant, but they are not evidence that the player discovered something in-world.

Use hint output to understand:

- what puzzles exist
- what topics matter
- what the game considers major sections
- possible intended solution paths

Do not use hint output as proof that:

- an item has been examined
- a room has been visited
- an object is visible
- a state transition occurred
- the player learned something diegetically

## Do Not Confuse With

About/credits/version:

    These describe the game, author, license, or release.

Inventory:

    This lists what the player carries.

Room descriptions:

    These describe the player's current location.

Examine responses:

    These describe a specific in-world object.

Quit confirmation:

    This asks whether the player wants to quit.

Human chatter:

    These are transcript-side comments from players, not game output.

## Rule Of Thumb

If the player types `hint` and the game opens a menu or gives puzzle help, classify it as meta/hint-menu or meta/hint-content.

Keep it as a valid command/output pair, but do not treat it as in-world narration or observed world state.
