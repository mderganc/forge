"""JSONL event log for Studio user interactions."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

EVENTS_FILE = "events.jsonl"
CURSOR_FILE = "read.cursor"
SCHEMA_VERSION = 1


def events_path(state_dir: Path) -> Path:
    return state_dir / EVENTS_FILE


def cursor_path(state_dir: Path) -> Path:
    return state_dir / CURSOR_FILE


def clear_events(state_dir: Path) -> None:
    path = events_path(state_dir)
    if path.exists():
        path.unlink()


def append_event(state_dir: Path, event: dict[str, Any]) -> dict[str, Any]:
    state_dir.mkdir(parents=True, exist_ok=True)
    row = {"v": SCHEMA_VERSION, "ts": int(time.time()), **event}
    with events_path(state_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _read_all_lines(state_dir: Path) -> list[str]:
    path = events_path(state_dir)
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def read_events_since_cursor(state_dir: Path, *, clear_cursor: bool = False) -> tuple[list[dict[str, Any]], int]:
    """Return new events since last cursor and the new cursor (line count)."""
    lines = _read_all_lines(state_dir)
    cur = 0
    cp = cursor_path(state_dir)
    if cp.is_file():
        try:
            cur = int(cp.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            cur = 0
    new_lines = lines[cur:]
    events: list[dict[str, Any]] = []
    for line in new_lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                events.append(obj)
        except json.JSONDecodeError:
            continue
    new_cursor = len(lines)
    if not clear_cursor:
        cp.write_text(str(new_cursor), encoding="utf-8")
    return events, new_cursor


def set_cursor(state_dir: Path, position: int) -> None:
    cursor_path(state_dir).write_text(str(position), encoding="utf-8")
