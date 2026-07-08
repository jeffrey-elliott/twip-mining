"""Pass 6 - Generate candidate cases.

Renders classified pairs into data/records/<category>/*.md files with
YAML front matter, for human review during Twip design.
See doc/pipeline/06_generate_candidate_cases.md.
"""
from __future__ import annotations

import argparse


def run(args: argparse.Namespace) -> None:
    raise NotImplementedError(
        "make-records is not implemented yet; see doc/pipeline/06_generate_candidate_cases.md"
    )
