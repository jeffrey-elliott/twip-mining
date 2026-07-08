"""Cross-check the manifest against data/raw, data/text, data/parsed, and
data/records, reporting missing, stale, or orphaned files.
"""
from __future__ import annotations

import argparse


def run(args: argparse.Namespace) -> None:
    raise NotImplementedError("audit is not implemented yet")
