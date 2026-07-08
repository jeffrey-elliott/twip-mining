from pathlib import Path
from types import SimpleNamespace

from clubfloyd_mine import discover
from clubfloyd_mine.models import ManifestStatus

FIXTURE = Path(__file__).parent / "fixtures" / "index_sample.html"


def _records_by_id(records):
    return {r.id: r for r in records}


def test_parse_index_html_finds_expected_record_count():
    records = discover.parse_index_html(FIXTURE.read_text(encoding="utf-8"))
    # 11 in 2007 (one grouped 4-game session) + 4 in 2012 (one grouped
    # 2-game, one grouped 3-game) + 7 in 2025.
    assert len(records) == 22


def test_parse_index_html_groups_multi_game_session_by_href():
    records = _records_by_id(discover.parse_index_html(FIXTURE.read_text(encoding="utf-8")))
    record = records["20071204-the-day-i-shot-hitler"]
    assert record.year == 2007
    assert record.source_url == "https://allthingsjacq.com/intfic_clubfloyd_20071204.html"
    assert [g.title for g in record.games] == [
        "The Day I Shot Hitler",
        "Nazi Mice",
        "The War On New Year's",
        "Not the Same Auld Lang Syne",
    ]
    assert record.status is ManifestStatus.DISCOVERED
    assert record.played_date is None
    assert record.page_title is None


def test_parse_index_html_title_containing_the_word_by_is_not_split():
    records = _records_by_id(discover.parse_index_html(FIXTURE.read_text(encoding="utf-8")))
    record = records["20250603-monk-by-the-sea"]
    assert len(record.games) == 1
    assert record.games[0].title == "Monk by the Sea"
    assert record.games[0].author == "Elizabeth Decoste"


def test_parse_index_html_strips_nf_marker_from_title():
    records = _records_by_id(discover.parse_index_html(FIXTURE.read_text(encoding="utf-8")))
    record = records["20120403-nf-a-comedy-of-error-messages"]
    assert record.games[0].title == "A Comedy of Error Messages"
    assert record.games[0].author == "Adam Le Doux"
    assert record.source_url.endswith("intfic_clubfloyd_20120403-NF.html")


def test_parse_index_html_decodes_html_entities():
    records = _records_by_id(discover.parse_index_html(FIXTURE.read_text(encoding="utf-8")))
    record = records["20071204-the-day-i-shot-hitler"]
    authors = [g.author for g in record.games]
    assert "Marius Müller" in authors


def test_parse_index_html_preserves_multi_author_string_verbatim():
    records = _records_by_id(discover.parse_index_html(FIXTURE.read_text(encoding="utf-8")))
    record = records["20250701-wild-west"]
    assert record.games[0].author == "Bonaventura Di Bello, Garry Francis, and Gianluca Girelli"


def test_parse_index_html_ignores_commented_out_template_line():
    records = discover.parse_index_html(FIXTURE.read_text(encoding="utf-8"))
    assert not any("2020----" in r.source_url for r in records)
    assert not any(g.title == "Game" for r in records for g in r.games)


def test_merge_discovered_adds_new_and_preserves_existing():
    records = discover.parse_index_html(FIXTURE.read_text(encoding="utf-8"))
    first_id = records[0].id
    advanced = records[0].model_copy(update={"status": ManifestStatus.CLASSIFIED})

    merged, new_count = discover.merge_discovered({first_id: advanced}, records)

    assert new_count == len(records) - 1
    assert merged[first_id].status is ManifestStatus.CLASSIFIED
    assert len(merged) == len(records)


def test_raw_path_respects_custom_root():
    records = _records_by_id(
        discover.parse_index_html(FIXTURE.read_text(encoding="utf-8"), root="/srv/cf-data")
    )
    record = records["20070901-nevermore"]
    assert record.raw_path == "/srv/cf-data/raw/2007/20070901-nevermore/source.html"


def test_run_writes_manifest_and_is_idempotent(tmp_path):
    root = tmp_path / "data"
    args = SimpleNamespace(input=FIXTURE, index_url=discover.INDEX_URL, root=root)

    discover.run(args)
    manifest_file = root / "manifest.jsonl"
    assert manifest_file.exists()
    first_lines = manifest_file.read_text(encoding="utf-8").splitlines()
    assert len(first_lines) == 22
    assert all(str(root / "raw") in line for line in first_lines)

    # Re-running against the same fixture should not duplicate records.
    discover.run(args)
    second_lines = manifest_file.read_text(encoding="utf-8").splitlines()
    assert len(second_lines) == 22
    assert sorted(first_lines) == sorted(second_lines)
