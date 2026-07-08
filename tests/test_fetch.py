import hashlib
from types import SimpleNamespace

import pytest

from clubfloyd_mine import fetch, manifest as manifest_io, paths
from clubfloyd_mine.models import FetchMeta, GameRef, ManifestRecord, ManifestStatus

ALLOW_ALL_ROBOTS = fetch.HttpResponse(200, b"User-agent: *\nAllow: /\n")
DISALLOW_ALL_ROBOTS = fetch.HttpResponse(200, b"User-agent: *\nDisallow: /\n")


class FakeHttpGet:
    """Records every URL it's asked for; raises on anything not stubbed so
    tests can assert exactly which requests (if any) were made."""

    def __init__(self, responses):
        self._responses = dict(responses)
        self.calls: list[str] = []

    def __call__(self, url: str, user_agent: str) -> fetch.HttpResponse:
        self.calls.append(url)
        result = self._responses.get(url)
        if result is None:
            raise AssertionError(f"unexpected request for {url}")
        if isinstance(result, BaseException):
            raise result
        return result


def _record(source_id="20250101-no-more", year=2025, status=ManifestStatus.DISCOVERED):
    return ManifestRecord(
        id=source_id,
        source_url=f"https://example.com/{source_id}.html",
        year=year,
        games=[GameRef(title="No More", author="Tabitha")],
        raw_path="unused-placeholder",
        status=status,
    )


def test_fetch_one_writes_html_and_meta(tmp_path):
    record = _record()
    body = b"<html>hello</html>"
    http_get = FakeHttpGet(
        {
            "https://example.com/robots.txt": ALLOW_ALL_ROBOTS,
            record.source_url: fetch.HttpResponse(200, body),
        }
    )
    robots = fetch.RobotsCache(http_get, "test-agent")

    result = fetch.fetch_one(
        record, root=tmp_path, user_agent="test-agent", http_get=http_get,
        robots=robots, force=False, dry_run=False,
    )

    assert result.action == "fetched"
    html_path = paths.raw_html_path(record.year, record.id, tmp_path)
    meta_path = paths.raw_meta_path(record.year, record.id, tmp_path)
    assert html_path.read_bytes() == body

    meta = FetchMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))
    assert meta.sha256 == hashlib.sha256(body).hexdigest()
    assert meta.http_status == 200
    assert meta.content_length == len(body)
    assert meta.user_agent == "test-agent"
    assert meta.previous_sha256 is None


def test_fetch_one_skips_existing_without_any_network_call(tmp_path):
    record = _record()
    html_path = paths.raw_html_path(record.year, record.id, tmp_path)
    paths.ensure_parent(html_path).write_bytes(b"already here")
    http_get = FakeHttpGet({})  # any call raises
    robots = fetch.RobotsCache(http_get, "test-agent")

    result = fetch.fetch_one(
        record, root=tmp_path, user_agent="test-agent", http_get=http_get,
        robots=robots, force=False, dry_run=False,
    )

    assert result.action == "skipped_exists"
    assert http_get.calls == []


def test_fetch_one_force_refetch_records_previous_sha256(tmp_path):
    record = _record()
    old_body = b"old content"
    new_body = b"new content, changed"
    http_get = FakeHttpGet(
        {
            "https://example.com/robots.txt": ALLOW_ALL_ROBOTS,
            record.source_url: fetch.HttpResponse(200, old_body),
        }
    )
    robots = fetch.RobotsCache(http_get, "test-agent")
    fetch.fetch_one(
        record, root=tmp_path, user_agent="test-agent", http_get=http_get,
        robots=robots, force=False, dry_run=False,
    )

    http_get._responses[record.source_url] = fetch.HttpResponse(200, new_body)
    result = fetch.fetch_one(
        record, root=tmp_path, user_agent="test-agent", http_get=http_get,
        robots=robots, force=True, dry_run=False,
    )

    assert result.action == "fetched"
    html_path = paths.raw_html_path(record.year, record.id, tmp_path)
    meta_path = paths.raw_meta_path(record.year, record.id, tmp_path)
    assert html_path.read_bytes() == new_body
    meta = FetchMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))
    assert meta.sha256 == hashlib.sha256(new_body).hexdigest()
    assert meta.previous_sha256 == hashlib.sha256(old_body).hexdigest()


@pytest.mark.parametrize("pre_existing", [False, True])
def test_fetch_one_dry_run_makes_zero_network_calls(tmp_path, pre_existing):
    record = _record()
    if pre_existing:
        html_path = paths.raw_html_path(record.year, record.id, tmp_path)
        paths.ensure_parent(html_path).write_bytes(b"already here")
    http_get = FakeHttpGet({})  # any call raises
    robots = fetch.RobotsCache(http_get, "test-agent")

    result = fetch.fetch_one(
        record, root=tmp_path, user_agent="test-agent", http_get=http_get,
        robots=robots, force=pre_existing, dry_run=True,
    )

    assert result.action == ("would_refetch" if pre_existing else "would_fetch")
    assert http_get.calls == []


def test_fetch_one_respects_robots_disallow(tmp_path):
    record = _record()
    http_get = FakeHttpGet({"https://example.com/robots.txt": DISALLOW_ALL_ROBOTS})
    robots = fetch.RobotsCache(http_get, "test-agent")

    result = fetch.fetch_one(
        record, root=tmp_path, user_agent="test-agent", http_get=http_get,
        robots=robots, force=False, dry_run=False,
    )

    assert result.action == "skipped_robots"
    assert record.source_url not in http_get.calls
    assert not paths.raw_html_path(record.year, record.id, tmp_path).exists()


def test_fetch_one_records_error_on_bad_http_status(tmp_path):
    record = _record()
    http_get = FakeHttpGet(
        {
            "https://example.com/robots.txt": ALLOW_ALL_ROBOTS,
            record.source_url: fetch.HttpResponse(404, b"not found"),
        }
    )
    robots = fetch.RobotsCache(http_get, "test-agent")

    result = fetch.fetch_one(
        record, root=tmp_path, user_agent="test-agent", http_get=http_get,
        robots=robots, force=False, dry_run=False,
    )

    assert result.action == "error"
    assert "404" in result.detail
    assert not paths.raw_html_path(record.year, record.id, tmp_path).exists()


def test_fetch_one_records_error_on_connection_failure(tmp_path):
    record = _record()
    http_get = FakeHttpGet(
        {
            "https://example.com/robots.txt": ALLOW_ALL_ROBOTS,
            record.source_url: OSError("connection refused"),
        }
    )
    robots = fetch.RobotsCache(http_get, "test-agent")

    result = fetch.fetch_one(
        record, root=tmp_path, user_agent="test-agent", http_get=http_get,
        robots=robots, force=False, dry_run=False,
    )

    assert result.action == "error"
    assert "connection refused" in result.detail


def test_robots_cache_fetches_robots_txt_once_per_host():
    http_get = FakeHttpGet(
        {
            "https://example.com/robots.txt": ALLOW_ALL_ROBOTS,
        }
    )
    robots = fetch.RobotsCache(http_get, "test-agent")

    assert robots.can_fetch("https://example.com/a.html") is True
    assert robots.can_fetch("https://example.com/b.html") is True
    assert http_get.calls == ["https://example.com/robots.txt"]


def test_robots_cache_missing_robots_txt_defaults_to_allow():
    http_get = FakeHttpGet({"https://example.com/robots.txt": fetch.HttpResponse(404, b"")})
    robots = fetch.RobotsCache(http_get, "test-agent")
    assert robots.can_fetch("https://example.com/a.html") is True


def test_rate_limited_get_does_not_sleep_before_first_call():
    sleeps = []
    limited = fetch.RateLimitedGet(
        FakeHttpGet({"u": fetch.HttpResponse(200, b"x")}), delay=5.0, sleep=sleeps.append
    )
    limited("u", "ua")
    assert sleeps == []


def test_rate_limited_get_sleeps_between_subsequent_calls():
    sleeps = []
    inner = FakeHttpGet({"u": fetch.HttpResponse(200, b"x")})
    limited = fetch.RateLimitedGet(inner, delay=5.0, sleep=sleeps.append)
    limited("u", "ua")
    limited("u", "ua")
    limited("u", "ua")
    assert sleeps == [5.0, 5.0]


def test_run_dry_run_makes_no_network_calls_and_leaves_manifest_untouched(tmp_path, monkeypatch):
    def fail_if_called(url, user_agent):
        raise AssertionError(f"unexpected real network call to {url}")

    monkeypatch.setattr(fetch, "urllib_get", fail_if_called)

    root = tmp_path / "data"
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": _record("a")})
    before = manifest_file.read_text(encoding="utf-8")

    args = SimpleNamespace(
        root=root, force=False, delay=0.0, user_agent="test-agent", dry_run=True
    )
    fetch.run(args)

    assert manifest_file.read_text(encoding="utf-8") == before


def test_run_fetches_all_records_and_advances_status(tmp_path, monkeypatch):
    record_a = _record("a")
    record_b = _record("b")
    responses = {
        "https://example.com/robots.txt": ALLOW_ALL_ROBOTS,
        record_a.source_url: fetch.HttpResponse(200, b"content a"),
        record_b.source_url: fetch.HttpResponse(200, b"content b"),
    }
    fake = FakeHttpGet(responses)
    monkeypatch.setattr(fetch, "urllib_get", fake)

    root = tmp_path / "data"
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": record_a, "b": record_b})

    args = SimpleNamespace(
        root=root, force=False, delay=0.0, user_agent="test-agent", dry_run=False
    )
    fetch.run(args)

    updated = manifest_io.load_manifest(manifest_file)
    assert updated["a"].status is ManifestStatus.FETCHED
    assert updated["b"].status is ManifestStatus.FETCHED
    assert updated["a"].raw_path == str(paths.raw_html_path(record_a.year, record_a.id, root))

    assert paths.raw_html_path(record_a.year, record_a.id, root).read_bytes() == b"content a"
    assert paths.raw_html_path(record_b.year, record_b.id, root).read_bytes() == b"content b"


def test_run_marks_discovered_record_as_error_on_failure(tmp_path, monkeypatch):
    record = _record(status=ManifestStatus.DISCOVERED)
    fake = FakeHttpGet(
        {
            "https://example.com/robots.txt": ALLOW_ALL_ROBOTS,
            record.source_url: fetch.HttpResponse(500, b"boom"),
        }
    )
    monkeypatch.setattr(fetch, "urllib_get", fake)

    root = tmp_path / "data"
    manifest_file = paths.manifest_path(root)
    manifest_io.write_manifest(manifest_file, {"a": record})

    args = SimpleNamespace(
        root=root, force=False, delay=0.0, user_agent="test-agent", dry_run=False
    )
    fetch.run(args)

    updated = manifest_io.load_manifest(manifest_file)
    assert updated[record.id].status is ManifestStatus.ERROR
