"""State staleness, completion checks, and timestamps for Forge skill sessions."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.shared.skill_state import SkillState


def now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def stale_session_threshold_seconds() -> float:
    """Session inactivity threshold used to classify stale in-progress states."""
    raw = os.environ.get("FORGE_STALE_SESSION_HOURS", "24").strip()
    try:
        hours = float(raw)
    except ValueError:
        hours = 24.0
    if hours <= 0:
        hours = 24.0
    return hours * 3600.0


def parse_iso_timestamp(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# Backward-compatible alias (orchestrator tests may use private name via re-export)
_parse_iso_timestamp = parse_iso_timestamp


def is_state_effectively_complete(state: SkillState) -> bool:
    """Treat legacy max-step states as complete when completed_at is absent."""
    if state.completed_at:
        return True
    if state.max_step <= 0:
        return False
    return state.current_step >= state.max_step and state.last_completed_step >= state.max_step


def is_state_stale(state: SkillState, path: Path) -> bool:
    """True when an in-progress state has not been touched recently."""
    if is_state_effectively_complete(state):
        return False
    touched = (
        parse_iso_timestamp(state.last_touched_at)
        or parse_iso_timestamp(state.started_at)
        or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    )
    age_seconds = (datetime.now(timezone.utc) - touched).total_seconds()
    return age_seconds > stale_session_threshold_seconds()


def is_evaluate_state_stale(data: dict[str, Any], path: Path) -> bool:
    """Staleness check for raw evaluate-state JSON objects."""
    touched = (
        parse_iso_timestamp(data.get("last_touched_at"))
        or parse_iso_timestamp(data.get("started_at"))
        or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    )
    age_seconds = (datetime.now(timezone.utc) - touched).total_seconds()
    return age_seconds > stale_session_threshold_seconds()
