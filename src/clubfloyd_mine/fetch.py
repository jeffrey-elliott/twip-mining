"""Pass 2 - Fetch Local.

Politely fetches each manifest URL to data/raw/<year>/<id>/source.html + meta.json.
See doc/pipeline/02_fetch_local.md.
"""
from __future__ import annotations

import argparse


def run(args: argparse.Namespace) -> None:
    raise NotImplementedError(
        "fetch is not implemented yet; see doc/pipeline/02_fetch_local.md"
    )
