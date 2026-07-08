# Mining Club Floyd Transcripts to Better Understand Parser-based Interactive Fiction

## Goal

Build a local, provenance-preserving corpus of ClubFloyd transcripts, then run repeatable passes that extract command/result evidence for parser behavior, world modeling, affordances, failure modes, and successful interaction patterns.

## What is Club Floyd?

Club Floyd is a gaming group that meets online to play text-adventures or parser-based interactive fiction using a chatbot named Floyd and a chat session.

Human participants discuss and comment about behaviors, mostly in the right column of the transcripts.

Floyd receives instructions from human participants and carries them out, as if they were passed directly to the game being played. Interactions with Floyd are shown in the left column of the transcripts.

## Sources

THe main index for Club Floyd is found here:
https://allthingsjacq.com/interactive_fiction.html

Transcripts are of play sessions that may involve more than one game.

The first transcript in the archive is found here:
https://allthingsjacq.com/intfic_clubfloyd_20070901.html

The last transcript in the archive is found here:
https://allthingsjacq.com/intfic_clubfloyd_20250703.html

## Layout

twip-mining/
  README.md
  CLAUDE.md
  pyproject.toml
  src/
    clubfloyd_mine/
      cli.py
      discover.py
      fetch.py
      normalize.py
      segment.py
      extract_pairs.py
      classify.py
      paths.py
      models.py
  tests/
    fixtures/
      sample_transcript.html
      sample_transcript.txt
    test_discover.py
    test_normalize.py
    test_segment.py
    test_extract_pairs.py
  data/
    manifest.jsonl
    raw/
      2007/
        2007-09-09-weishaupt-scholars/
          source.html
          meta.json
    text/
      2007/
        2007-09-09-weishaupt-scholars/
          transcript.txt
    parsed/
      2007/
        2007-09-09-weishaupt-scholars/
          session.json
          command_pairs.jsonl
    records/
      viewing/
      containers/
      opening/
      conversation/
      parser-failures/

