# Interaction Type: Read / Readable Text

## Summary

The `read` command asks the game to read text from an in-world readable object.

Readable targets may include books, papers, notes, labels, inscriptions, signs, journals, letters, plaques, scrolls, or other textual scenery.

This is world-model relevant and often puzzle-relevant.

`read` is different from `examine`: examine usually describes the physical object; read usually returns the object's written content.

## Canonical Examples

Input:

    > read pharmacopia

Output:

    You hunt feverishly through the pages of Adams' Pharmacopia, and
    discover:

    "The leaves of the hasheesh or hemp, when dried and smoked, may produce
    a sensation of relaxation and general suggestibility. In combination
    with certain rhythmical musical ceremonies such as the drumming rituals
    of Africa or the dances of Jamaica, these leaves have been long
    associated with the sprit world."

    The raven watches you silently from the bust of Pallas.

    An icy gust from the window sends the curtains reeling.

    >

Input:

    > read pharmacopia

Output:

    You hunt feverishly through the pages of Adams' Pharmacopia, and
    discover:

    "Peyote, a cactus found on the American continent, when dried in
    "button" form has remarkable properties of provoking visionary states
    of mind and has been used extensively by native shamans in magical
    rituals, where it is said to provide great wisdom and insight. It does
    not induce sleep, however, which makes its use all the more
    controversial."

    The raven caws. "Nevermore!"

    >

## Classification

    interaction_type: read_text
    command_family: read
    world_model_relevant: true
    puzzle_relevant: usually
    state_change_expected: sometimes
    state_observation_expected: true
    transcript_noise: false
    keep_as_command_pair: true
    short_label: read/text

## Common Input Forms

Commands in this family include:

    read book
    read note
    read paper
    read sign
    read inscription
    read pharmacopia
    read Concerning Immortality
    read label
    read plaque
    read writing

## Recognize This Type By

The player command starts with `read`, followed by a readable target.

The response often includes:

- quoted text
- book excerpts
- inscriptions
- signs or labels
- discovered written information
- lore
- puzzle clues
- instructions
- warnings
- repeated or paged reading behavior

Common phrases:

    You read...
    Written on it is...
    The sign says...
    The book says...
    You hunt through the pages...
    You discover:
    It reads:

## What To Mine

Useful for extracting:

- readable objects
- book titles
- written content
- lore
- puzzle clues
- instructions
- recipes or rituals
- topic lists
- repeated-read sequences
- knowledge gated behind reading
- whether a target is readable

From these examples:

    readable_object:
      name: Adams' Pharmacopia
      object_type: book
      readable: true

    discovered_topics:
      - hasheesh or hemp
      - peyote
      - coca
      - opium

    possible_puzzle_relevance:
      - substances may have different effects
      - some substances may affect sleep, visions, stamina, or suggestibility
      - repeated reading reveals multiple entries

## Read Versus Examine

Do not collapse `read` and `examine`.

Example difference:

    > x book

Usually describes the book as an object.

    > read book

Usually returns text from inside the book.

If `x book` returns readable text, classify it as examine with readable-content overlap.

If `read book` returns physical description only, classify it as read attempted against a readable target, but note that the result was descriptive rather than textual.

## Repeated Read Behavior

Some readable objects return different content on repeated reads.

In this example, repeated reads of Adams' Pharmacopia reveal different drug entries.

Possible extraction:

    object: Adams' Pharmacopia
    read_behavior: repeated_reads_reveal_multiple_entries
    entries_seen:
      - hemp / hasheesh
      - peyote
      - coca
      - opium

Do not assume the first read exhausts the object.

## State Guidance

A read command may or may not change state.

Usually it reveals information.

But repeated-read systems may advance an internal reading cursor, choose another entry, or reveal new content.

Possible extraction:

    command: read pharmacopia
    result: readable_text_returned
    state_change:
      reading_cursor_or_topic_may_advance: true
    world_state_change: false

Use caution: the changing output may be random, sequential, or context-dependent.

## Ambient Text Inside Read Output

Read output may include unrelated or semi-related ambient narration after the readable text.

Examples:

    The raven watches you silently from the bust of Pallas.

    An icy gust from the window sends the curtains reeling.

    The raven caws. "Nevermore!"

These lines are game output, not chatter.

However, they should usually be classified separately as ambient event text, not as part of the written text being read.

## How To Treat It

This is a valid player command and valid game response.

Do not classify it as chatter.

Do not treat quoted book text as player speech.

Do not treat ambient narration after the excerpt as part of the book's written contents.

Do separate:

    Readable text:
      "Peyote, a cactus found on the American continent..."

    Ambient event:
      The raven caws. "Nevermore!"

## Do Not Confuse With

Examine responses:

    These describe an object, although they may sometimes reveal readable text.

Room descriptions:

    These describe the current location.

Inventory listings:

    These list carried or worn objects.

Meta commands:

    These describe the game, help system, author, version, or hints.

Human chatter:

    These are transcript-side comments from players, not game output.

## Rule Of Thumb

If the player types `read X` and the game returns written content from an in-world object, classify it as read/text.

If repeated reads produce different excerpts, keep each pair and mark the readable object as having repeated-read behavior.