from clubfloyd_mine import manifest as manifest_io
from clubfloyd_mine.models import GameRef, ManifestRecord, ManifestStatus


def _record(source_id="20250101-no-more", status=ManifestStatus.DISCOVERED):
    return ManifestRecord(
        id=source_id,
        source_url=f"https://example.com/{source_id}.html",
        year=2025,
        games=[GameRef(title="No More", author="Tabitha")],
        raw_path=f"data/raw/2025/{source_id}/source.html",
        status=status,
    )


def test_load_manifest_missing_file_returns_empty(tmp_path):
    assert manifest_io.load_manifest(tmp_path / "manifest.jsonl") == {}


def test_write_then_load_round_trips(tmp_path):
    manifest_file = tmp_path / "manifest.jsonl"
    original = {"a": _record("a"), "b": _record("b")}

    manifest_io.write_manifest(manifest_file, original)
    loaded = manifest_io.load_manifest(manifest_file)

    assert loaded == original


def test_write_manifest_orders_by_year_then_id(tmp_path):
    manifest_file = tmp_path / "manifest.jsonl"
    records = {
        "b": _record("b").model_copy(update={"year": 2007}),
        "a": _record("a").model_copy(update={"year": 2025}),
    }

    manifest_io.write_manifest(manifest_file, records)

    ids_in_file_order = [
        ManifestRecord.model_validate_json(line).id
        for line in manifest_file.read_text(encoding="utf-8").splitlines()
    ]
    assert ids_in_file_order == ["b", "a"]  # 2007 before 2025


def test_advance_status_moves_forward():
    record = _record(status=ManifestStatus.DISCOVERED)
    advanced = manifest_io.advance_status(record, ManifestStatus.FETCHED)
    assert advanced.status is ManifestStatus.FETCHED


def test_advance_status_does_not_regress():
    record = _record(status=ManifestStatus.CLASSIFIED)
    unchanged = manifest_io.advance_status(record, ManifestStatus.FETCHED)
    assert unchanged.status is ManifestStatus.CLASSIFIED


def test_advance_status_overrides_error():
    record = _record(status=ManifestStatus.ERROR)
    advanced = manifest_io.advance_status(record, ManifestStatus.FETCHED)
    assert advanced.status is ManifestStatus.FETCHED
