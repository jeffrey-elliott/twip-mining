# Club Floyd Transcript Classifier Examples

Source page: `intfic_clubfloyd_20070901.html` — first ClubFloyd session, *Nevermore*.

Use this as a practical classification guide for Club Floyd transcript mining.

## Core distinction

A transcript line is **probably game input** when a player explicitly addresses Floyd:

```text
<player> says (to Floyd), "<command>"
<player> says (to floyd), "<command>"
<player> asks (to Floyd), "<command>"
```

The game command is only the quoted text.

A block is **probably game output** when the left prefix is exactly:

```text
Floyd |
```

Consecutive `Floyd |` lines after a player command belong to that command turn until the next non-output transcript event.

Everything else is usually **chatter / session metadata / MUD activity**, even when it contains words that look like parser commands.

## Important startup rule

The opening MUD room description is not the IF game. In this transcript, the page begins with a Toyshop/Floyditorium room description, player arrivals, and setup discussion. Treat that as session setup.

The actual game output begins when Floyd starts printing the game banner and location text:

```text
Floyd | NEVERMORE
Floyd | An Interactive Gothic
Floyd | ...
Floyd | Study (on the velvet couch)
Floyd | ...
Floyd | >
```

## Positive examples: game input

### Simple command to Floyd

```text
maga says (to floyd), "x lamp"
```

Classification:

```yaml
type: game_input
speaker: maga
target_bot: floyd
command: x lamp
```

The following `Floyd |` block is game output for that command:

```text
Floyd | An oil-lamp of copper and glass, warm to the touch and old as time.
Floyd | ...
Floyd | >
```

### Another examine command

```text
inky says (to Floyd), "x desk"
```

Classification:

```yaml
type: game_input
speaker: inky
command: x desk
```

The following `Floyd |` lines are game output until the prompt.

### Inventory shorthand

```text
maga says (to floyd), "i"
```

Classification:

```yaml
type: game_input
speaker: maga
command: i
normalized_possible_intent: inventory
```

### Invalid commands are still input

```text
Bishop says (to floyd), "Snort coke"
```

Classification:

```yaml
type: game_input
speaker: Bishop
command: Snort coke
result_kind: parser_error_or_failed_command
```

Do not discard it just because Floyd reports a parse failure. It is still a player attempt.

### Multiple commands in one player utterance

```text
inky says (to Floyd), "open window. look behind curtains"
```

Classification:

```yaml
type: game_input
speaker: inky
command: open window. look behind curtains
contains_multiple_commands: true
```

For later mining passes, this can either remain one turn or be split into command attempts. The immediate extraction pass should preserve the original text.

## Negative examples: not game input

### General setup chatter

```text
maga asks, "did we decide on Nevermore?"
```

Classification:

```yaml
type: chatter
reason: addressed to the channel, not Floyd
```

### Session coordination

```text
Jacqueline says, "We'll keep the commentary to the channel, and the game play here."
```

Classification:

```yaml
type: chatter
reason: coordination/commentary, not a game command
```

### Player arrival/departure metadata

```text
maga arrives, full of neither funk nor fun.
```

Classification:

```yaml
type: mud_event
reason: player arrival, not game text
```

### Channel events

```text
* maga has added PerrySimm to the channel.
```

Classification:

```yaml
type: channel_event
reason: MUD/channel metadata
```

### Command-looking text that was not sent to Floyd

```text
Rob asks, "inventory?"
```

Classification:

```yaml
type: chatter
looks_like_command: true
reason: not addressed to Floyd
```

### Thought bubble / suggested commands, not submitted commands

```text
Rob . o O ( look behind couch. look under couch. search couch. )
```

Classification:

```yaml
type: chatter_or_suggestion
looks_like_command: true
reason: thought/commentary syntax, not a says-to-Floyd command
```

### Command sent to another bot/person

```text
Rob says (to alex), "touch couch"
```

Classification:

```yaml
type: chatter_or_wrong_target
looks_like_command: true
reason: addressed to alex, not Floyd
```

### Bare command-looking chatter

```text
Rob says, "push button"
```

Classification:

```yaml
type: chatter_or_suggestion
looks_like_command: true
reason: no `(to Floyd)` target
```

If a nearby Floyd response follows another player’s actual `says (to Floyd)` line, attach the output to the actual Floyd-addressed command, not to this bare chatter line.

## Non-game Floyd-adjacent examples

### Whispers are MUD interaction, not IF output

```text
Gunther | You whisper "HELLO!!!" to Floyd.
Gunther | Floyd whispers, "Hi!"
```

Classification:

```yaml
type: mud_whisper
reason: left prefix is Gunther, not Floyd
```

The string `Floyd whispers` is not the same as a `Floyd |` output line.

### Instruction/example line from a player

```text
Jacqueline | ..Floyd x me
```

Classification:

```yaml
type: mud_or_instructional_text
reason: left prefix is Jacqueline, not Floyd; this is demonstrating how to send a command
```

## Practical extraction heuristic

Use this as the first-pass rule:

```text
IF line matches /^(?<speaker>.+?)\s+(says|asks)\s+\(to\s+floyd\),\s+"(?<command>.*)"$/i
THEN classify as game_input

ELSE IF line starts with "Floyd |"
THEN classify as game_output

ELSE classify as non_game_text
```

Then associate output blocks:

```text
When game_input is found:
  collect the following consecutive `Floyd |` lines
  stop when a non-`Floyd |` line appears
  attach collected lines as that input's output
```

## Cautions

1. Do not classify by command-like words alone. `inventory?`, `push button`, `look behind couch`, and `touch couch` can all be chatter when not addressed to Floyd.
2. Case should not matter for `Floyd` / `floyd`.
3. The quoted command may be invalid, mistyped, or rejected by the parser. Still keep it as input.
4. `Floyd | >` is a game prompt and belongs inside the output block.
5. Lines before the first real `Floyd |` game banner/location block are usually MUD/session setup, not the IF game.
