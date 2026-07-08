"""Pass 4 - Pair Commands to Results.

Reads normalized transcript blocks and writes
data/parsed/<year>/<id>/command_pairs.jsonl.
See doc/pipeline/04_pair_commands_to_results.md.
"""
from __future__ import annotations

import argparse


def run(args: argparse.Namespace) -> None:
    raise NotImplementedError(
        "extract-pairs is not implemented yet; see doc/pipeline/04_pair_commands_to_results.md"
    )
