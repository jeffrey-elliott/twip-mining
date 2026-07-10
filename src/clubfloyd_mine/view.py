"""Local read-only HTML viewer for browsing command pairs.

Not a numbered pipeline pass (like `audit`/`segment`) -- it's a dev tool for
eyeballing extraction and rule-based classification quality by eye, e.g.
before widening a crawl or picking a sample for classify's LLM tier
(classify.classify_pair_llm). Serves data already on disk over a
loopback-only HTTP server; writes nothing and calls no LLM.

Every pair is shown with its classify.classify_pair_rule() outcome (or
"uncertain" if the rule tier didn't match) and each session page links back
to its manifest source_url, so the view never loses the provenance trail
CLAUDE.md's priorities require of generated output.

/verbs and /verb/<verb> give a second, cross-session way to browse the same
data: instead of one session's pairs in transcript order, every pair across
every loaded session with the same normalized first word (e.g. "x lamp" and
"examine desk" both under "examine") shown together, grouped by outcome so
same-shaped cases cluster. Seeing many real instances of one behavior side
by side is what actually surfaces a new classify.py rule candidate -- this
project's whole annotated-screenshot workflow so far has been a manual,
one-transcript-at-a-time version of exactly that.
"""
from __future__ import annotations

import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

from clubfloyd_mine import classify, extract_pairs
from clubfloyd_mine import manifest as manifest_io
from clubfloyd_mine import paths
from clubfloyd_mine.models import CommandPair, ManifestRecord, OutcomeBucket

DEFAULT_PORT = 8765
# Loopback only by default: transcript text isn't meant to be republished
# (CLAUDE.md's data policy), so don't default to exposing it on the network.
DEFAULT_HOST = "127.0.0.1"

# "uncertain" isn't an OutcomeBucket value -- it's classify_pair_rule
# returning None -- so it's appended here rather than living in the enum.
# Driven off OutcomeBucket (not a hardcoded subset) so a future bucket the
# rule tier starts producing shows up as a filter automatically instead of
# silently having no shortcut.
_FILTER_VALUES = [bucket.value for bucket in OutcomeBucket] + ["uncertain"]

# Known single-letter/short abbreviations, from
# doc/classification/examples/uncle_zarf_pd.md's "Important abbreviations"
# list -- deliberately conservative, no unevidenced synonym merging (e.g.
# "get"/"take" stay separate verbs here) per this project's convention of
# not guessing synonyms without corpus evidence.
_VERB_ALIASES = {
    "x": "examine",
    "l": "look",
    "i": "inventory",
    "z": "wait",
    "g": "again",
    "u": "up",
    "d": "down",
}

_STYLE = """
<style>
body { font-family: system-ui, sans-serif; margin: 2rem; color: #222; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: 0.3rem 0.6rem; border-bottom: 1px solid #ddd; font-size: 0.9rem; }
th { background: #f4f4f4; }
.pair { border: 1px solid #ddd; border-radius: 6px; margin: 0.75rem 0; padding: 0.6rem 0.9rem; }
.command { font-weight: 600; font-family: monospace; }
.result { white-space: pre-wrap; font-family: monospace; color: #333; margin: 0.4rem 0 0; }
/* Default background covers any bucket without its own rule below (e.g. a
   new one added to OutcomeBucket before this list is updated) so it still
   reads as a badge instead of blending in unstyled. */
.badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 999px; font-size: 0.75rem; color: white; margin-left: 0.5rem; background: #616161; }
.badge-success { background: #2e7d32; }
.badge-parser_failure { background: #c62828; }
.badge-world_failure { background: #ef6c00; }
.badge-disambiguation { background: #6a1b9a; }
.badge-clarification { background: #8e24aa; }
.badge-inventory_change { background: #00838f; }
.badge-location_change { background: #1565c0; }
.badge-score_or_end_state { background: #4527a0; }
.badge-meta_or_floyd_control { background: #37474f; }
.badge-unknown { background: #9e9e9e; }
.badge-uncertain { background: #9e9e9e; }
a { color: #1565c0; }
.filters a { margin-right: 0.75rem; }
</style>
"""


def _badge(label: str) -> str:
    return f'<span class="badge badge-{html.escape(label)}">{html.escape(label)}</span>'


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>{_STYLE}</head><body>{body}</body></html>"
    )


def _render_not_found() -> str:
    return _page("Not found", "<h1>404</h1><p>Unknown session.</p><p><a href='/'>&larr; all sessions</a></p>")


def _render_index(records: dict[str, ManifestRecord], root) -> str:
    rows = []
    for record in sorted(records.values(), key=lambda r: (r.year, r.id)):
        pairs = extract_pairs.load_command_pairs(record, root)
        games = ", ".join(html.escape(g.title) for g in record.games) or "(unknown game)"
        link = f'<a href="/session/{record.year}/{html.escape(record.id)}">{html.escape(record.id)}</a>'
        rows.append(
            f"<tr><td>{record.year}</td><td>{link}</td><td>{games}</td>"
            f"<td>{html.escape(record.played_date or '')}</td><td>{len(pairs)}</td></tr>"
        )
    body_rows = "\n".join(rows) or "<tr><td colspan='5'>No sessions found.</td></tr>"
    body = (
        "<h1>ClubFloyd sessions</h1>"
        '<p><a href="/verbs">Browse commands by verb &rarr;</a></p>'
        f"<p>{len(records)} session(s) in manifest.</p>"
        "<table><thead><tr><th>Year</th><th>Session</th><th>Game(s)</th>"
        f"<th>Played</th><th>Pairs</th></tr></thead><tbody>{body_rows}</tbody></table>"
    )
    return _page("ClubFloyd sessions", body)


def _normalize_verb(command_text: str) -> str:
    """First whitespace-separated token of a command, lowercased, with
    known abbreviations expanded (_VERB_ALIASES) -- e.g. "x lamp" and
    "examine lamp" both normalize to "examine". Used to group same-behavior
    commands together across sessions for the /verb/<verb> view. Returns
    "" for a blank command_text (the synthetic leading-output pair from
    extract_pairs.py -- see CommandPair.is_leading_output)."""
    stripped = command_text.strip()
    if not stripped:
        return ""
    first = stripped.split(None, 1)[0].lower()
    return _VERB_ALIASES.get(first, first)


def _iter_all_pairs(records: dict[str, ManifestRecord], root):
    """Yield (record, pair) for every command pair across all given
    records, in manifest order. Same full-disk-scan-per-request approach
    _render_index already uses -- fine at this project's current scale (a
    local, single-user dev tool), not meant to hold up under a full
    650-session corpus without revisiting."""
    for record in sorted(records.values(), key=lambda r: (r.year, r.id)):
        for pair in extract_pairs.load_command_pairs(record, root):
            yield record, pair


def _render_verb_index(records: dict[str, ManifestRecord], root) -> str:
    counts: dict[str, int] = {}
    for _, pair in _iter_all_pairs(records, root):
        verb = _normalize_verb(pair.command_text)
        if verb:
            counts[verb] = counts.get(verb, 0) + 1

    rows = []
    for verb, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        link = f'<a href="/verb/{quote(verb, safe="")}">{html.escape(verb)}</a>'
        rows.append(f"<tr><td>{link}</td><td>{count}</td></tr>")
    body_rows = "\n".join(rows) or "<tr><td colspan='2'>No commands found.</td></tr>"
    body = (
        '<p><a href="/">&larr; all sessions</a></p>'
        "<h1>Commands by verb</h1>"
        "<p>Every command pair across all loaded sessions, grouped by its normalized first word "
        '(known abbreviations like "x" &rarr; "examine" are expanded) -- pick a verb to see every '
        "instance side by side and spot classes by eye.</p>"
        f"<table><thead><tr><th>Verb</th><th>Count</th></tr></thead><tbody>{body_rows}</tbody></table>"
    )
    return _page("Commands by verb", body)


def _render_verb_detail(verb: str, records: dict[str, ManifestRecord], root, *, outcome_filter: str | None) -> str:
    matches = []
    for record, pair in _iter_all_pairs(records, root):
        if _normalize_verb(pair.command_text) != verb:
            continue
        outcome = classify.classify_pair_rule(pair)
        label = outcome.value if outcome else "uncertain"
        matches.append((label, record, pair))

    total = len(matches)
    if outcome_filter:
        matches = [m for m in matches if m[0] == outcome_filter]
    shown = len(matches)

    # Group same-outcome pairs together (rather than manifest order) so
    # visually similar cases cluster -- that's the point of this view.
    matches.sort(key=lambda m: (m[0], m[1].year, m[1].id, m[2].pair_index))

    blocks = []
    for label, record, pair in matches:
        result_text = "\n".join(b.text for b in pair.result_blocks) or "(no result)"
        session_link = f'<a href="/session/{record.year}/{html.escape(record.id)}">{html.escape(record.id)}</a>'
        blocks.append(
            '<div class="pair">'
            f'<div><span class="command">&gt; {html.escape(pair.command_text)}</span>{_badge(label)}'
            f' <span style="color:#888">{session_link} #{pair.pair_index}</span></div>'
            f'<pre class="result">{html.escape(result_text)}</pre>'
            "</div>"
        )
    filter_links = " ".join(f'<a href="?filter={value}">{value}</a>' for value in _FILTER_VALUES)
    filters = f'<div class="filters">{filter_links} | <a href="?">all</a></div>'
    body_pairs = "\n".join(blocks) or "<p>No pairs match this filter.</p>"
    body = (
        '<p><a href="/verbs">&larr; all verbs</a></p>'
        f"<h1>&quot;{html.escape(verb)}&quot; across all sessions</h1>"
        f"<p>{shown} of {total} pair(s) shown.</p>"
        f"{filters}{body_pairs}"
    )
    return _page(f'"{verb}"', body)


def _render_session(record: ManifestRecord, pairs: list[CommandPair], *, outcome_filter: str | None) -> str:
    blocks = []
    shown = 0
    for pair in pairs:
        outcome = classify.classify_pair_rule(pair)
        label = outcome.value if outcome else "uncertain"
        if outcome_filter and label != outcome_filter:
            continue
        shown += 1
        result_text = "\n".join(b.text for b in pair.result_blocks) or "(no result)"
        blocks.append(
            '<div class="pair">'
            f'<div><span class="command">&gt; {html.escape(pair.command_text)}</span>{_badge(label)}'
            f' <span style="color:#888">#{pair.pair_index}</span></div>'
            f'<pre class="result">{html.escape(result_text)}</pre>'
            "</div>"
        )
    filter_links = " ".join(f'<a href="?filter={value}">{value}</a>' for value in _FILTER_VALUES)
    filters = f'<div class="filters">{filter_links} | <a href="?">all</a></div>'
    games = ", ".join(html.escape(g.title) for g in record.games) or "(unknown game)"
    body_pairs = "\n".join(blocks) or "<p>No pairs match this filter.</p>"
    body = (
        '<p><a href="/">&larr; all sessions</a></p>'
        f"<h1>{html.escape(record.id)}</h1>"
        f"<p>{games} &mdash; played {html.escape(record.played_date or 'unknown')} &mdash; "
        f'<a href="{html.escape(record.source_url)}" target="_blank" rel="noopener">source</a></p>'
        f"<p>{shown} of {len(pairs)} pair(s) shown.</p>"
        f"{filters}{body_pairs}"
    )
    return _page(record.id, body)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002 (stdlib signature)
        pass  # quiet by default -- this is a local dev tool, not a monitored service

    def _send_html(self, status: int, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802 (stdlib method name)
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        query = parse_qs(parsed.query)
        records: dict[str, ManifestRecord] = self.server.records  # type: ignore[attr-defined]
        root = self.server.root  # type: ignore[attr-defined]

        if not parts:
            self._send_html(200, _render_index(records, root))
            return

        if len(parts) == 1 and parts[0] == "verbs":
            self._send_html(200, _render_verb_index(records, root))
            return

        if len(parts) == 2 and parts[0] == "verb":
            verb = unquote(parts[1])
            outcome_filter = query.get("filter", [None])[0]
            self._send_html(200, _render_verb_detail(verb, records, root, outcome_filter=outcome_filter))
            return

        if len(parts) == 3 and parts[0] == "session":
            _, year_str, source_id = parts
            record = records.get(source_id)
            if record is None or str(record.year) != year_str:
                self._send_html(404, _render_not_found())
                return
            pairs = extract_pairs.load_command_pairs(record, root)
            outcome_filter = query.get("filter", [None])[0]
            self._send_html(200, _render_session(record, pairs, outcome_filter=outcome_filter))
            return

        self._send_html(404, _render_not_found())


def make_server(address: tuple[str, int], *, root, records: dict[str, ManifestRecord]) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(address, _Handler)
    server.root = root  # type: ignore[attr-defined]
    server.records = records  # type: ignore[attr-defined]
    return server


def run(args: argparse.Namespace) -> None:
    manifest_file = paths.manifest_path(args.root)
    records = manifest_io.load_manifest(manifest_file)
    if not records:
        print(f"view: no records in {manifest_file}; run discover first")
        return

    year = getattr(args, "year", None)
    selected = {r.id: r for r in records.values() if year is None or r.year == year}
    if not selected:
        scope = f"year {year}" if year is not None else "any year"
        print(f"view: no records found for {scope}")
        return

    server = make_server((args.host, args.port), root=args.root, records=selected)
    host, port = server.server_address[:2]
    print(f"view: serving {len(selected)} session(s) at http://{host}:{port}/ (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nview: stopping")
    finally:
        server.server_close()
