# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# twip-mining agent rules

This project builds deterministic tooling for mining ClubFloyd transcripts for Twip design evidence.

## Priorities

1. Preserve source provenance.
2. Prefer deterministic extraction before LLM interpretation.
3. Every generated record must trace back to a source URL and source id.
4. Do not republish full transcripts in committed files.
5. Keep passes restartable and idempotent.
6. Add tests before broad crawling.
7. Work in small commits.

## Development commands

```bash
pip install -e ".[dev]"       # install package + dev deps
pytest                         # run all tests
pytest tests/test_discover.py  # run a single test file
pytest -k "test_name"          # run a single test by name
```

The CLI entry point is `clubfloyd` (defined in `pyproject.toml`), backed by `src/clubfloyd_mine/cli.py`.

## Pipeline passes and data flow

Each pass reads from and writes to well-defined paths. All passes must be restartable and idempotent.

| Pass | Command | Input | Output |
|------|---------|-------|--------|
| 1 | `clubfloyd discover` | Index page HTML | `data/manifest.jsonl` |
| 2 | `clubfloyd fetch` | `manifest.jsonl` | `data/raw/<year>/<id>/source.html` + `meta.json` |
| 3 | `clubfloyd normalize` | Raw HTML | `data/text/<year>/<id>/transcript.txt` + `transcript.json` |
| 4 | `clubfloyd extract-pairs` | Normalized JSON | `data/parsed/<year>/<id>/command_pairs.jsonl` |
| 5 | `clubfloyd classify` | Command pairs | Outcome bucket per pair |
| 6 | `clubfloyd make-records` | Classified pairs | `data/records/<category>/*.md` |
| — | `clubfloyd audit` | manifest + data dirs | Consistency report |
| — | `clubfloyd segment` | Normalized transcript | Per-game segments |

## Data policy

- Raw mirrored HTML lives under `data/raw/` and is gitignored.
- Normalized transcript text lives under `data/text/` and is gitignored.
- Parsed command pairs may be gitignored by default.
- Small fixtures are allowed in `tests/fixtures/`.
- Generated summaries/records may be committed only if they contain short excerpts and source references, not full transcript dumps.

## Key data structures

**Manifest record** (`data/manifest.jsonl`):
```json
{
  "id": "2025-01-26-no-more",
  "source_url": "https://allthingsjacq.com/intfic_clubfloyd_20250105.html",
  "year": 2025,
  "played_date": "2025-01-26",
  "games": [{"title": "No More", "author": "Tabitha"}],
  "raw_path": "data/raw/2025/2025-01-26-no-more/source.html",
  "status": "discovered"
}
```

**Normalized block kinds**: `discussion`, `command` (to Floyd), `game_output`, `bot_meta`

**Outcome buckets** (Pass 5): `success`, `parser_failure`, `world_failure`, `disambiguation`, `clarification`, `inventory_change`, `location_change`, `score_or_end_state`, `meta_or_floyd_control`, `unknown`

**Classify strategy**: regex/rule first → LLM for uncertain → human-review queue for low confidence.

## Source

ClubFloyd index: `https://allthingsjacq.com/interactive_fiction.html`

Transcripts span 2007-09-01 through 2025-07-03. Human commentary is in the right column; Floyd/game output is in the left column.

## Testing

Use pytest. Each pass needs fixture-based tests before being run across the full corpus. Fixtures live in `tests/fixtures/`.
