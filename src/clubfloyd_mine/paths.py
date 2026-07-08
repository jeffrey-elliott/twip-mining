"""Path helpers for the pipeline's on-disk layout (see README.md's Layout section).

All functions are pure: given a data root, a year, and a source id, they
compute where a pass should read or write. Nothing here touches the
filesystem except `ensure_parent`, which passes call before writing.
"""
from __future__ import annotations

import os
from pathlib import Path

_DATA_ROOT_ENV_VAR = "CLUBFLOYD_DATA_ROOT"
_DEFAULT_DATA_ROOT = Path("data")


def data_root(root: Path | str | None = None) -> Path:
    """Resolve the data root: explicit arg > env var > ./data."""
    if root is not None:
        return Path(root)
    env_value = os.environ.get(_DATA_ROOT_ENV_VAR)
    if env_value:
        return Path(env_value)
    return _DEFAULT_DATA_ROOT


def manifest_path(root: Path | str | None = None) -> Path:
    return data_root(root) / "manifest.jsonl"


def raw_dir(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return data_root(root) / "raw" / str(year) / source_id


def raw_html_path(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return raw_dir(year, source_id, root) / "source.html"


def raw_meta_path(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return raw_dir(year, source_id, root) / "meta.json"


def text_dir(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return data_root(root) / "text" / str(year) / source_id


def transcript_txt_path(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return text_dir(year, source_id, root) / "transcript.txt"


def transcript_json_path(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return text_dir(year, source_id, root) / "transcript.json"


def parsed_dir(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return data_root(root) / "parsed" / str(year) / source_id


def session_json_path(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return parsed_dir(year, source_id, root) / "session.json"


def command_pairs_path(year: int, source_id: str, root: Path | str | None = None) -> Path:
    return parsed_dir(year, source_id, root) / "command_pairs.jsonl"


def records_dir(category: str, root: Path | str | None = None) -> Path:
    return data_root(root) / "records" / category


def ensure_parent(path: Path) -> Path:
    """Create the parent directory of `path` if needed, and return `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
