"""Shared read/write helpers for data/manifest.jsonl, used by every pass."""
from __future__ import annotations

from pathlib import Path

from clubfloyd_mine import paths
from clubfloyd_mine.models import ManifestRecord, ManifestStatus

# Order a record is expected to move through. ERROR ranks below DISCOVERED
# so a later successful pass always overrides a prior failure.
_STATUS_RANK = {
    ManifestStatus.ERROR: -1,
    ManifestStatus.DISCOVERED: 0,
    ManifestStatus.FETCHED: 1,
    ManifestStatus.NORMALIZED: 2,
    ManifestStatus.PARSED: 3,
    ManifestStatus.CLASSIFIED: 4,
}


def load_manifest(manifest_file: Path) -> dict[str, ManifestRecord]:
    records: dict[str, ManifestRecord] = {}
    if not manifest_file.exists():
        return records
    for line in manifest_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            record = ManifestRecord.model_validate_json(line)
            records[record.id] = record
    return records


def write_manifest(manifest_file: Path, records: dict[str, ManifestRecord]) -> None:
    paths.ensure_parent(manifest_file)
    ordered = sorted(records.values(), key=lambda r: (r.year, r.id))
    lines = [record.model_dump_json() for record in ordered]
    manifest_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def advance_status(record: ManifestRecord, target: ManifestStatus) -> ManifestRecord:
    """Move `record` to `target` only if that's forward progress.

    A pass that reruns over an already-advanced record (e.g. fetch running
    again after normalize has already run) must not regress its status.
    """
    if _STATUS_RANK[target] > _STATUS_RANK[record.status]:
        return record.model_copy(update={"status": target})
    return record
