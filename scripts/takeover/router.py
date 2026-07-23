"""Route planning for forge takeover."""

from __future__ import annotations

import json
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
    scope_tier: str = "medium"  # small | medium | large
    skip_evaluate: bool = False
    code_review_effort: str = "standard"
    short_circuit_to_test: bool = False


def normalize_scope_tier(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if text in ("trivial", "small", "simple", "lite", "light"):
        return "small"
    if text in ("large", "thorough"):
        return "large"
    return "medium"


def _infer_scope_from_memory() -> tuple[str, bool]:
    """Return (scope_tier, short_circuit_simple_fix) from design-scope / diagnose handoff."""
    short_circuit = False
    tier: str | None = None
    for memory_dir in (runtime_memory_dir(), legacy_memory_dir()):
        handoff = memory_dir / "handoff-diagnose.md"
        if handoff.is_file():
            text = handoff.read_text(encoding="utf-8").lower()
            if re.search(
                r"fix\s*complexity\**\s*[:=]\**\s*simple",
                text,
            ) or "fix_complexity: simple" in text:
                short_circuit = True
                tier = "small"
            elif re.search(
                r"fix\s*complexity\**\s*[:=]\**\s*large",
                text,
            ):
                tier = tier or "large"
        for name in ("design-scope.json", "develop-scope.json"):
            path = memory_dir / name
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
            if data.get("scope_tier"):
                mapped = normalize_scope_tier(str(data.get("scope_tier") or ""))
                # Diagnose simple wins over a larger design-scope when short-circuiting
                if short_circuit:
                    tier = "small"
                else:
                    tier = mapped
    if short_circuit:
        return "small", True
    return tier or "medium", False


def _decorate_plan(plan: RoutePlan) -> RoutePlan:
    tier, short = _infer_scope_from_memory()
    # CLI/issue bug path may still be medium unless memory says small
    if plan.scope_tier == "medium":
        plan.scope_tier = tier
    # Diagnose simple + fix handoff → short-circuit toward test/ship regardless of entry
    plan.short_circuit_to_test = bool(short)
    if plan.scope_tier == "small":
        plan.skip_evaluate = True
        plan.code_review_effort = "light"
    elif plan.scope_tier == "large":
        plan.code_review_effort = "thorough"
    else:
        plan.code_review_effort = "standard"
    return plan


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
            _decorate_plan(
                RoutePlan(
                    entry_skill="plan",
                    entry_reason=reason,
                    design_path=str(dp),
                    goal=resolved_goal,
                )
            ),
            inferences,
        )

    if issue:
        reason = f"--issue {issue}"
        inferences.append({"field": "issue", "chosen": issue, "reason": reason})
        upstream = ["diagnose"] if _issue_looks_like_bug(issue) else []
        return (
            _decorate_plan(
                RoutePlan(
                    entry_skill="plan" if not upstream else "diagnose",
                    entry_reason=reason,
                    upstream_skills=upstream,
                    issue_ref=issue,
                    goal=resolved_goal,
                )
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
            _decorate_plan(
                RoutePlan(
                    entry_skill=s["skill"],
                    entry_reason="single active session",
                    active_session_id=s.get("session_id"),
                    active_session_path=str(s["path"]),
                    goal=resolved_goal,
                )
            ),
            inferences,
        )

    if len(sessions) > 1:
        s = sorted(
            sessions,
            key=lambda x: x.get("started_at") or "",
            reverse=True,
        )[0]
        inferences.append(
            {
                "field": "active_session",
                "chosen": s.get("session_id") or s["path"],
                "reason": "newest of multiple active sessions (best-effort)",
            }
        )
        return (
            _decorate_plan(
                RoutePlan(
                    entry_skill=s["skill"],
                    entry_reason="newest active session among many",
                    active_session_id=s.get("session_id"),
                    active_session_path=str(s["path"]),
                    goal=resolved_goal,
                )
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
            _decorate_plan(
                RoutePlan(entry_skill=successor, entry_reason="pipeline handoff successor", goal=resolved_goal)
            ),
            inferences,
        )

    spec = _latest_design_spec(repo_root)
    if spec:
        inferences.append(
            {"field": "design_spec", "chosen": str(spec), "reason": "latest docs/forge/specs design"}
        )
        return (
            _decorate_plan(
                RoutePlan(
                    entry_skill="plan",
                    entry_reason="latest design spec",
                    design_path=str(spec),
                    goal=resolved_goal,
                )
            ),
            inferences,
        )

    inferences.append(
        {"field": "entry", "chosen": "sketch", "reason": "no session, handoff, or spec — upstream intent"}
    )
    return (
        _decorate_plan(
            RoutePlan(
                entry_skill="sketch",
                entry_reason="no inferrable epic",
                upstream_skills=["sketch", "design"],
                goal=resolved_goal,
            )
        ),
        inferences,
    )
