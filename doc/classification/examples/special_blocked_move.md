# Interaction Type: Failed Movement / Blocked By Hazard

## Summary

A movement command may be recognized but blocked by an environmental hazard, missing condition, insufficient resource, fear, darkness, danger, or puzzle gate.

This is still a valid command/output pair.

Failed movement is important for map and puzzle mining because it identifies attempted directions, blocked exits, required conditions, and hazards.

## Canonical Example

Input:

    > d

Output:

    Even with a lamp, you would not chance these stairs in the darkness.
    The merest slip would send you plummeting.

    The coca rush fades, but the sense of alertness remains.

    >

## Classification

    interaction_type: movement_blocked
    command_family: movement
    world_model_relevant: true
    puzzle_relevant: true
    state_change_expected: false
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: movement/blocked-hazard

## Common Input Forms

Blocked movement may occur after any movement command:

    n
    north
    s
    south
    e
    east
    w
    west
    ne
    northeast
    nw
    northwest
    se
    southeast
    sw
    southwest
    u
    up
    d
    down
    in
    out
    enter
    exit
    go down
    climb down
    descend stairs
    go through door

## Recognize This Type By

The command is a movement command, but the player does not arrive in a new room.

The response may mention:

- darkness
- danger
- fear
- falling
- locked doors
- closed doors
- blocked passages
- missing light
- insufficient light
- missing tools
- missing permission
- unsafe conditions
- unwillingness to proceed

Common response patterns:

    You can't go that way.
    You cannot go that way.
    It is too dark.
    You would not chance it.
    The way is blocked.
    The door is closed.
    The door is locked.
    You need more light.
    You would fall.
    You cannot safely proceed.

## What To Mine

Useful for extracting:

- attempted exit direction
- blocked direction
- hazard
- missing or insufficient condition
- possible puzzle gate
- environmental danger
- movement constraints
- room graph negative evidence

From this example:

    movement_attempt:
      command: d
      normalized_direction: down
      result: blocked
      destination_room: unknown
      state_change: false

    blocker:
      type: hazard
      details:
        - darkness
        - dangerous stairs
        - risk of falling

    light_state:
      lamp_present_or_available: true
      lamp_sufficient: false

    possible_puzzle_gate:
      condition_needed: safer way to descend or improved visibility
      exact_solution: unknown

## Important: Blocked Does Not Mean Invalid

Do not classify this as an unknown command.

The game understood `d` as `down`.

The movement failed because conditions were not right.

Correct:

    command: d
    normalized_command: down
    result: movement_blocked

Incorrect:

    command: d
    result: unknown_command

## Insufficient Resource Versus Missing Resource

Be precise.

Example:

    Even with a lamp, you would not chance these stairs in the darkness.

This does not mean:

    player_has_no_lamp: true

It suggests:

    lamp_exists_or_is_present: true
    lamp_not_enough_to_make_stairs_safe: true
    darkness_or_danger_still_blocks_movement: true

Do not infer that the player lacks a light source when the text says they have one or that even one is insufficient.

## Ambient Or Status Text

The output may include status changes unrelated to the movement failure.

Example:

    The coca rush fades, but the sense of alertness remains.

This is game output, not chatter.

However, it should be separated from the movement blocker.

Correct split:

    movement_result:
      Even with a lamp, you would not chance these stairs in the darkness.
      The merest slip would send you plummeting.

    status_effect:
      The coca rush fades, but the sense of alertness remains.

## Related Interaction: Wrong Inferred Action

Sometimes a movement-blocking message suggests an action to the player, but the inferred action is not actually the solution.

Example:

    The merest slip would send you plummeting.

A player may infer:

    > jump

Output:

    The cold night beckons seductively, but you resist. There is work you
    must be about.

    Lightning forks the sky overhead, followed immediately by clamouring
    thunder.

    >

This is a recognized action, but not the correct solution to the blocked movement problem.

## Classification For Jump Example

    interaction_type: action_attempt_wrong_solution
    command_family: physical_action
    world_model_relevant: true
    puzzle_relevant: true
    state_change_expected: false
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: action/recognized-wrong-solution

## What To Mine From Jump

    command:
      verb: jump
      result: refused_or_resisted
      recognized_by_game: true
      state_change: false

    puzzle_inference:
      player_may_have_inferred_jump_from_previous_text: true
      jump_is_not_solution_here: true

    ambient_event:
      Lightning forks the sky overhead, followed by thunder.

## Recognized But Wrong

A command can be recognized by the parser and still fail as a solution.

Examples:

    jump
    climb
    push
    pull
    break
    attack
    yell
    pray
    wait

The response may be custom prose, not a parser error.

Classify these as valid attempted actions, not unknown commands.

## Do Not Over-Infer

From:

    The merest slip would send you plummeting.

Do not infer:

    jump is required

From:

    The cold night beckons seductively, but you resist.

Do infer:

    jump was understood
    player did not jump
    no successful movement occurred
    likely wrong action or unsafe action

## Do Not Confuse With

Successful movement:

    A new room name and room description appear.

Unknown command:

    The parser says it does not understand the verb.

Generic failure:

    The action fails, but not because of movement or passage blocking.

Ambient events:

    Lightning, thunder, drug effects, raven behavior, and weariness may appear after the result but are not necessarily caused by the command.

Human chatter:

    Transcript-side comments are not game output.

## Rule Of Thumb

If the player enters a direction like `d` and the game explains why travel is unsafe or impossible, classify it as movement/blocked-hazard.

If the player then tries a plausible but wrong inferred action like `jump`, classify that as a recognized failed action, not as movement and not as an unknown command.