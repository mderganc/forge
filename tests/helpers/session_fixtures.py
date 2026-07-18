"""Session and flat-state helpers for Forge regression tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_session_state(
    base: Path,
    skill: str,
    *,
    session_id: str = "abc",
    current_step: int = 1,
    last_completed_step: int = 0,
    max_step: int = 6,
    custom: dict[str, Any] | None = None,
    started_at: str | None = None,
    last_touched_at: str | None = None,
) -> Path:
    """Write ``.forge/sessions/{id}/session.json`` and return the path."""
    now = _now_iso()
    path = base / ".forge" / "sessions" / session_id / "session.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "skill_name": skill,
        "session_id": session_id,
        "current_step": current_step,
        "last_completed_step": last_completed_step,
        "max_step": max_step,
        "started_at": started_at or now,
        "completed_at": None,
        "last_touched_at": last_touched_at if last_touched_at is not None else now,
        "custom": custom or {},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_completed_flat_state(
    base: Path,
    skill: str,
    *,
    current_step: int = 7,
    last_completed_step: int = 7,
    max_step: int = 7,
    completed_at: str = "2026-05-07T00:00:00+00:00",
) -> Path:
    """Write a completed flat state under ``.forge/state/{skill}.json``."""
    path = base / ".forge" / "state" / f"{skill}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    now = _now_iso()
    payload = {
        "skill_name": skill,
        "current_step": current_step,
        "last_completed_step": last_completed_step,
        "max_step": max_step,
        "started_at": now,
        "completed_at": completed_at,
        "last_touched_at": now,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_stale_flat_state(
    base: Path,
    skill: str,
    *,
    current_step: int = 7,
    last_completed_step: int = 7,
    max_step: int = 7,
) -> Path:
    """Write a logically complete flat state without ``completed_at`` (cleanup eligible)."""
    path = base / ".forge" / "state" / f"{skill}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    now = _now_iso()
    payload = {
        "skill_name": skill,
        "current_step": current_step,
        "last_completed_step": last_completed_step,
        "max_step": max_step,
        "started_at": now,
        "last_touched_at": now,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
