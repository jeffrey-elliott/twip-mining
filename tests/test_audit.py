from types import SimpleNamespace

from clubfloyd_mine import audit, manifest as manifest_io, paths
from clubfloyd_mine.models import (
    BlockKind,
    CommandPair,
    GameRef,
    ManifestRecord,
    ManifestStatus,
    TranscriptBlock,
)


def _record(source_id, year, status=ManifestStatus.DISCOVERED):
    return ManifestRecord(
        id=source_id,
        source_url=f"https://example.com/{source_id}.html",
        year=year,
        games=[GameRef(title="Some Game")],
        raw_path="unused",
        status=status,
    )


def _write_pairs(record, root, pairs):
    path = paths.command_pairs_path(record.year, record.id, root)
    lines = [p.model_dump_json() for p in pairs]
    paths.ensure_parent(path).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _pair(index, *result_texts, source_id="a"):
    return CommandPair(
        source_id=source_id,
        pair_index=index,
        command_text="look",
        result_blocks=[TranscriptBlock(kind=BlockKind.GAME_OUTPUT, text=t) for t in result_texts],
    )


def test_build_report_counts_disk_state_and_rule_outcomes(tmp_path):
    root = tmp_path / "data"
    record = _record("a", 2007)
    paths.ensure_parent(paths.raw_html_path(record.year, record.id, root)).write_text("x", encoding="utf-8")
    paths.ensure_parent(paths.transcript_json_path(record.year, record.id, root)).write_text(
        "{}", encoding="utf-8"
    )
    _write_pairs(
        record,
        root,
        [
            _pair(0, " Taken."),
            _pair(1, " You can't go that way."),
            _pair(2, " An oil-lamp of copper and glass."),
        ],
    )

    report = audit.build_report([record], root=root, year=2007)

    assert report.discovered == 1
    assert report.fetched == 1
    assert report.normalized == 1
    assert report.extracted_commands == 3
    assert report.obvious_success == 1
    assert report.obvious_failure == 1
    assert report.uncertain == 1


def test_build_report_flags_missing_files_without_relying_on_status(tmp_path):
    root = tmp_path / "data"
    # Status claims FETCHED/NORMALIZED but no files exist on disk -- audit
    # must report actual disk state, not the (possibly stale) status field.
    record = _record("a", 2007, status=ManifestStatus.NORMALIZED)

    report = audit.build_report([record], root=root, year=2007)

    assert report.discovered == 1
    assert report.fetched == 0
    assert report.normalized == 0
    assert report.extracted_commands == 0


def test_run_scopes_to_requested_year(tmp_path, capsys):
    root = tmp_path / "data"
    record_2007 = _record("a", 2007)
    record_2025 = _record("b", 2025)
    paths.ensure_parent(paths.raw_html_path(2007, "a", root)).write_text("x", encoding="utf-8")
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": record_2007, "b": record_2025})

    args = SimpleNamespace(root=root, year=2007)
    audit.run(args)

    out = capsys.readouterr().out
    assert "year 2007" in out
    assert "discovered pages:    1" in out
    assert "fetched pages:       1" in out


def test_run_reports_all_years_when_year_not_given(tmp_path, capsys):
    root = tmp_path / "data"
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": _record("a", 2007), "b": _record("b", 2025)})

    args = SimpleNamespace(root=root, year=None)
    audit.run(args)

    out = capsys.readouterr().out
    assert "all years" in out
    assert "discovered pages:    2" in out


def test_run_handles_empty_manifest(tmp_path, capsys):
    args = SimpleNamespace(root=tmp_path / "data", year=None)
    audit.run(args)
    assert "no records in" in capsys.readouterr().out


def test_run_handles_year_with_no_matching_records(tmp_path, capsys):
    root = tmp_path / "data"
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": _record("a", 2007)})

    args = SimpleNamespace(root=root, year=1999)
    audit.run(args)

    assert "no records found for year 1999" in capsys.readouterr().out
