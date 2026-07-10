# Interaction Type: Search / Careful Inspection For Hidden Content

## Summary

The `search` command asks the game to inspect something carefully, usually looking for hidden, concealed, non-obvious, or additional information.

It may overlap with `look` or `examine`, but it often implies a more active and thorough investigation.

Common command shape:

    search TARGET

This interaction is world-model relevant and often puzzle-relevant, even when nothing is found.

## Canonical Example

Input:

    > search ring

Output:

    You find nothing of interest.

    >

## Classification

    interaction_type: search_action
    command_family: search
    world_model_relevant: true
    puzzle_relevant: possibly
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: action/search

## Common Input Forms

Commands in this family include:

    search ring
    search desk
    search room
    search shelves
    search corpse
    search pockets
    search under bed
    look under bed
    look behind painting
    examine closely
    inspect carefully

Some games treat `search X` as equivalent to `examine X`.

Other games reserve `search` for finding hidden things.

Classify based on response.

## Recognize This Type By

The player command usually begins with:

    search

The response may indicate:

- something hidden was found
- nothing was found
- the target was searched but empty
- the target cannot be searched
- the player needs to be more specific
- the player discovers a concealed object, passage, clue, switch, writing, or compartment

Common responses:

    You find nothing of interest.
    You find nothing unusual.
    There is nothing hidden there.
    You discover a small key.
    Searching more carefully, you find...
    Hidden behind it is...
    You uncover...

## What To Mine

Search responses are useful for extracting:

- searchable objects
- hidden objects
- failed hidden-object searches
- concealment relationships
- puzzle clues
- object affordances
- possible secret compartments
- evidence that a target has no hidden content
- evidence that a target was worth trying to search

From this example:

    command:
      verb: search
      target: ring

    ring:
      searchable: true
      search_result: nothing_found
      hidden_content_found: false
      state_change: false

## Nothing Found Is Still Useful

A response like:

    You find nothing of interest.

is not chatter and not an unknown-command result.

It means the command was understood, the target was recognized, and the search completed without discovering anything.

Possible extraction:

    result: success_no_discovery
    recognized_command: true
    recognized_target: true
    discovered_objects: none

Do not discard this pair.

## Search Versus Examine

`examine` usually asks:

    What does this thing look like?

`search` usually asks:

    Is anything hidden, concealed, or discoverable here?

Example distinction:

    > x ring

might describe the ring's appearance.

    > search ring

might check whether the ring contains an inscription, compartment, hidden mark, or clue.

If `search X` returns ordinary descriptive prose, it may overlap with examine.

If `search X` returns discovery or “nothing found,” classify it as search.

## Search May Reveal Hidden Objects

A successful search may produce a state change.

Example pattern:

    > search desk

    You find a small brass key taped underneath the drawer.

Possible extraction:

    command: search desk
    result: hidden_object_found
    state_change: true
    revealed_objects:
      - small brass key
    concealment:
      small brass key:
        hidden_in_or_under: desk

## Search May Be A Failed Puzzle Attempt

A no-discovery result can still be puzzle-relevant.

Example:

    > search ring

    You find nothing of interest.

Possible interpretation:

    search was valid
    ring did not reveal hidden content here
    ring may still matter for another action
    no state change occurred

Do not infer that the ring is useless globally.

Only infer that this search did not reveal anything.

## State Guidance

Search may or may not change state.

No discovery:

    state_change: false
    hidden_content_found: false

Discovery:

    state_change: true
    hidden_content_found: true
    revealed_objects: list discovered objects

Do not mark inventory changes unless the output says the discovered object was taken, removed, or added to inventory.

Finding an object is not always the same as taking it.

## Do Not Confuse With

Examine:

    Gives descriptive detail about a specific object.

Look:

    Describes the current room or visible surroundings.

Take:

    Moves an object into inventory.

Open:

    Opens a container, door, covering, or passage.

Move:

    Manipulates an object and may reveal something.

Read:

    Reads written text from an object.

Unknown command:

    Parser does not understand the verb.

Human chatter:

    Transcript-side player comments are not game output.

## Rule Of Thumb

If the player types `search X`, classify the pair as action/search.

If the output says nothing was found, keep the pair and record a successful search with no discovery.

If the output reveals hidden content, record the discovered object or clue separately from any later action that takes or uses it.