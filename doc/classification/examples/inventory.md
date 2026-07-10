# Interaction Type: Inventory / Carried Items List

## Summary

The `inventory` command, often shortened to `i`, asks the game to list what the player character is currently carrying or wearing.

This is a real command/output pair and is highly useful for inventory-state mining.

The command does not usually change game state, but it reveals the player's current possessions and sometimes the state of those possessions.

## Canonical Examples

Input:

    > I

Output:

    You are carrying:
      opium resin
      an opium pipe
      a peyote button
      Concerning Immortality
      an oil-lamp (providing light)
      a paper sachet (which is open)
        coca powder
      a gold ring (being worn)

    A dull, dark weariness drifts over you.

    >

Input:

    > i

Output:

    You are carrying:
      a gold ring (being worn)

    A staccato rap echoes through the room.

    >

## Classification

    interaction_type: inventory_listing
    command_family: inventory
    world_model_relevant: true
    puzzle_relevant: possibly
    state_change_expected: false
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: inventory/list

## Common Input Forms

Commands in this family include:

    inventory
    inv
    i
    I

Normalize these to:

    inventory

## Recognize This Type By

The output usually begins with:

    You are carrying:

It then lists carried or worn objects, often one per line.

Inventory entries may include parenthetical state notes, such as:

    an oil-lamp (providing light)
    a paper sachet (which is open)
    a gold ring (being worn)

Inventory entries may also show containment by indentation.

Example:

    a paper sachet (which is open)
      coca powder

This means the player is carrying the sachet, and the sachet contains coca powder.

## What To Mine

Inventory responses are useful for extracting:

- objects currently carried by the player
- objects currently worn by the player
- object state
- light-source state
- open/closed container state
- contained inventory items
- player possessions at a particular point in the transcript
- possible puzzle resources available to the player

From the first example:

    player_inventory:
      carried:
        - opium resin
        - opium pipe
        - peyote button
        - Concerning Immortality
        - oil-lamp
        - paper sachet
        - gold ring

      worn:
        - gold ring

      providing_light:
        - oil-lamp

      containers:
        paper sachet:
          state: open
          contains:
            - coca powder

From the second example:

    player_inventory:
      carried:
        - gold ring

      worn:
        - gold ring

## State Guidance

Inventory commands usually do not change state.

They reveal existing state.

Example:

    a paper sachet (which is open)

This should be treated as an observed state:

    object: paper sachet
    state_observed:
      open: true

Not as:

    state_change:
      opened_by_inventory_command: true

## Worn Items

Parenthetical text like this:

    (being worn)

means the item is on the player, but in a worn/equipped state.

Possible extraction:

    object: gold ring
    carried_by_player: true
    worn_by_player: true

Do not treat worn items as absent from inventory.

## Light Sources

Parenthetical text like this:

    (providing light)

means the item is actively producing light.

Possible extraction:

    object: oil-lamp
    carried_by_player: true
    light_source: true
    currently_lit_or_providing_light: true

This may be puzzle-relevant.

## Contained Items In Inventory

Indented lines under an inventory item usually indicate containment.

Example:

    a paper sachet (which is open)
      coca powder

Possible extraction:

    object: paper sachet
    carried_by_player: true
    open: true
    contains:
      - coca powder

    object: coca powder
    contained_in: paper sachet
    indirectly_carried_by_player: true

## Ambient Text Inside Inventory Output

Inventory output may include unrelated ambient narration after the carried-items list.

Examples:

    A dull, dark weariness drifts over you.

    A staccato rap echoes through the room.

These lines are game output, not chatter.

However, they should usually be classified separately as ambient event text, not as inventory contents.

## How To Treat It

This is a valid player command and valid game response.

Do not classify it as chatter.

Do not discard it because it is a meta-like command.

Do not treat it as an in-world physical action.

Do separate:

    Inventory list:
      You are carrying:
        a gold ring (being worn)

    Ambient event:
      A staccato rap echoes through the room.

## Do Not Confuse With

Room descriptions:

    These describe what is visible in the current location.

Examine responses:

    These describe one specific object in more detail.

Taking/dropping actions:

    These change what the player carries.

Meta commands:

    These describe the game, author, help system, version, or license.

Human chatter:

    These are transcript-side comments from players, not game output.

## Rule Of Thumb

If the player types `i`, `I`, `inv`, or `inventory`, and the game responds with “You are carrying:”, classify the pair as inventory/list.

Mine the carried objects and parenthetical state notes, but split off any atmospheric narration that follows the list.