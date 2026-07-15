# Pass 03 - Normalize Data

Convert HTML to plain text while preserving meaningful transcript structure.

Important: preserve these distinctions:

Human discussion:
  Jacqueline says, "..."

Commands to Floyd:
  DavidW says (to Floyd), "look"

Game/bot output:
  Floyd |
  Floyd | You are standing in...

Bot/meta messages:
  Floyd says (to Jacqueline), "Floyd doesn't know that game."

Pagination pauses (MORE-prompt, not real input/output -- see Pass 4):
  DavidW says (to Floyd), "push space"
  DavidW pushes the green 'space' button.

The output should be boring:
- `data/text/2025/2025-01-26-no-more/transcript.txt`
- `data/text/2025/2025-01-26-no-more/transcript.json`

A structured example:

```
{
  "source_id": "2025-01-26-no-more",
  "blocks": [
    {
      "kind": "discussion",
      "speaker": "DavidW",
      "text": "load sleepmask nomore"
    },
    {
      "kind": "game_output",
      "speaker": "CF",
      "text": "\"Stop, please!\" your mother cries..."
    }
  ]
}
```