# Pass 05 - Classify Outcomes

Don’t overdo this at first. Start with coarse buckets:

```
success
parser_failure
world_failure
disambiguation
clarification
inventory_change
location_change
score_or_end_state
meta_or_floyd_control
unknown
```

Example questions the classifier can answer:

1. Did the game understand the verb?
2. Did the game understand the noun?
3. Was the action impossible because of world state?
4. Did output reveal a new object?
5. Did the player retry with a synonym?
6. Did the game give a custom failure message?
7. Did a command become useful only after another state change?

The solution here is a hybrid:
1. Regex/rule classifier for obvious cases.
2. LLM classifier for uncertain cases.
3. Human-review queue for low confidence.
