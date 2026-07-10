"""Pydantic data models shared across pipeline passes.

Field shapes follow the examples in doc/pipeline/*.md. Keep these models
additive (new optional fields) rather than renaming/removing, since JSONL
files already written by earlier passes must stay loadable.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ManifestStatus(str, Enum):
    DISCOVERED = "discovered"
    FETCHED = "fetched"
    NORMALIZED = "normalized"
    PARSED = "parsed"
    CLASSIFIED = "classified"
    ERROR = "error"


class GameRef(BaseModel):
    title: str
    author: Optional[str] = None


class ManifestRecord(BaseModel):
    """One row of data/manifest.jsonl (Pass 1 output)."""

    id: str
    source_url: str
    year: int
    # Stored as a string, not datetime.date: some source pages only give a
    # partial or ambiguous date, and we must not silently coerce/drop those.
    played_date: Optional[str] = None
    page_title: Optional[str] = None
    games: list[GameRef] = Field(default_factory=list)
    raw_path: str
    status: ManifestStatus = ManifestStatus.DISCOVERED


class FetchMeta(BaseModel):
    """data/raw/<year>/<id>/meta.json (Pass 2 output)."""

    source_url: str
    fetched_at: datetime
    sha256: str
    http_status: int
    content_length: int
    user_agent: str
    previous_sha256: Optional[str] = None


class BlockKind(str, Enum):
    DISCUSSION = "discussion"
    COMMAND = "command"
    GAME_OUTPUT = "game_output"
    BOT_META = "bot_meta"


class TranscriptBlock(BaseModel):
    """One entry in transcript.json's "blocks" list (Pass 3 output)."""

    kind: BlockKind
    speaker: Optional[str] = None
    # e.g. "Floyd" for a command block ("DavidW says (to Floyd), ...")
    addressee: Optional[str] = None
    text: str


class Transcript(BaseModel):
    """data/text/<year>/<id>/transcript.json (Pass 3 output)."""

    source_id: str
    blocks: list[TranscriptBlock] = Field(default_factory=list)


class CommandPair(BaseModel):
    """One entry in data/parsed/<year>/<id>/command_pairs.jsonl (Pass 4 output)."""

    source_id: str
    pair_index: int
    speaker: Optional[str] = None
    addressee: Optional[str] = None
    command_text: str
    result_blocks: list[TranscriptBlock] = Field(default_factory=list)
    # True only for the synthetic leading pair extract_pairs.extract_pairs
    # emits when a transcript's first GAME_OUTPUT run has no preceding
    # COMMAND (a game auto-booting before any command was logged, e.g. a
    # pre-loaded single-game session -- see
    # doc/annotated_screenshots/preamble.png). command_text is "" and
    # speaker/addressee are None in that case; every other pair leaves this
    # at its default.
    is_leading_output: bool = False


class GameSegment(BaseModel):
    """One entry in data/parsed/<year>/<id>/session.json's "segments" list
    (segment pass output). Stores block-index ranges into the same
    transcript.json rather than duplicating block content."""

    segment_index: int
    start_block_index: int  # inclusive, into transcript.blocks
    end_block_index: int  # exclusive
    # The "load X" command text that started this segment, or None for the
    # implicit first segment when a game was already loaded before the
    # transcript log started (no "load" anywhere in the transcript).
    start_command: Optional[str] = None


class SessionSegments(BaseModel):
    """data/parsed/<year>/<id>/session.json (segment pass output)."""

    source_id: str
    segments: list[GameSegment] = Field(default_factory=list)


class OutcomeBucket(str, Enum):
    SUCCESS = "success"
    PARSER_FAILURE = "parser_failure"
    WORLD_FAILURE = "world_failure"
    DISAMBIGUATION = "disambiguation"
    CLARIFICATION = "clarification"
    INVENTORY_CHANGE = "inventory_change"
    LOCATION_CHANGE = "location_change"
    SCORE_OR_END_STATE = "score_or_end_state"
    META_OR_FLOYD_CONTROL = "meta_or_floyd_control"
    UNKNOWN = "unknown"


class ClassificationSource(str, Enum):
    RULE = "rule"
    LLM = "llm"
    HUMAN = "human"


class ClassifiedPair(BaseModel):
    """Pass 5 output: a CommandPair with an assigned outcome bucket."""

    source_id: str
    pair_index: int
    outcome: OutcomeBucket
    confidence: float
    classifier: ClassificationSource
    # Verbatim quotes from the pair's own result_blocks text that justify
    # `outcome`. Required (and verified against the source pair) for
    # classifier=LLM; always empty for classifier=RULE, whose justification
    # is the matched rule itself. See classify.classify_pair_llm.
    evidence: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class RecordFrontMatter(BaseModel):
    """YAML front matter for a data/records/<category>/*.md file (Pass 6 output).

    Success and failure records share this shape but populate different
    optional fields (see doc/pipeline/06_generate_candidate_cases.md).
    """

    record_type: str
    category: str
    source_id: str
    confidence: float
    game: Optional[str] = None
    played_date: Optional[str] = None
    source_url: Optional[str] = None
    command: Optional[str] = None
    normalized_verb: Optional[str] = None
    normalized_preposition: Optional[str] = None
    behavior_candidate: Optional[str] = None
    outcome: Optional[str] = None
    failure_kind: Optional[str] = None
