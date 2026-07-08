import pytest
from pydantic import ValidationError

from clubfloyd_mine.models import (
    BlockKind,
    ClassificationSource,
    ClassifiedPair,
    CommandPair,
    FetchMeta,
    GameRef,
    ManifestRecord,
    ManifestStatus,
    OutcomeBucket,
    RecordFrontMatter,
    Transcript,
    TranscriptBlock,
)


def test_manifest_record_matches_doc_example():
    record = ManifestRecord.model_validate(
        {
            "id": "2025-01-26-no-more",
            "source_url": "https://allthingsjacq.com/intfic_clubfloyd_20250105.html",
            "year": 2025,
            "played_date": "2025-01-26",
            "page_title": "ClubFloyd - January 26, 2025 - No More by Tabitha",
            "games": [{"title": "No More", "author": "Tabitha"}],
            "raw_path": "data/raw/2025/2025-01-26-no-more/source.html",
            "status": "discovered",
        }
    )
    assert record.status is ManifestStatus.DISCOVERED
    assert record.games == [GameRef(title="No More", author="Tabitha")]
    assert record.model_dump()["id"] == "2025-01-26-no-more"


def test_manifest_record_defaults_status_to_discovered():
    record = ManifestRecord(
        id="x",
        source_url="https://example.com",
        year=2025,
        raw_path="data/raw/2025/x/source.html",
    )
    assert record.status is ManifestStatus.DISCOVERED
    assert record.games == []


def test_manifest_record_rejects_unknown_status():
    with pytest.raises(ValidationError):
        ManifestRecord(
            id="x",
            source_url="https://example.com",
            year=2025,
            raw_path="p",
            status="not-a-real-status",
        )


def test_fetch_meta_round_trip():
    meta = FetchMeta.model_validate(
        {
            "source_url": "https://example.com",
            "fetched_at": "2025-01-26T12:00:00Z",
            "sha256": "a" * 64,
            "http_status": 200,
            "content_length": 12345,
            "user_agent": "clubfloyd-mine/0.1",
        }
    )
    assert meta.previous_sha256 is None
    assert meta.http_status == 200


def test_transcript_blocks_preserve_kind_distinctions():
    transcript = Transcript(
        source_id="2025-01-26-no-more",
        blocks=[
            TranscriptBlock(kind=BlockKind.DISCUSSION, speaker="Jacqueline", text="..."),
            TranscriptBlock(
                kind=BlockKind.COMMAND,
                speaker="DavidW",
                addressee="Floyd",
                text="load sleepmask nomore",
            ),
            TranscriptBlock(
                kind=BlockKind.GAME_OUTPUT,
                speaker="CF",
                text='"Stop, please!" your mother cries...',
            ),
            TranscriptBlock(
                kind=BlockKind.BOT_META,
                speaker="Floyd",
                addressee="Jacqueline",
                text="Floyd doesn't know that game.",
            ),
        ],
    )
    assert [b.kind for b in transcript.blocks] == [
        BlockKind.DISCUSSION,
        BlockKind.COMMAND,
        BlockKind.GAME_OUTPUT,
        BlockKind.BOT_META,
    ]


def test_command_pair_and_classified_pair():
    pair = CommandPair(
        source_id="2009-01-25-earth-and-sky",
        pair_index=0,
        speaker="DavidW",
        addressee="Floyd",
        command_text="look through window",
        result_blocks=[
            TranscriptBlock(kind=BlockKind.GAME_OUTPUT, text="You see a garden.")
        ],
    )
    classified = ClassifiedPair(
        source_id=pair.source_id,
        pair_index=pair.pair_index,
        outcome=OutcomeBucket.SUCCESS,
        confidence=0.77,
        classifier=ClassificationSource.RULE,
    )
    assert classified.outcome is OutcomeBucket.SUCCESS
    assert classified.classifier is ClassificationSource.RULE


def test_record_front_matter_success_example():
    front_matter = RecordFrontMatter(
        record_type="interaction_pattern",
        category="viewing",
        behavior_candidate="LookThroughable",
        outcome="success",
        source_id="2009-01-25-earth-and-sky",
        game="Earth and Sky",
        played_date="2009-01-25",
        command="look through window",
        normalized_verb="look",
        normalized_preposition="through",
        source_url="https://allthingsjacq.com/intfic_clubfloyd_20090125.html",
        confidence=0.77,
    )
    assert front_matter.category == "viewing"


def test_record_front_matter_failure_example():
    front_matter = RecordFrontMatter(
        record_type="failure_pattern",
        category="parser_failure",
        source_id="2015-01-04-you-were-here",
        command="x obelisk",
        failure_kind="unknown_abbreviation_or_target",
        confidence=0.64,
    )
    assert front_matter.failure_kind == "unknown_abbreviation_or_target"
