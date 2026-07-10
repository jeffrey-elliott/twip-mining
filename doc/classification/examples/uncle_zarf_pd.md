# Parser Interactive Fiction Command Taxonomy

This document describes common command shapes in parser-based interactive fiction.

Parser IF commands are usually short imperatives typed by the player. They often omit the subject "I" and follow simple patterns:

- VERB
- VERB object
- VERB object PREPOSITION object
- VERB person ABOUT topic
- VERB object TO person
- DIRECTION

Different games support different vocabularies, but these command families are widely recognizable.

---

## 1. Meta / Help Commands

These are not usually actions inside the story world. They ask the game for information.

### ABOUT

Shows information about the game, author, premise, credits, or release.

### INFO

Similar to ABOUT. Often gives game-specific notes, content warnings, or instructions.

### HELP

Asks for general help or hints.

### UNDO

Takes back one move. This is a player-control command, not an in-world action.

Differentiate:

- HELP, ABOUT, and INFO ask the game for information.
- UNDO changes the command history.
- These should not usually be treated as physical actions by the player character.

---

## 2. Looking / Perception Commands

These commands gather information.

### LOOK

Looks around the current location.

Common abbreviation:

- L

Use when the player wants the room/location description again.

### EXAMINE object

Looks at a specific thing in more detail.

Common abbreviation:

- X object

Examples:

- EXAMINE MAILBOX
- X DOOR
- EXAMINE HOUSE

### LOOK UNDER object

Checks beneath an object.

Example:

- LOOK UNDER RUG

### SEARCH object

Looks through or investigates an object more thoroughly than EXAMINE.

Example:

- SEARCH DESK

### SMELL object

Uses smell as the primary sense.

Example:

- SMELL FLOWER

### LISTEN

Listens generally to the current location.

### LISTEN TO object

Listens to a specific object or person.

Example:

- LISTEN TO RADIO

### FEEL object

Touches or physically senses an object.

Example:

- FEEL WALL

Differentiate:

- LOOK is location-level.
- EXAMINE object is object-level.
- SEARCH object implies a more active attempt to find something.
- LOOK UNDER object is spatially specific.
- LISTEN is ambient.
- LISTEN TO object is targeted.
- SMELL object and FEEL object are sensory but not visual.

---

## 3. Movement Commands

These move the player through the world.

### Compass Directions

Short forms:

- N
- S
- E
- W
- NE
- NW
- SE
- SW

Expanded forms:

- GO NORTH
- GO SOUTH
- GO EAST
- GO WEST
- GO NORTHEAST
- GO NORTHWEST
- GO SOUTHEAST
- GO SOUTHWEST

### Vertical / Relative Movement

Commands:

- UP
- DOWN
- IN
- OUT

Common abbreviations:

- U
- D

### ENTER object

Moves into, onto, or through something enterable.

Examples:

- ENTER HOUSE
- ENTER CAR

### CLIMB object

Moves by climbing.

Example:

- CLIMB TREE

Differentiate:

- Compass directions move between mapped locations.
- IN and OUT are relative movement commands.
- ENTER object targets a specific thing.
- CLIMB object implies vertical or physical traversal.
- GO direction and bare direction commands are usually equivalent.

---

## 4. Inventory Commands

These manage what the player carries.

### INVENTORY

Shows what the player is carrying.

Common abbreviation:

- I

### TAKE object

Picks something up.

Example:

- TAKE LAMP

### DROP object

Removes something from inventory and places it in the current location.

Example:

- DROP LAMP

### WEAR object

Puts on wearable clothing or equipment.

Example:

- WEAR HAT

### TAKE object OFF

Removes a worn item.

Example:

- TAKE HAT OFF

Differentiate:

- TAKE object moves an item into inventory.
- DROP object moves an item out of inventory.
- WEAR object changes worn state.
- TAKE object OFF removes worn state but may keep the item in inventory.

---

## 5. Placing / Containment Commands

These move one object relative to another.

### PUT object IN container

Places an object inside another object.

Example:

- PUT COIN IN BOX

### PUT object ON supporter

Places an object on top of another object.

Example:

- PUT BOOK ON TABLE

### FILL object

Fills a container or fillable thing.

Example:

- FILL BOTTLE

Differentiate:

- PUT X IN Y means containment.
- PUT X ON Y means support/surface placement.
- FILL X may require an implied or available substance.
- Some games may support FILL X WITH Y, but the basic card form is FILL X.

---

## 6. Opening / Locking Commands

These change access state.

### OPEN object

Opens something openable.

Examples:

- OPEN DOOR
- OPEN MAILBOX

### UNLOCK object WITH object

Unlocks something using a key or tool.

Example:

- UNLOCK DOOR WITH KEY

Differentiate:

- OPEN object changes open/closed state.
- UNLOCK object WITH tool changes locked/unlocked state.
- A thing may need to be unlocked before it can be opened.
- OPEN does not necessarily imply possession of a key or tool.

---

## 7. Physical Manipulation Commands

These physically interact with objects.

### PUSH object

Applies force away from the player or activates pushable things.

Example:

- PUSH BUTTON

### PULL object

Applies force toward the player.

Example:

- PULL LEVER

### TURN object

Rotates or adjusts something.

Example:

- TURN KNOB

### TURN object ON

Activates a device.

Example:

- TURN LAMP ON

### WAVE object

Moves an object around, often in the air.

Example:

- WAVE WAND

### BREAK object

Attempts to damage or destroy something.

Example:

- BREAK WINDOW

### BURN object

Attempts to set something on fire or apply fire to it.

Example:

- BURN PAPER

### DIG IN object

Attempts to dig in a target material or location.

Example:

- DIG IN DIRT

Differentiate:

- PUSH, PULL, and TURN are mechanical manipulation commands.
- TURN object means rotate or adjust.
- TURN object ON means activate.
- BREAK is destructive force.
- BURN is destructive fire.
- DIG IN object is excavation or disturbance of material.

---

## 8. Eating / Drinking Commands

These consume objects.

### EAT object

Consumes edible food.

Example:

- EAT PIE

### DRINK object

Consumes drinkable liquid.

Example:

- DRINK WATER

Differentiate:

- EAT is for solid or food-like things.
- DRINK is for liquids.
- These are usually irreversible or state-changing.

---

## 9. Waiting / Repeating Commands

These affect turn flow.

### WAIT

Passes one turn without doing anything.

Common abbreviation:

- Z

### AGAIN

Repeats the previous command.

Common abbreviation:

- G

Differentiate:

- WAIT spends a turn intentionally.
- AGAIN repeats the last command.
- UNDO reverses a previous turn; it is not the opposite of WAIT.

---

## 10. Miscellaneous In-World Commands

These are common but less structurally central.

### JUMP

Performs a jump.

### SLEEP

Attempts to sleep.

### WAKE UP

Attempts to wake, or stop sleeping.

### PRAY

Performs prayer.

### CURSE

Curses or swears.

### SING

Sings.

Differentiate:

- These are usually single-verb commands.
- They may be mostly flavor unless a specific game implements them.
- They are still recognizable parser IF commands.

---

## 11. General Recognition Rules

A phrase is likely a parser IF command if it resembles one of these patterns:

- VERB
- VERB object
- VERB object PREPOSITION object
- VERB person ABOUT topic
- VERB object TO person
- DIRECTION

Important prepositions:

- IN
- ON
- UNDER
- WITH
- TO
- ABOUT
- OFF

Important abbreviations:

- L = LOOK
- X = EXAMINE
- I = INVENTORY
- Z = WAIT
- G = AGAIN
- N/S/E/W/NE/NW/SE/SW = movement
- U = UP
- D = DOWN

Core principle:

Visible nouns invite plausible verbs. If the room description mentions a door, mailbox, button, pie, person, key, table, or container, the player can try commands that sensibly apply to that noun.

Examples:

- OPEN DOOR
- OPEN MAILBOX
- PUSH BUTTON
- EAT PIE
- TAKE KEY
- PUT KEY IN BOX
- ASK GUARD ABOUT HOUSE
- SHOW BADGE TO GUARD