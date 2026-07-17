"""Shared sub-agent lifecycle reminders for Cursor and Claude Code hooks."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LIFECYCLE_MSG = (
    "forge subagents: Before this tool call, close unused sub-agents. "
    "Codex: `close_agent` for every finished `spawn_agent` (wait first if you still need output). "
    "Cursor/Claude: resume or close completed background Task/Agent sessions — do not leave them open across tool calls."
)

PROGRESS_MSG = (
    "forge subagents: While agents are running, Read `.forge/state/subagent-progress/*.json` "
    "(and `~/.cursor/subagents/` when present) and relay a short status — do not stay silent "
    "until completion. Subagents must update those files per templates/subagent-progress.md."
)

_SKIP_TOOLS = frozenset(
    {
        "close_agent",
        "wait_agent",
    }
)

_STATE_VERSION = 1


def lifecycle_suppressed() -> bool:
    v = os.environ.get("FORGE_SKIP_SUBAGENT_LIFECYCLE", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _tool_input(data: dict[str, Any]) -> dict[str, Any]:
    ti = data.get("tool_input")
    if isinstance(ti, dict):
        return ti
    return data if isinstance(data, dict) else {}


def _tool_name(data: dict[str, Any]) -> str:
    return str(data.get("tool_name") or data.get("tool") or "").strip()


def _agent_id_from_mapping(mapping: dict[str, Any]) -> str | None:
    for key in (
        "agent_id",
        "agentId",
        "subagent_id",
        "subagentId",
        "conversation_id",
        "conversationId",
        "id",
        "resume",
    ):
        val = mapping.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def extract_agent_id(data: dict[str, Any]) -> str | None:
    found = _agent_id_from_mapping(data)
    if found:
        return found
    return _agent_id_from_mapping(_tool_input(data))


def should_skip_lifecycle_reminder(data: dict[str, Any]) -> bool:
    if lifecycle_suppressed():
        return True
    tool = _tool_name(data)
    if not tool:
        return False
    if tool in _SKIP_TOOLS:
        return True
    ti = _tool_input(data)
    if tool in ("Task", "Agent", "Subagent"):
        # Closing, resuming, or interrupting — not a leak.
        if ti.get("interrupt") is True:
            return True
        if ti.get("resume") or ti.get("close") is True:
            return True
    return False


def lifecycle_reminder_message(
    data: dict[str, Any],
    *,
    state_path: Path | None = None,
) -> str | None:
    """Return a reminder when completed sub-agents may still be open."""
    if should_skip_lifecycle_reminder(data):
        return None
    parts: list[str] = [LIFECYCLE_MSG]
    pending = pending_close_ids(state_path) if state_path else []
    if pending:
        listed = ", ".join(pending[:8])
        suffix = " …" if len(pending) > 8 else ""
        parts.append(f"Pending close (from hook tracker): {listed}{suffix}.")
    running = running_agent_ids(state_path) if state_path else []
    if running:
        listed = ", ".join(running[:8])
        suffix = " …" if len(running) > 8 else ""
        parts.append(f"{PROGRESS_MSG} Running: {listed}{suffix}.")
    return " ".join(parts)


def default_state_path(cwd: Path) -> Path:
    return cwd / ".cursor" / "forge-subagent-lifecycle.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"version": _STATE_VERSION, "running": {}, "pending_close": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": _STATE_VERSION, "running": {}, "pending_close": []}
    if not isinstance(raw, dict):
        return {"version": _STATE_VERSION, "running": {}, "pending_close": []}
    running = raw.get("running")
    pending = raw.get("pending_close")
    return {
        "version": _STATE_VERSION,
        "running": running if isinstance(running, dict) else {},
        "pending_close": pending if isinstance(pending, list) else [],
    }


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def pending_close_ids(state_path: Path | None) -> list[str]:
    if state_path is None or not state_path.is_file():
        return []
    state = _load_state(state_path)
    pending = state.get("pending_close")
    if not isinstance(pending, list):
        return []
    return [str(x) for x in pending if str(x).strip()]


def running_agent_ids(state_path: Path | None) -> list[str]:
    if state_path is None or not state_path.is_file():
        return []
    state = _load_state(state_path)
    running = state.get("running")
    if not isinstance(running, dict):
        return []
    return [str(k) for k in running if str(k).strip()]


def record_subagent_start(data: dict[str, Any], *, state_path: Path) -> None:
    agent_id = extract_agent_id(data)
    if not agent_id:
        return
    state = _load_state(state_path)
    running = state.setdefault("running", {})
    if not isinstance(running, dict):
        running = {}
        state["running"] = running
    running[agent_id] = {"started_at": _utc_now()}
    pending = state.get("pending_close")
    if isinstance(pending, list) and agent_id in pending:
        state["pending_close"] = [x for x in pending if str(x) != agent_id]
    _save_state(state_path, state)


def record_subagent_stop(data: dict[str, Any], *, state_path: Path) -> None:
    agent_id = extract_agent_id(data)
    if not agent_id:
        return
    state = _load_state(state_path)
    running = state.get("running")
    if isinstance(running, dict):
        running.pop(agent_id, None)
    pending = state.get("pending_close")
    if not isinstance(pending, list):
        pending = []
    if agent_id not in pending:
        pending.append(agent_id)
    state["pending_close"] = pending
    _save_state(state_path, state)


def record_task_post_tool(data: dict[str, Any], *, state_path: Path) -> None:
    """After Task tool use, clear pending close when agent was resumed."""
    tool = _tool_name(data)
    if tool not in ("Task", "Agent", "Subagent"):
        return
    agent_id = extract_agent_id(data)
    if not agent_id:
        return
    state = _load_state(state_path)
    pending = state.get("pending_close")
    if not isinstance(pending, list):
        return
    if agent_id not in pending:
        return
    state["pending_close"] = [x for x in pending if str(x) != agent_id]
    _save_state(state_path, state)
