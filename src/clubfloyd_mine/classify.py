"""Pass 5 - Classify Outcomes.

Assigns an OutcomeBucket to each command pair: regex/rule first, then LLM
for uncertain cases, then a human-review queue for low confidence.
See doc/pipeline/05_classify_outcomes.md.
"""
from __future__ import annotations

import argparse


def run(args: argparse.Namespace) -> None:
    raise NotImplementedError(
        "classify is not implemented yet; see doc/pipeline/05_classify_outcomes.md"
    )
