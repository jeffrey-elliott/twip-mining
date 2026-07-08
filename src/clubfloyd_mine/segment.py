"""Segment a normalized transcript into per-game sessions.

A single ClubFloyd transcript can cover more than one game; this splits
the block list from transcript.json into per-game segments.
"""
from __future__ import annotations

import argparse


def run(args: argparse.Namespace) -> None:
    raise NotImplementedError("segment is not implemented yet")
