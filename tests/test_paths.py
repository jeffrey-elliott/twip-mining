import os
from pathlib import Path

from clubfloyd_mine import paths


def test_default_data_root_is_data():
    assert paths.data_root() == Path("data")


def test_explicit_root_overrides_default():
    assert paths.data_root("/tmp/somewhere") == Path("/tmp/somewhere")


def test_env_var_overrides_default(monkeypatch):
    monkeypatch.setenv("CLUBFLOYD_DATA_ROOT", "/tmp/env-root")
    assert paths.data_root() == Path("/tmp/env-root")


def test_explicit_root_overrides_env_var(monkeypatch):
    monkeypatch.setenv("CLUBFLOYD_DATA_ROOT", "/tmp/env-root")
    assert paths.data_root("/tmp/explicit") == Path("/tmp/explicit")


def test_manifest_path():
    assert paths.manifest_path("data") == Path("data/manifest.jsonl")


def test_raw_paths():
    root = "data"
    year, source_id = 2025, "2025-01-26-no-more"
    assert paths.raw_dir(year, source_id, root) == Path(
        "data/raw/2025/2025-01-26-no-more"
    )
    assert paths.raw_html_path(year, source_id, root) == Path(
        "data/raw/2025/2025-01-26-no-more/source.html"
    )
    assert paths.raw_meta_path(year, source_id, root) == Path(
        "data/raw/2025/2025-01-26-no-more/meta.json"
    )


def test_text_paths():
    root = "data"
    year, source_id = 2007, "2007-09-09-weishaupt-scholars"
    assert paths.text_dir(year, source_id, root) == Path(
        "data/text/2007/2007-09-09-weishaupt-scholars"
    )
    assert paths.transcript_txt_path(year, source_id, root) == Path(
        "data/text/2007/2007-09-09-weishaupt-scholars/transcript.txt"
    )
    assert paths.transcript_json_path(year, source_id, root) == Path(
        "data/text/2007/2007-09-09-weishaupt-scholars/transcript.json"
    )


def test_parsed_paths():
    root = "data"
    year, source_id = 2009, "2009-01-25-earth-and-sky"
    assert paths.parsed_dir(year, source_id, root) == Path(
        "data/parsed/2009/2009-01-25-earth-and-sky"
    )
    assert paths.session_json_path(year, source_id, root) == Path(
        "data/parsed/2009/2009-01-25-earth-and-sky/session.json"
    )
    assert paths.command_pairs_path(year, source_id, root) == Path(
        "data/parsed/2009/2009-01-25-earth-and-sky/command_pairs.jsonl"
    )


def test_records_dir():
    assert paths.records_dir("viewing", "data") == Path("data/records/viewing")


def test_ensure_parent_creates_directory(tmp_path):
    target = tmp_path / "nested" / "dir" / "file.txt"
    result = paths.ensure_parent(target)
    assert result == target
    assert target.parent.is_dir()
    assert not target.exists()
