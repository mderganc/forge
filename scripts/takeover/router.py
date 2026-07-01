"""Route planning for forge takeover."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.shared.orchestrator import (
    KNOWN_SKILLS,
    legacy_memory_dir,
    runtime_memory_dir,
)
from scripts.shared.session_hygiene import detect_active_sessions


@dataclass
class RoutePlan:
    entry_skill: str
    entry_reason: str
    upstream_skills: list[str] = field(default_factory=list)
    active_session_id: str | None = None
    active_session_path: str | None = None
    design_path: str | None = None
    issue_ref: str | None = None
    goal: str = "ship-ready"


def _check_handoffs() -> list[str]:
    memory_dirs = [runtime_memory_dir(), legacy_memory_dir()]
    completed: list[str] = []
    for skill in KNOWN_SKILLS:
        for memory_dir in memory_dirs:
            handoff = memory_dir / f"handoff-{skill}.md"
            if handoff.exists():
                completed.append(skill)
                break
    return completed


def _pipeline_successor(completed: set[str]) -> str | None:
    from scripts.shared.orchestrator import PIPELINE_SKILL_ORDER

    pipeline = list(PIPELINE_SKILL_ORDER)
    for i, skill in enumerate(pipeline):
        if i == 0:
            continue
        predecessor = pipeline[i - 1]
        if predecessor in completed and skill not in completed:
            return skill
    return None


def _latest_design_spec(repo_root: Path) -> Path | None:
    specs = repo_root / "docs" / "forge" / "specs"
    if not specs.is_dir():
        return None
    candidates = sorted(specs.glob("*-design.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _issue_looks_like_bug(issue_ref: str) -> bool:
    text = issue_ref.lower()
    return bool(re.search(r"\b(bug|fix|broken|error|regression|fail)\b", text))


def build_route_plan(
    *,
    repo_root: Path,
    issue: str | None = None,
    design: str | None = None,
    goal: str | None = None,
) -> tuple[RoutePlan, list[dict[str, str]]]:
    """Return route plan and inference log entries."""
    inferences: list[dict[str, str]] = []
    resolved_goal = (goal or "").strip() or "ship-ready"

    if design:
        dp = Path(design)
        if not dp.is_file():
            dp = repo_root / design
        reason = f"--design {design}"
        inferences.append({"field": "design", "chosen": str(dp), "reason": reason})
        return (
            RoutePlan(
                entry_skill="plan",
                entry_reason=reason,
                design_path=str(dp),
                goal=resolved_goal,
            ),
            inferences,
        )

    if issue:
        reason = f"--issue {issue}"
        inferences.append({"field": "issue", "chosen": issue, "reason": reason})
        upstream = ["diagnose"] if _issue_looks_like_bug(issue) else []
        return (
            RoutePlan(
                entry_skill="plan" if not upstream else "diagnose",
                entry_reason=reason,
                upstream_skills=upstream,
                issue_ref=issue,
                goal=resolved_goal,
            ),
            inferences,
        )

    sessions = detect_active_sessions(repo_root)
    if len(sessions) == 1:
        s = sessions[0]
        inferences.append(
            {
                "field": "active_session",
                "chosen": s.get("session_id") or s["path"],
                "reason": "single active session",
            }
        )
        return (
            RoutePlan(
                entry_skill=s["skill"],
                entry_reason="single active session",
                active_session_id=s.get("session_id"),
                active_session_path=str(s["path"]),
                goal=resolved_goal,
            ),
            inferences,
        )

    if len(sessions) > 1:
        s = sorted(sessions, key=lambda x: x.get("started_at", ""), reverse=True)[0]
        inferences.append(
            {
                "field": "active_session",
                "chosen": s.get("session_id") or s["path"],
                "reason": "newest of multiple active sessions (best-effort)",
            }
        )
        return (
            RoutePlan(
                entry_skill=s["skill"],
                entry_reason="newest active session among many",
                active_session_id=s.get("session_id"),
                active_session_path=str(s["path"]),
                goal=resolved_goal,
            ),
            inferences,
        )

    completed = set(_check_handoffs())
    successor = _pipeline_successor(completed)
    if successor:
        inferences.append(
            {"field": "pipeline_successor", "chosen": successor, "reason": "handoff chain"}
        )
        return (
            RoutePlan(entry_skill=successor, entry_reason="pipeline handoff successor", goal=resolved_goal),
            inferences,
        )

    spec = _latest_design_spec(repo_root)
    if spec:
        inferences.append(
            {"field": "design_spec", "chosen": str(spec), "reason": "latest docs/forge/specs design"}
        )
        return (
            RoutePlan(
                entry_skill="plan",
                entry_reason="latest design spec",
                design_path=str(spec),
                goal=resolved_goal,
            ),
            inferences,
        )

    inferences.append(
        {"field": "entry", "chosen": "sketch", "reason": "no session, handoff, or spec — upstream intent"}
    )
    return (
        RoutePlan(
            entry_skill="sketch",
            entry_reason="no inferrable epic",
            upstream_skills=["sketch", "design"],
            goal=resolved_goal,
        ),
        inferences,
    )
