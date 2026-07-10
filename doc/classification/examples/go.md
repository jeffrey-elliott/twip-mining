# Interaction Type: Movement / Room Transition

## Summary

Movement commands attempt to move the player character from one location to another.

These commands are extremely important for room-graph mining because successful movement usually returns the destination room name, room description, visible objects, exits, and sometimes ambient events.

The command may be a full direction word, a direction abbreviation, or a movement phrase.

## Canonical Examples

Input:

    > w

Output:

    Gallery

    The dust of ages -- and of your family for so many generations --
    clings to crooked stone walls, here in this gallery that twists from
    southwest to east as it winds through the tower and ends at a stout
    wooden door. Wider archways open to the north and southeast.

    A portrait of Lenore, radiant on your wedding day, adorns the wall.

    The raven flutters after you, and perches on the portrait.

    >

Input:

    > sw

Output:

    Hallway

    Stone columns, either side of the northwest arch to your study, brace
    the ceiling, whose upper reaches are lost in darkness that your lamp
    cannot pierce. The hallway winds deeper into the tower to the
    northeast; but a faint wisp of draft seeps in from the south.

    The raven flutters after you.

    >

Input:

    > nw

Output:

    Study

    Stone walls, wreathed in shadows and velvet curtains, rise into the
    gloom overhead. The old oak writing desk -- once your father's, now
    your own -- is wedged beneath the window lattice, with a velvet couch
    before it. A low fire smoulders in its ancient hearth. To the
    southeast, a bust of Pallas sits atop an arch with darkness beyond.

    The raven follows you through the archway, and roosts on the bust of
    Pallas.

    >

## Classification

    interaction_type: movement
    command_family: movement
    world_model_relevant: true
    puzzle_relevant: possibly
    state_change_expected: true
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: movement/room-transition

## Basic Direction Commands

Common cardinal directions:

    n
    north
    s
    south
    e
    east
    w
    west

Common diagonal directions:

    ne
    northeast
    nw
    northwest
    se
    southeast
    sw
    southwest

Common vertical directions:

    u
    up
    d
    down

Common relative directions:

    in
    inside
    enter
    out
    outside
    exit
    leave

Some games may also support:

    forward
    f
    back
    backward
    b
    left
    right

These are game-specific and should be classified by response.

## Movement Phrases

Movement can also appear as verb phrases:

    go north
    walk north
    head north
    move north
    travel north
    run north
    go through door
    enter door
    enter archway
    enter hallway
    exit room
    leave room
    climb stairs
    climb up
    climb down
    descend stairs
    ascend stairs

Normalize these to movement when the response indicates location change or attempted location change.

## Direction Normalization

Use this normalization map:

    n: north
    north: north

    s: south
    south: south

    e: east
    east: east

    w: west
    west: west

    ne: northeast
    northeast: northeast

    nw: northwest
    northwest: northwest

    se: southeast
    southeast: southeast

    sw: southwest
    southwest: southwest

    u: up
    up: up

    d: down
    down: down

    in: in
    inside: in
    enter: in

    out: out
    outside: out
    exit: out
    leave: out

## Recognize Successful Movement By

Successful movement often returns:

- a room name as the first line
- a room description
- visible objects or scenery
- visible exits
- NPC or companion movement
- ambient events
- a final prompt

Room name examples:

    Gallery
    Hallway
    Study

A successful movement response may not explicitly say “You go west.” The new room heading is often the main evidence.

## What To Mine

Movement responses are useful for extracting:

- source room
- destination room
- direction used
- room names
- room descriptions
- visible exits
- room-to-room graph edges
- visible scenery
- visible portable objects
- NPC/companion movement
- light/darkness constraints
- blocked exits
- one-way passages
- environmental events

From the examples:

    movement:
      command: w
      normalized_direction: west
      destination_room: Gallery

    room:
      name: Gallery
      exits_or_connections:
        southwest: Hallway or unknown
        east: unknown
        north: unknown
        southeast: unknown
      visible_objects:
        - stout wooden door
        - portrait of Lenore
      ambient_or_npc_event:
        - raven follows and perches on portrait

    movement:
      command: sw
      normalized_direction: southwest
      destination_room: Hallway

    room:
      name: Hallway
      exits_or_connections:
        northwest: Study
        northeast: Gallery or unknown
        south: unknown
      visible_or_implied_features:
        - stone columns
        - northwest arch
        - darkness overhead
        - draft from south
      ambient_or_npc_event:
        - raven follows player

    movement:
      command: nw
      normalized_direction: northwest
      destination_room: Study

    room:
      name: Study
      exits_or_connections:
        southeast: Hallway or unknown
      visible_objects:
        - velvet curtains
        - writing desk
        - window lattice
        - velvet couch
        - hearth
        - bust of Pallas
        - arch
      ambient_or_npc_event:
        - raven follows and roosts on bust of Pallas

## Room Graph Guidance

A movement command creates evidence for a room connection.

Example:

    previous_room: Study
    command: w
    destination_room: Gallery

Possible graph edge:

    Study --west--> Gallery

But be cautious. If the previous room is unknown, do not invent the source room.

If the response says the destination room has a return direction, that may imply a reverse edge.

Example:

    Gallery twists from southwest to east

Possible exits from Gallery:

    southwest
    east

But do not assume exact destination rooms unless proven by movement or explicit text.

## Failed Movement

Movement commands may fail.

Examples of failed movement output:

    You can't go that way.
    You cannot go that way.
    There is no exit in that direction.
    The door is closed.
    The way is blocked.
    You would rather not.
    Darkness bars your way.

Classify these as movement/blocked or movement/failed.

Possible extraction:

    command: north
    result: failed
    state_change: false
    blocked_direction: north
    reason: no exit or blocked path

Failed movement is still useful for map mining because it can rule out or constrain exits.

## Movement Versus Room Description

A room description can occur after:

    look
    l
    movement
    scripted teleport
    waking
    entering a new scene

If the input is a direction or movement phrase and the output begins with a room name, classify it as movement/room-transition.

If the input is `look` or `l`, classify it as room-description/look, not movement.

## Movement Versus Examine

Do not classify a full room description as examine just because it contains object descriptions.

Movement output may include:

    A portrait of Lenore...
    The old oak writing desk...
    A low fire...

These are visible room contents discovered during movement, not direct examine results.

They may create object candidates, but they are not detailed examine descriptions unless the player explicitly examines them.

## Movement Versus Ambient Events

Movement output may include companion or atmosphere text.

Examples:

    The raven flutters after you.

    The raven follows you through the archway, and roosts on the bust of Pallas.

These are game output, not chatter.

They should usually be split from the stable room description as ambient or NPC-following events.

Possible extraction:

    room_description:
      Study room description text

    npc_or_ambient_event:
      raven follows player
      raven roosts on bust of Pallas

## In And Out

`in` and `out` are movement commands when they change location or attempt to.

Examples:

    > in
    > enter
    > enter door
    > go in
    > out
    > exit
    > leave
    > go out

Classify as movement when the response indicates entering, exiting, leaving, or arriving somewhere.

If `enter X` produces a failure such as “You can’t enter that,” classify as movement/failed or action/enter-failed depending on game behavior.

## Up And Down

`up` and `down` are movement directions.

Examples:

    > u
    > up
    > climb up
    > d
    > down
    > descend

Classify as movement when the response indicates vertical travel or attempted vertical travel.

Objects like stairs, ladders, trapdoors, trees, cliffs, and towers often use up/down movement.

## Forward And Back

Some games support relative movement:

    forward
    f
    back
    backward
    b

These are less universal than compass directions.

Classify them as movement only when the response clearly indicates movement or attempted movement.

Do not assume `b` means back in every game. It may be game-specific.

## Sit And Stand

`sit` and `stand` are not direction aliases.

They are posture or body-position commands unless the response changes location.

Examples:

    sit
    sit on couch
    stand
    stand up
    get up

Usually classify these as:

    action/posture

or:

    action/sit
    action/stand

However, some games may use `stand` or `get up` to leave furniture, exit a vehicle, or return from a special location.

If the response changes the room or moves the player, also record movement.

Possible extraction:

    command: stand
    primary_interaction_type: action/posture
    movement_effect: possible
    destination_room: only_if_response_proves_it

## How To Treat It

Movement commands are valid player commands and valid game responses.

Do not classify short commands like `w`, `sw`, `nw`, `u`, `d`, `in`, or `out` as unknown just because they are terse.

Do not require the command to contain the word `go`.

Do not treat the full response as chatter.

Do not merge ambient events into the stable room description.

Do extract the destination room when a room heading appears.

## Do Not Confuse With

Look commands:

    `look` or `l` returns the current room description without necessarily moving.

Examine commands:

    `x desk` describes a specific object.

Inventory:

    `i` lists carried items.

Again:

    `g` repeats the previous command.

Quit:

    `q` may mean quit in gameplay, but inside hint menus it may mean resume.

Posture commands:

    `sit`, `stand`, and `get up` are posture unless they clearly move the player.

Human chatter:

    Transcript-side human comments are not game commands.

## Rule Of Thumb

If the player command is a direction, direction abbreviation, or movement phrase, and the game responds with a new room name or blocked-exit message, classify it as movement.

For successful movement, mine the destination room, room description, visible exits, visible objects, and any ambient/NPC event separately.