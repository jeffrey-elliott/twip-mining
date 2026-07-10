"""Tests for view.py, the local read-only HTML browser for command pairs.

Talks to a real (loopback, ephemeral-port) HTTP server rather than mocking
BaseHTTPRequestHandler, since the routing only matters in combination with
the stdlib server plumbing it's built on.
"""
from __future__ import annotations

import threading
import urllib.error
import urllib.request
from contextlib import contextmanager

from clubfloyd_mine import paths, view
from clubfloyd_mine.models import BlockKind, CommandPair, GameRef, ManifestRecord, TranscriptBlock


def _record(source_id, year=2007, source_url=None):
    return ManifestRecord(
        id=source_id,
        source_url=source_url or f"https://example.com/{source_id}.html",
        year=year,
        games=[GameRef(title="Nevermore", author="Nate Cull")],
        raw_path="unused",
    )


def _pair(index, *result_texts, command_text="look", source_id="a"):
    return CommandPair(
        source_id=source_id,
        pair_index=index,
        command_text=command_text,
        result_blocks=[TranscriptBlock(kind=BlockKind.GAME_OUTPUT, text=t) for t in result_texts],
    )


def _write_pairs(record, root, pairs):
    path = paths.command_pairs_path(record.year, record.id, root)
    lines = [p.model_dump_json() for p in pairs]
    paths.ensure_parent(path).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


@contextmanager
def _running_server(root, records):
    server = view.make_server(("127.0.0.1", 0), root=root, records=records)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def _get(base_url, path):
    with urllib.request.urlopen(f"{base_url}{path}") as resp:
        return resp.status, resp.read().decode("utf-8")


# --- pure render helpers ---------------------------------------------------------------


def test_render_index_lists_session_id_game_and_pair_count(tmp_path):
    record = _record("20070901-nevermore")
    _write_pairs(record, tmp_path, [_pair(0, " Taken.", source_id=record.id)])

    html_out = view._render_index({record.id: record}, tmp_path)

    assert "20070901-nevermore" in html_out
    assert "Nevermore" in html_out
    assert ">1<" in html_out  # one pair


def test_render_session_shows_command_result_and_rule_badge():
    record = _record("a")
    pairs = [_pair(0, " Taken.", command_text="take lamp", source_id="a")]

    html_out = view._render_session(record, pairs, outcome_filter=None)

    assert "take lamp" in html_out
    assert "Taken." in html_out
    assert "badge-success" in html_out
    assert record.source_url in html_out


def test_render_session_marks_unmatched_pairs_uncertain():
    record = _record("a")
    pairs = [_pair(0, " An oil-lamp of copper and glass.", source_id="a")]

    html_out = view._render_session(record, pairs, outcome_filter=None)

    assert "badge-uncertain" in html_out


def test_render_session_filter_excludes_non_matching_pairs():
    record = _record("a")
    pairs = [
        _pair(0, " Opened.", command_text="open door", source_id="a"),
        _pair(1, " You can't go that way.", command_text="up", source_id="a"),
    ]

    html_out = view._render_session(record, pairs, outcome_filter="success")

    assert "open door" in html_out
    assert "up" not in html_out


def test_render_session_escapes_html_in_transcript_text():
    record = _record("a")
    pairs = [_pair(0, " <script>alert(1)</script>", command_text="x <thing>", source_id="a")]

    html_out = view._render_session(record, pairs, outcome_filter=None)

    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out


# --- live server -------------------------------------------------------------------------


def test_index_route_serves_html(tmp_path):
    record = _record("a")
    _write_pairs(record, tmp_path, [_pair(0, " Taken.", source_id="a")])

    with _running_server(tmp_path, {"a": record}) as base_url:
        status, body = _get(base_url, "/")

    assert status == 200
    assert "a" in body


def test_session_route_serves_pairs_for_that_session(tmp_path):
    record = _record("a")
    _write_pairs(record, tmp_path, [_pair(0, " Taken.", command_text="take lamp", source_id="a")])

    with _running_server(tmp_path, {"a": record}) as base_url:
        status, body = _get(base_url, f"/session/{record.year}/a")

    assert status == 200
    assert "take lamp" in body


def test_session_route_supports_outcome_filter_query_param(tmp_path):
    record = _record("a")
    _write_pairs(
        record,
        tmp_path,
        [
            _pair(0, " Opened.", command_text="open door", source_id="a"),
            _pair(1, " You can't go that way.", command_text="up", source_id="a"),
        ],
    )

    with _running_server(tmp_path, {"a": record}) as base_url:
        status, body = _get(base_url, f"/session/{record.year}/a?filter=success")

    assert status == 200
    assert "open door" in body
    assert "up" not in body


def test_unknown_session_returns_404(tmp_path):
    record = _record("a")
    with _running_server(tmp_path, {"a": record}) as base_url:
        try:
            urllib.request.urlopen(f"{base_url}/session/2007/does-not-exist")
            assert False, "expected HTTPError"
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
