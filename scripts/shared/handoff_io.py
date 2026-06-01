"""Handoff markdown files and per-skill run-memory jsonl under the runtime memory dir."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.shared.runtime_layout import (
    RUN_HISTORY_MAX_ENTRIES,
    legacy_memory_dir,
    runtime_memory_dir,
)
from scripts.shared.skill_state import SkillState
from scripts.shared.state_lifecycle import now_iso


def handoff_paths(name: str, search_dir: Path | None = None) -> tuple[Path, Path]:
    """Return canonical and legacy handoff paths for a skill name."""
    return (
        runtime_memory_dir(search_dir) / f"handoff-{name}.md",
        legacy_memory_dir(search_dir) / f"handoff-{name}.md",
    )


_handoff_paths = handoff_paths


def read_handoff(name: str, search_dir: Path | None = None) -> str:
    """Read a handoff file from the runtime memory directory if it exists."""
    for handoff in handoff_paths(name, search_dir):
        if handoff.exists():
            return handoff.read_text(encoding="utf-8")
    return ""


def close_handoff(name: str, search_dir: Path | None = None) -> bool:
    """Delete canonical + legacy handoff files for a skill."""
    removed = False
    for handoff in handoff_paths(name, search_dir):
        if handoff.exists():
            handoff.unlink()
            removed = True
    return removed


def consume_handoff(name: str, search_dir: Path | None = None) -> str:
    """Read and close a handoff so it does not leak across later sessions."""
    content = read_handoff(name, search_dir=search_dir)
    if content:
        close_handoff(name, search_dir=search_dir)
    return content


def write_handoff(
    skill_name: str,
    state: SkillState,
    context: dict[str, str],
    suggested_next: str,
    memory_dir: Path | None = None,
) -> Path:
    """Write a handoff file to the runtime memory directory."""
    if memory_dir is None:
        memory_dir = runtime_memory_dir()
    memory_dir.mkdir(parents=True, exist_ok=True)

    handoff_path = memory_dir / f"handoff-{skill_name}.md"
    now = datetime.now(timezone.utc).isoformat()

    lines = [
        f"# Handoff: {skill_name} → {suggested_next.split()[0] if suggested_next else 'next'}",
        "",
        "## Completed",
        f"- **Skill:** {skill_name}",
        f"- **Timestamp:** {now}",
        f"- **Status:** complete",
        f"- **Quick mode:** {state.quick_mode}",
        "",
        "## Context for Next Skill",
    ]

    for key, val in context.items():
        lines.append(f"- **{key}:** {val}")

    lines.extend([
        "",
        "## Beads State",
        f"- **Epic:** {state.epic_id or 'N/A'}",
        f"- **Open issues:** {', '.join(k for k, v in state.issue_ids.items()) or 'none'}",
        "",
        "## Suggested Next",
        f"`{suggested_next}`" if suggested_next else "(end of flow)",
        "",
    ])

    handoff_path.write_text("\n".join(lines), encoding="utf-8")
    return handoff_path


def skill_run_memory_path(
    skill_name: str,
    search_dir: Path | None = None,
    memory_dir: Path | None = None,
) -> Path:
    """Path to per-skill run-memory jsonl file."""
    md = memory_dir or runtime_memory_dir(search_dir)
    return md / f"{skill_name}-runs.jsonl"


def append_skill_run_memory(
    skill_name: str,
    step: int,
    phase: str,
    summary: str,
    *,
    state: Any | None = None,
    state_path: Path | None = None,
    handoff_path: Path | None = None,
    max_entries: int = RUN_HISTORY_MAX_ENTRIES,
    search_dir: Path | None = None,
    memory_dir: Path | None = None,
) -> Path:
    """Append an auditable run entry and cap history to the most recent entries."""
    md = memory_dir or runtime_memory_dir(search_dir)
    md.mkdir(parents=True, exist_ok=True)
    history_path = skill_run_memory_path(skill_name, search_dir=search_dir, memory_dir=md)
    timestamp = now_iso()

    state_path_str = str(state_path.resolve()) if isinstance(state_path, Path) else (
        str(Path(state_path).resolve()) if state_path else ""
    )
    handoff_path_str = str(handoff_path.resolve()) if isinstance(handoff_path, Path) else (
        str(Path(handoff_path).resolve()) if handoff_path else ""
    )

    started_at = getattr(state, "started_at", None) if state is not None else None
    session_ref = f"{skill_name}:{state_path_str or '(no-state)'}:{started_at or '(unknown-start)'}"
    handoff_ref = handoff_path_str or "(none)"

    entry: dict[str, Any] = {
        "timestamp": timestamp,
        "skill": skill_name,
        "step": int(step),
        "phase": phase,
        "summary": summary.strip(),
        "session_ref": session_ref,
        "state_path": state_path_str,
        "session_started_at": started_at,
        "handoff_ref": handoff_ref,
        "handoff_path": handoff_path_str,
    }
    if state is not None:
        entry["current_step"] = getattr(state, "current_step", None)
        entry["last_completed_step"] = getattr(state, "last_completed_step", None)
        entry["max_step"] = getattr(state, "max_step", None)
        entry["completed_at"] = getattr(state, "completed_at", None)
        entry["quick_mode"] = bool(getattr(state, "quick_mode", False))

    records: list[dict[str, Any]] = []
    if history_path.exists():
        for line in history_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                records.append(obj)

    records.append(entry)
    keep = max(1, int(max_entries))
    records = records[-keep:]

    history_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=True, separators=(",", ":")) for r in records) + "\n",
        encoding="utf-8",
    )
    return history_path


def build_skill_handoff_menu(
    skill_name: str,
    state: SkillState | None = None,
    state_path: Path | None = None,
) -> str:
    """Build a numbered handoff menu for skill-chain transitions."""
    from scripts.shared.handoff_menu import format_handoff_menu_lines, resolve_handoff_commands
    from scripts.shared.skill_chain import SKILL_CHAIN

    transition = SKILL_CHAIN.get(skill_name)
    if not transition:
        return f"\nWORKFLOW HANDOFF — {skill_name} complete\n\nNo configured next skill."

    default_cmd, alternatives = resolve_handoff_commands(
        skill_name,
        state,
        default_cmd=transition.default,
        alternatives=list(transition.alternatives) or [],
    )
    return "\n".join(
        format_handoff_menu_lines(
            skill_name,
            default_cmd=default_cmd,
            alternatives=alternatives,
            state_path=state_path,
        )
    )
