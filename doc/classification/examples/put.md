# Interaction Type: Put / Place Object In Or On Target

## Summary

The `put` command attempts to move an object into, onto, around, under, behind, or otherwise onto/into relation with another object.

Common command shape:

    put OBJECT PREPOSITION TARGET

Examples:

    put resin in pipe
    put coin in slot
    put book on table
    put ring on finger
    put cloak around shoulders
    put key under mat

This interaction is highly useful for inventory, containment, supporter, puzzle, and state-change mining.

## Canonical Examples

Input:

    > put resin in pipe

Output:

    You need to be holding opium resin before you can put it into something
    else.

    A staccato rap echoes through the room.

    The sense of awful weariness grows stronger and heavier every moment.

    >

Input:

    > Put resin in pipe

Output:

    You put opium resin into the opium pipe.

    A dull, dark weariness drifts over you.

    >

## Classification

    interaction_type: put_action
    command_family: put
    world_model_relevant: true
    puzzle_relevant: possibly
    inventory_relevant: true
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: action/put

## Common Input Forms

Commands in this family include:

    put resin in pipe
    put opium resin into opium pipe
    put coin in slot
    put book on table
    put ring on finger
    put cloak around shoulders
    put key under mat
    put paper behind painting
    insert coin in slot
    insert key into lock
    place book on table
    drop coin in well

Normalize obvious variants carefully:

    put X into Y -> put X in Y
    place X on Y -> put X on Y
    insert X into Y -> put X in Y

Do not over-normalize when the game treats the verb specially.

## Recognize This Type By

The command usually starts with:

    put

and includes:

    object being moved
    preposition
    destination or target

Common prepositions:

    in
    into
    on
    onto
    around
    under
    beneath
    behind
    inside
    through

The response may indicate:

- the object was placed successfully
- the player is not holding the object
- the destination cannot contain/support it
- the object does not fit
- the target is closed
- the target is not available
- the command requires a different preposition
- the action triggers a puzzle effect

## What To Mine

Put responses are useful for extracting:

- movable objects
- containers
- supporters
- wearable/body targets
- required inventory
- object relationships
- failed placement attempts
- successful containment changes
- puzzle mechanisms
- preposition-specific affordances

From the examples:

    failed_put:
      command: put resin in pipe
      object: resin
      resolved_object: opium resin
      preposition: in
      target: pipe
      resolved_target: opium pipe
      result: failed
      reason: player_not_holding_object
      required_inventory:
        - opium resin

    successful_put:
      command: put resin in pipe
      object: resin
      resolved_object: opium resin
      preposition: in
      target: pipe
      resolved_target: opium pipe
      result: success
      state_change: true
      new_relation:
        opium resin:
          contained_in: opium pipe

## Object Versus Destination

In:

    put resin in pipe

The moved object is:

    resin

The destination is:

    pipe

The preposition is:

    in

Do not treat both nouns as equal targets.

Possible extraction:

    command:
      verb: put
      object: resin
      preposition: in
      destination: pipe

## Inventory Requirement

Many games require the player to be holding the object before putting it somewhere.

Example:

    You need to be holding opium resin before you can put it into something else.

This means:

    command understood: true
    object recognized: true
    target likely recognized: true
    state_change: false
    failure_reason: object_not_in_inventory

It does not mean the command is invalid.

It does not mean the pipe cannot hold resin.

It means the player must first take or otherwise acquire the resin.

## Successful Put

Example:

    You put opium resin into the opium pipe.

Possible extraction:

    result: success
    state_change: true
    object_moved: opium resin
    destination: opium pipe
    relation_after:
      opium resin contained_in opium pipe

If the object was previously in inventory, successful put may remove it from direct inventory and place it inside/on the destination.

## Preposition Matters

Different prepositions imply different relationships.

    put X in Y
      X is contained inside Y

    put X on Y
      X is supported by Y

    put X around Y
      X surrounds or is worn around Y

    put X under Y
      X is beneath Y, possibly hidden

    put X behind Y
      X is behind Y, possibly hidden

Do not collapse all put commands into generic containment.

## Some Engines Are Specific

Some games give precise failure reasons.

Example:

    You need to be holding opium resin...

This gives strong evidence about the missing precondition.

Other games may give vague responses:

    That won't work.
    You can't do that.
    Nothing happens.

Classify these as put attempts, but mark the reason as unknown unless the output explains it.

## Case Does Not Matter

These are equivalent unless the game proves otherwise:

    put resin in pipe
    Put resin in pipe
    PUT RESIN IN PIPE

Normalize command case for classification.

Preserve original casing only for transcript fidelity.

## State Guidance

Successful put usually changes object location or relation.

Possible state change:

    object:
      location_before: player_inventory
      location_after: inside_or_on_target

    target:
      contains_or_supports:
        - object

Failed put usually does not change state.

Possible failed state:

    state_change: false
    reason: not_holding_object

## Puzzle Guidance

Put interactions are often puzzle-relevant.

They may indicate:

- ingredient placement
- machine loading
- container use
- ritual arrangement
- key/lock mechanics
- object combination
- wearable/equipment use
- hidden placement
- environmental manipulation

From this example, `put resin in pipe` is likely puzzle-relevant because it combines opium resin with the opium pipe.

## Ambient Text Inside Put Output

Put output may include unrelated ambient narration after the action result.

Examples:

    A staccato rap echoes through the room.

    A dull, dark weariness drifts over you.

    The sense of awful weariness grows stronger and heavier every moment.

These lines are game output, not chatter.

However, they should usually be split from the put result unless the response clearly links them causally.

Correct split:

    put_result:
      You put opium resin into the opium pipe.

    ambient_or_status_event:
      A dull, dark weariness drifts over you.

Incorrect extraction:

    opium pipe:
      causes dull dark weariness

Only infer causality if repeated evidence supports it.

## Do Not Confuse With

Take:

    Moves an object into inventory.

Drop:

    Removes an object from inventory and places it in the current location.

Insert:

    Often equivalent to put-in, but may be a distinct verb in some games.

Wear:

    Puts clothing or equipment on the player.

Open:

    Opens a container, passage, or covering.

Use:

    Generic command that may resolve to put, insert, unlock, light, or another action.

Examine:

    Describes an object.

Ambient events:

    Tapping, weariness, raven behavior, curtains, and weather are game output but not automatically part of the put action.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the player types `put X in Y`, `put X on Y`, or another `put X PREPOSITION Y` shape, classify the pair as action/put.

Extract the moved object, preposition, destination, result, and any object-location state change.

If the game says the player must be holding the object first, classify it as a recognized failed put with a missing-inventory precondition.