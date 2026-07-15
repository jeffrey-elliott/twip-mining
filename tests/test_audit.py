from types import SimpleNamespace

import pytest

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
    assert report.parsed == 1
    assert report.extracted_commands == 3
    assert report.rule_outcome_counts == {
        "inventory_change": 1,  # "Taken."
        "parser_failure": 1,  # "You can't go that way."
        "success": 1,  # rich descriptive oil-lamp text following "look" -- a successful look
    }
    assert report.complete is True


def test_build_report_flags_missing_files_without_relying_on_status(tmp_path):
    root = tmp_path / "data"
    # Status claims FETCHED/NORMALIZED but no files exist on disk -- audit
    # must report actual disk state, not the (possibly stale) status field.
    record = _record("a", 2007, status=ManifestStatus.NORMALIZED)

    report = audit.build_report([record], root=root, year=2007)

    assert report.discovered == 1
    assert report.fetched == 0
    assert report.normalized == 0
    assert report.parsed == 0
    assert report.extracted_commands == 0
    assert report.complete is False


def test_build_report_excludes_errored_record_from_completeness():
    # A record the manifest marks ERROR (a confirmed-gone source page, e.g.
    # a real 404) is never going to fetch -- it must not make the whole
    # corpus report FAIL forever alongside records that are genuinely
    # complete. See 20230603-i-am-prey.
    errored = _record("gone-404", 2023, status=ManifestStatus.ERROR)
    report = audit.build_report([errored], root="unused", year=2023)

    assert report.discovered == 1
    assert report.errored == 1
    assert report.fetched == 0
    assert report.complete is True


def test_build_report_still_fails_when_a_non_errored_record_is_incomplete(tmp_path):
    root = tmp_path / "data"
    complete = _complete_record("a", 2007, root)
    errored = _record("gone-404", 2007, status=ManifestStatus.ERROR)
    incomplete = _record("b", 2007, status=ManifestStatus.DISCOVERED)

    report = audit.build_report([complete, errored, incomplete], root=root, year=2007)

    assert report.discovered == 3
    assert report.errored == 1
    assert report.fetched == 1
    assert report.complete is False


def _complete_record(source_id, year, root):
    record = _record(source_id, year)
    paths.ensure_parent(paths.raw_html_path(year, source_id, root)).write_text("x", encoding="utf-8")
    paths.ensure_parent(paths.transcript_json_path(year, source_id, root)).write_text("{}", encoding="utf-8")
    _write_pairs(record, root, [_pair(0, " Taken.", source_id=source_id)])
    return record


def test_run_scopes_to_requested_year(tmp_path, capsys):
    root = tmp_path / "data"
    record_2007 = _complete_record("a", 2007, root)
    record_2025 = _record("b", 2025)  # not fetched -- must not affect the 2007-scoped report
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": record_2007, "b": record_2025})

    args = SimpleNamespace(root=root, year=2007)
    audit.run(args)  # 2007 is complete -- must not raise

    out = capsys.readouterr().out
    assert "year 2007" in out
    assert "discovered pages:    1" in out
    assert "fetched pages:       1" in out
    assert "result:              PASS" in out


def test_run_reports_all_years_when_year_not_given(tmp_path, capsys):
    root = tmp_path / "data"
    record_a = _complete_record("a", 2007, root)
    record_b = _complete_record("b", 2025, root)
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": record_a, "b": record_b})

    args = SimpleNamespace(root=root, year=None)
    audit.run(args)  # both complete -- must not raise

    out = capsys.readouterr().out
    assert "all years" in out
    assert "discovered pages:    2" in out
    assert "result:              PASS" in out


def test_run_exits_nonzero_when_pipeline_is_incomplete(tmp_path, capsys):
    root = tmp_path / "data"
    # Discovered but never fetched -- an incomplete pipeline for this scope.
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": _record("a", 2007)})

    args = SimpleNamespace(root=root, year=2007)
    with pytest.raises(SystemExit) as exc_info:
        audit.run(args)

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "result:              FAIL" in out


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
