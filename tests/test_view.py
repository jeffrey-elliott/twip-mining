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
    # Note: the CSS block in every page always contains the literal string
    # "badge-success" etc. (it's a static stylesheet, not conditional), so
    # asserting a badge class name is *anywhere in the page* would pass even
    # if the pair were tagged with a completely different bucket. Assert
    # the exact <span> markup for this pair's outcome instead.
    record = _record("a")
    pairs = [_pair(0, " Opened.", command_text="open door", source_id="a")]

    html_out = view._render_session(record, pairs, outcome_filter=None)

    assert "open door" in html_out
    assert "Opened." in html_out
    assert view._badge("success") in html_out
    assert record.source_url in html_out


def test_render_session_marks_unmatched_pairs_uncertain():
    record = _record("a")
    # "push idol", not the default "look": _EXAMINE_OR_LOOK_COMMANDS now
    # rule-classifies bare look/examine prose as success, so this needs a
    # verb the rule tier genuinely can't resolve.
    pairs = [_pair(0, " The idol wobbles unsteadily but does not fall.", command_text="push idol", source_id="a")]

    html_out = view._render_session(record, pairs, outcome_filter=None)

    assert view._badge("uncertain") in html_out


def test_render_session_filter_excludes_non_matching_pairs():
    # Same caveat as above: check the excluded pair's own <span> markup, not
    # a bare substring of its command text -- "up" is short enough to
    # coincidentally match unrelated page text (e.g. inside a CSS comment).
    record = _record("a")
    pairs = [
        _pair(0, " Opened.", command_text="open door", source_id="a"),
        _pair(1, " You can't go that way.", command_text="up", source_id="a"),
    ]

    html_out = view._render_session(record, pairs, outcome_filter="success")

    assert "open door" in html_out
    assert '<span class="command">&gt; up</span>' not in html_out


def test_render_session_shows_new_rule_tier_buckets_with_their_own_badge():
    # Guards against the filter/badge lists silently going stale when
    # classify_pair_rule grows new buckets (see classify.py's docstring).
    record = _record("a")
    pairs = [_pair(0, " You already have that.", command_text="take lamp", source_id="a")]

    html_out = view._render_session(record, pairs, outcome_filter=None)

    assert view._badge("world_failure") in html_out
    assert '<a href="?filter=world_failure">world_failure</a>' in html_out


def test_render_session_escapes_html_in_transcript_text():
    record = _record("a")
    pairs = [_pair(0, " <script>alert(1)</script>", command_text="x <thing>", source_id="a")]

    html_out = view._render_session(record, pairs, outcome_filter=None)

    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out


# --- verb normalization / cross-session views -----------------------------------------


def test_normalize_verb_expands_known_abbreviation():
    assert view._normalize_verb("x lamp") == "examine"


def test_normalize_verb_leaves_full_word_alone():
    assert view._normalize_verb("examine lamp") == "examine"


def test_normalize_verb_leaves_unmapped_verb_alone():
    assert view._normalize_verb("take key") == "take"


def test_normalize_verb_is_case_insensitive():
    assert view._normalize_verb("X Lamp") == "examine"


def test_normalize_verb_of_blank_command_is_empty_string():
    # The synthetic leading-output pair from extract_pairs.py has
    # command_text="" -- it shouldn't show up as a fake "" verb.
    assert view._normalize_verb("") == ""


def test_render_verb_index_groups_x_and_examine_under_one_count(tmp_path):
    record = _record("a")
    _write_pairs(
        record,
        tmp_path,
        [
            _pair(0, " An oil-lamp.", command_text="x lamp", source_id="a"),
            _pair(1, " A writing desk.", command_text="examine desk", source_id="a"),
            _pair(2, " Taken.", command_text="take key", source_id="a"),
        ],
    )

    html_out = view._render_verb_index({record.id: record}, tmp_path)

    assert '<a href="/verb/examine">examine</a>' in html_out
    assert "<td>2</td>" in html_out  # two "examine"-family commands
    assert '<a href="/verb/take">take</a>' in html_out


def test_render_verb_detail_shows_instances_across_sessions_with_source_link(tmp_path):
    record_a = _record("a")
    record_b = _record("b")
    _write_pairs(record_a, tmp_path, [_pair(0, " An oil-lamp.", command_text="x lamp", source_id="a")])
    _write_pairs(record_b, tmp_path, [_pair(0, " A writing desk.", command_text="examine desk", source_id="b")])

    html_out = view._render_verb_detail("examine", {"a": record_a, "b": record_b}, tmp_path, outcome_filter=None)

    assert "x lamp" in html_out
    assert "examine desk" in html_out
    assert '<a href="/session/2007/a">a</a>' in html_out
    assert '<a href="/session/2007/b">b</a>' in html_out


def test_render_verb_detail_filter_excludes_non_matching_outcome(tmp_path):
    record = _record("a")
    _write_pairs(
        record,
        tmp_path,
        [
            _pair(0, " An oil-lamp.", command_text="x lamp", source_id="a"),
            _pair(1, " You can't see any such thing.", command_text="x unicorn", source_id="a"),
        ],
    )

    html_out = view._render_verb_detail("examine", {"a": record}, tmp_path, outcome_filter="parser_failure")

    assert "x unicorn" in html_out
    assert "x lamp" not in html_out


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
    assert '<span class="command">&gt; up</span>' not in body


def test_unknown_session_returns_404(tmp_path):
    record = _record("a")
    with _running_server(tmp_path, {"a": record}) as base_url:
        try:
            urllib.request.urlopen(f"{base_url}/session/2007/does-not-exist")
            assert False, "expected HTTPError"
        except urllib.error.HTTPError as exc:
            assert exc.code == 404


def test_verbs_route_serves_html(tmp_path):
    record = _record("a")
    _write_pairs(record, tmp_path, [_pair(0, " An oil-lamp.", command_text="x lamp", source_id="a")])

    with _running_server(tmp_path, {"a": record}) as base_url:
        status, body = _get(base_url, "/verbs")

    assert status == 200
    assert '<a href="/verb/examine">examine</a>' in body


def test_verb_detail_route_serves_matching_pairs_across_sessions(tmp_path):
    record_a = _record("a")
    record_b = _record("b")
    _write_pairs(record_a, tmp_path, [_pair(0, " An oil-lamp.", command_text="x lamp", source_id="a")])
    _write_pairs(record_b, tmp_path, [_pair(0, " A writing desk.", command_text="examine desk", source_id="b")])

    with _running_server(tmp_path, {"a": record_a, "b": record_b}) as base_url:
        status, body = _get(base_url, "/verb/examine")

    assert status == 200
    assert "x lamp" in body
    assert "examine desk" in body


def test_verb_detail_route_handles_url_reserved_verb(tmp_path):
    # "?" is a real meta-command verb (classify.py's _META_COMMANDS) --
    # exercises the quote()/unquote() round-trip for a URL-reserved char.
    record = _record("a")
    _write_pairs(record, tmp_path, [_pair(0, " Type HINT for a hint.", command_text="?", source_id="a")])

    with _running_server(tmp_path, {"a": record}) as base_url:
        status, body = _get(base_url, "/verb/%3F")

    assert status == 200
    assert "Type HINT for a hint." in body
