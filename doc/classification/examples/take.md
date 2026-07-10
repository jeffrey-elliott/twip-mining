# Interaction Type: Take / Add Object To Inventory

## Summary

The `take` command attempts to pick up an in-world object and add it to the player's inventory.

Common command shapes include:

    take TARGET
    get TARGET
    pick up TARGET
    take TARGET from SOURCE
    take all
    take all from SOURCE
    take all TARGET from SOURCE

This interaction is highly useful for inventory-state and puzzle mining.

A successful take usually means an object moved from the world, a container, or a source object into the player's inventory.

## Canonical Examples

Input:

    > take books

Output:

    There are far too many books to remove them all. You should select a
    volume by name.

    The raven stares down from the stacks.

    >

Input:

    > take all from pallas

Output:

    peyote button: Removed.
    opium pipe: Removed.
    opium resin: Removed.

    There is silence for a moment; then the soft rapping returns.

    The curtains move softly, caressed by the breeze.

    A dull, dark weariness drifts over you.

    >

Input:

    > take all from shelves

Output:

    Ex Sanguine Vita: Removed.
    Adams' Pharmacopia: Removed.
    Inhumanities: Removed.
    Principia Caelestium Mysteriorum: Removed.
    Arts of the Chaldean Magi: Removed.

    The raven pecks at a dusty volume.

    >

## Classification

    interaction_type: take_action
    command_family: take
    world_model_relevant: true
    puzzle_relevant: possibly
    inventory_relevant: true
    state_change_expected: usually
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: action/take

## Common Input Forms

Commands in this family include:

    take lamp
    get lamp
    pick up lamp
    take book
    take all
    take all from shelf
    take all from shelves
    take coin from box
    remove coin from box
    take all books from shelves

Normalize common aliases:

    get X -> take X
    pick up X -> take X

Use caution with `remove`. It may mean take-from, but it may also mean detach, uncover, undress, or manipulate depending on output.

## Recognize This Type By

The player command usually starts with:

    take
    get
    pick up

The response may indicate:

- the object was taken
- the object was removed
- multiple objects were removed
- the object cannot be taken
- the target is too broad
- the player must choose a more specific object
- the object is fixed in place
- the object is already held
- the source/container is empty
- the player cannot carry more

Common success patterns:

    Taken.
    You take the lamp.
    lamp: Removed.
    peyote button: Removed.

Common failure patterns:

    You can't take that.
    That's fixed in place.
    There are far too many books to remove them all.
    You should select a volume by name.
    You already have that.
    You can't carry any more.

## What To Mine

Take responses are useful for extracting:

- portable objects
- inventory additions
- source containers
- object removal from room/container/scenery
- failed take attempts
- disambiguation requirements
- bulk inventory changes
- puzzle resources acquired
- hidden/revealed objects that become takeable

From the examples:

    take books:
      result: failed
      reason: target_too_broad
      target: books
      guidance: select a volume by name
      portable_group: maybe
      individual_books_takeable: likely

    take all from pallas:
      result: success
      source: pallas
      items_removed:
        - peyote button
        - opium pipe
        - opium resin
      inventory_added:
        - peyote button
        - opium pipe
        - opium resin

    take all from shelves:
      result: success
      source: shelves
      items_removed:
        - Ex Sanguine Vita
        - Adams' Pharmacopia
        - Inhumanities
        - Principia Caelestium Mysteriorum
        - Arts of the Chaldean Magi

## Take X

Basic shape:

    take TARGET

Example:

    take lamp

Possible extraction:

    command:
      verb: take
      target: lamp

    result:
      inventory_added:
        - lamp

## Take X From Y

Shape:

    take TARGET from SOURCE

Example:

    take coin from box

Possible extraction:

    command:
      verb: take
      target: coin
      source: box

    result:
      inventory_added:
        - coin
      removed_from:
        coin: box

## Take All

Shape:

    take all

This attempts to take all available takeable objects in the current scope.

Scope may be:

- current room
- open container
- visible supporter
- current implicit source

Possible extraction:

    command:
      verb: take
      target: all
      source: current_scope

## Take All From Y

Shape:

    take all from SOURCE

This attempts to take every takeable object from a named source.

Example:

    take all from shelves

Possible extraction:

    command:
      verb: take
      target: all
      source: shelves

    result:
      items_removed:
        - Ex Sanguine Vita
        - Adams' Pharmacopia
        - Inhumanities
        - Principia Caelestium Mysteriorum
        - Arts of the Chaldean Magi

## Removed Means Taken

Some games report successful taking with:

    ITEM: Removed.

In this context, `Removed.` usually means the item was removed from the source and added to inventory.

Example:

    peyote button: Removed.
    opium pipe: Removed.
    opium resin: Removed.

Possible extraction:

    inventory_added:
      - peyote button
      - opium pipe
      - opium resin

    removed_from_source:
      source: pallas

## Failed Take Due To Broad Target

Example:

    > take books

    There are far too many books to remove them all. You should select a
    volume by name.

This is a failed take, not chatter.

It is also useful world-model evidence.

Possible extraction:

    command: take books
    result: failed
    reason: too_many_matching_objects
    disambiguation_needed: true
    suggested_action: select volume by name
    group_target: books

This implies that individual books may be takeable even though the plural group is not.

## Multi-Command Input Lines

Some transcript lines may contain more than one player command.

Example:

    > move hair. take all from pallas

This should be split before classification:

    command_1:
      surface: move hair
      interaction_type: action/move
      output:
        You tip back the goddess' sculpted hair, revealing a hollow space
        inside the bust...

    command_2:
      surface: take all from pallas
      interaction_type: action/take
      output:
        peyote button: Removed.
        opium pipe: Removed.
        opium resin: Removed.

Do not classify the whole line as one take command.

Do not attribute the reveal text to the take command if it was caused by the earlier `move hair`.

## Revealed Objects Then Taken Objects

In the multi-command example, the first command reveals objects:

    peyote button
    opium pipe
    opium resin

Then the second command takes them.

Possible extraction:

    action_1:
      command: move hair
      result: reveals_hidden_space
      revealed_objects:
        - peyote button
        - opium pipe
        - opium resin

    action_2:
      command: take all from pallas
      result: success
      inventory_added:
        - peyote button
        - opium pipe
        - opium resin

Keep the reveal and the take as separate events.

## Target Versus Source

In:

    take all from shelves

The target is:

    all

The source is:

    shelves

In:

    take coin from box

The target is:

    coin

The source is:

    box

Do not treat the source as the item being taken.

## Ambient Text Inside Take Output

Take output may include unrelated ambient narration after the action result.

Examples:

    The raven stares down from the stacks.

    There is silence for a moment; then the soft rapping returns.

    The curtains move softly, caressed by the breeze.

    A dull, dark weariness drifts over you.

These lines are game output, not chatter.

However, they should usually be classified separately as ambient event text, not as part of the take result.

Correct split:

    take_result:
      peyote button: Removed.
      opium pipe: Removed.
      opium resin: Removed.

    ambient_events:
      The gentle tapping sounds again.
      A dull, dark weariness drifts over you.

Incorrect extraction:

    opium resin:
      causes dull dark weariness

Only infer causality if other evidence supports it.

## State Guidance

Successful take commands usually change inventory state.

Possible state changes:

    object:
      location_before: room/container/source
      location_after: player_inventory

    player_inventory:
      added:
        - object

Failed take commands do not usually change inventory.

Possible failed state:

    object_or_group:
      take_failed: true
      reason: too_broad_or_not_portable

## Puzzle Guidance

Take interactions may be puzzle-relevant because they show what resources the player can acquire.

Especially important cases:

- objects hidden until revealed
- objects inside containers
- objects needed for later commands
- objects providing light
- books or notes containing clues
- failed take because the object is fixed
- failed take because the player used a broad noun

## Do Not Confuse With

Drop:

    Removes an object from inventory and places it somewhere.

Put:

    Moves an object from inventory into or onto something.

Move:

    Manipulates an object, possibly revealing hidden contents.

Open:

    Opens a container, door, covering, or passage.

Read:

    Reads text from an object.

Examine:

    Describes an object.

Ambient events:

    Raven behavior, tapping, curtains, drafts, and weariness are game output but not part of the take action unless clearly linked.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the player types `take X`, `get X`, `pick up X`, or `take all from Y`, classify the pair as action/take.

Extract the target, source if present, result, and inventory changes.

For multi-command lines, split the commands first and classify each command/output segment separately.