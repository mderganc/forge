"""Named workflow phases and step resolution for Forge skills."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from scripts.shared.skill_state import SkillState

# Canonical phase names per skill (and optional variant, e.g. evaluate mode).
# Keys: skill name -> variant (None for default) -> step -> display name
_SKILL_PHASE_NAMES: dict[str, dict[str | None, dict[int, str]]] = {
    "design": {
        None: {
            1: "Startup",
            2: "Scope & Team",
            3: "Investigation Dispatch",
            4: "Investigation Review",
            5: "Solution Dispatch",
            6: "Solution Review & Approval",
            7: "Handoff",
        },
    },
    "plan": {
        None: {
            1: "Context Detection",
            2: "Architecture Dispatch",
            3: "Plan Creation Dispatch",
            4: "Plan Review Loop",
            5: "User Approval",
            6: "Documentation Planning",
            7: "Handoff",
        },
    },
    "implement": {
        None: {
            1: "Plan Detection",
            2: "Branch Setup",
            3: "Wave Dispatch",
            4: "Wave Review",
            5: "Wave Completion",
            6: "Integration Verification",
            7: "Documentation",
            8: "Handoff",
        },
    },
    "code-review": {
        None: {
            1: "Target Detection",
            2: "Mode Selection",
            3: "Team Dispatch",
            4: "Deep Dive",
            5: "Discussion",
            6: "Report",
        },
    },
    "test": {
        "run": {
            1: "Context Detection",
            2: "Test Discovery",
            3: "Test Execution",
            4: "Failure Analysis",
            5: "Coverage Gap Analysis",
            6: "Report",
        },
        "flows": {
            1: "Flow Context Detection",
            2: "Flow-Type Recommendation",
            3: "Scope Definition",
            4: "Scaffolding",
            5: "Mock Authoring",
            6: "Execution + Iteration",
            7: "Report + Handoff",
        },
        "ux": {
            1: "App Understanding",
            2: "Goal-Based Test Plan",
            3: "Browser Journey Execution",
            4: "Edge Cases & Persistence",
            5: "Issue Documentation",
            6: "Report + Handoff",
        },
    },
    "diagnose": {
        None: {
            1: "Frame the Problem",
            2: "Reproduce & Observe",
            3: "Deepen (5 Whys)",
            4: "Analyze & Rank",
            5: "Solution Generation",
            6: "Implement & Validate",
            7: "Report & Prevention",
        },
    },
    "sketch": {
        None: {
            1: "Startup",
            2: "Sketch session",
            3: "Handoff",
        },
    },
    "ux-review": {
        None: {
            1: "Orient",
            2: "Review plan",
            3: "Browser walkthrough",
            4: "States & viewports",
            5: "Findings",
            6: "Report + handoff",
        },
    },
    "iterate": {
        None: {
            1: "Initialize",
            2: "Diagnose",
            3: "Plan",
            4: "Evaluate (pre)",
            5: "Implement",
            6: "Evaluate (post)",
            7: "Code review",
            8: "Test + metric",
            9: "Report",
        },
    },
    "takeover": {
        None: {
            1: "Initialize + route",
            2: "Upstream / continue",
            3: "Plan + evaluate (pre)",
            4: "Implement + evaluate (post)",
            5: "Code review + test",
            6: "Report",
        },
    },
    "ship": {
        None: {
            1: "Graphify preflight (before commit)",
        },
    },
    "evaluate": {
        "pre": {
            1: "Plan Parsing",
            2: "Feasibility",
            3: "Completeness",
            4: "Codebase Alignment",
            5: "Risk & Dependencies",
            6: "Discussion",
            7: "Report",
        },
        "post": {
            1: "Plan Parsing",
            2: "Completeness Audit",
            3: "Correctness",
            4: "Code Quality",
            5: "Performance",
            6: "Operational Readiness",
            7: "Discussion",
            8: "Report",
        },
        "review": {
            1: "Team Dispatch",
            2: "Findings Aggregation",
            3: "Remediation",
            4: "Discussion",
            5: "Report",
        },
    },
}

# CLI / script folder token -> canonical skill name for phase lookup and agent tokens.
_SCRIPT_SKILL_ALIASES: dict[str, str] = {
    "develop": "design",
}


def phase_slug(name: str) -> str:
    """Stable kebab-case slug from a display phase name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
    return slug.strip("-")


def canonical_skill_name(skill_or_token: str) -> str:
    """Map legacy script tokens (develop) to canonical skill names (design)."""
    key = skill_or_token.strip().replace("_", "-")
    return _SCRIPT_SKILL_ALIASES.get(key, key)


def agent_skill_token(skill_name: str) -> str:
    """Hyphenated token for ``$forge:`` / ``/forge:`` continuations."""
    return canonical_skill_name(skill_name).replace("_", "-")


def phase_names_for(skill_name: str, variant: str | None = None) -> dict[int, str]:
    """Return {step: display name} for a skill (and optional variant)."""
    skill = canonical_skill_name(skill_name)
    variants = _SKILL_PHASE_NAMES.get(skill, {})
    if variant is not None and variant in variants:
        return dict(variants[variant])
    if None in variants:
        return dict(variants[None])
    if variants:
        return dict(next(iter(variants.values())))
    return {}


def max_step_for(skill_name: str, variant: str | None = None) -> int:
    names = phase_names_for(skill_name, variant)
    return max(names) if names else 0


def _slug_index(skill_name: str, variant: str | None) -> dict[str, int]:
    names = phase_names_for(skill_name, variant)
    index: dict[str, int] = {}
    for step, display in names.items():
        slug = phase_slug(display)
        if slug in index and index[slug] != step:
            prefixed = f"{variant}-{slug}" if variant else f"step-{step}-{slug}"
            index[prefixed] = step
        index[slug] = step
    if variant:
        for step, display in names.items():
            index[f"{variant}-{phase_slug(display)}"] = step
    return index


def phase_for_step(skill_name: str, step: int, *, variant: str | None = None) -> str:
    """Return the primary slug for a step."""
    skill = canonical_skill_name(skill_name)
    names = phase_names_for(skill, variant)
    display = names.get(step, f"step-{step}")
    slug = phase_slug(display)
    if skill == "evaluate" and variant:
        return f"{variant}-{slug}"
    return slug


def step_for_phase(skill_name: str, phase: str, *, variant: str | None = None) -> int:
    """Resolve a phase slug (or step number as string) to a step index."""
    raw = (phase or "").strip()
    if not raw:
        sys.exit("ERROR: --phase requires a non-empty phase name")
    if raw.isdigit():
        return int(raw)
    skill = canonical_skill_name(skill_name)
    key = raw.lower().replace("_", "-")

    if skill == "evaluate":
        for prefix in ("pre", "post", "review"):
            if key.startswith(f"{prefix}-"):
                return step_for_phase(skill, key[len(prefix) + 1 :], variant=prefix)
        if variant is not None:
            index = _slug_index(skill, variant)
            if key in index:
                return index[key]
            known = ", ".join(sorted(index.keys()))
            sys.exit(
                f"ERROR: unknown phase {phase!r} for evaluate mode {variant!r}. Known: {known}"
            )
        matches: list[tuple[str, int]] = []
        for mode in ("pre", "post", "review"):
            idx = _slug_index(skill, mode)
            if key in idx:
                matches.append((mode, idx[key]))
        if not matches:
            known = ", ".join(
                sorted(
                    f"{m}-{s}"
                    for m in ("pre", "post", "review")
                    for s in _slug_index(skill, m).keys()
                )
            )
            sys.exit(f"ERROR: unknown phase {phase!r} for evaluate. Known: {known}")
        steps = {step for _, step in matches}
        if len(steps) > 1:
            modes = ", ".join(f"{m} (step {s})" for m, s in matches)
            sys.exit(
                f"ERROR: phase {phase!r} is ambiguous for evaluate ({modes}). "
                "Use --mode or a prefixed slug (e.g. post-discussion)."
            )
        return matches[0][1]

    index = _slug_index(skill, variant)
    if key in index:
        return index[key]
    if variant is None:
        for var_key in _SKILL_PHASE_NAMES.get(skill, {}):
            idx = _slug_index(skill, var_key if var_key is not None else None)
            if key in idx:
                return idx[key]
    known = ", ".join(sorted(index.keys()))
    sys.exit(f"ERROR: unknown phase {phase!r} for skill {skill!r}. Known: {known}")


def _session_dict_from_path(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    return SkillState.from_dict(data).to_dict() if hasattr(SkillState, "from_dict") else {}


def infer_resume_step(
    session: dict[str, Any],
) -> int:
    """Mirror ``resume._resume_step`` using a loaded session dict."""
    current = session.get("current_step", 1)
    last_completed = session.get("last_completed_step", 0)
    max_step = session.get("max_step", 6)
    last_completed = min(last_completed, current)
    if current <= 0:
        return 1
    if current >= max_step and last_completed >= max_step:
        return max_step
    if last_completed == current and current < max_step:
        return current + 1
    return max(current, 1)


def _load_session_dict(
    *,
    skill_name: str,
    state_file: str | None,
    session_id: str | None,
    search_dir: Path | None = None,
) -> dict[str, Any] | None:
    from scripts.shared.session_store import session_json_path
    from scripts.shared.orchestrator import _detect_repo_root, validate_state_path

    repo_root = _detect_repo_root(search_dir).resolve()
    if session_id:
        path = session_json_path(session_id, repo_root)
        if not path.is_file():
            return None
        return _session_dict_from_path(path)
    if state_file:
        sp = validate_state_path(state_file, canonical_skill_name(skill_name))
        if sp is None or not sp.is_file():
            sp = Path(state_file)
            if not sp.is_file():
                return None
        return _session_dict_from_path(sp)
    return None


def variant_from_session(session: dict[str, Any], skill_name: str) -> str | None:
    """Infer phase variant (test mode, evaluate mode) from persisted state."""
    skill = canonical_skill_name(skill_name)
    if skill == "test":
        custom = session.get("custom") or {}
        mode = custom.get("mode", "run")
        return str(mode) if mode in ("run", "flows", "ux") else "run"
    if skill == "evaluate":
        mode = session.get("mode")
        return str(mode) if mode in ("pre", "post", "review") else "pre"
    return None


def resolve_workflow_step(
    *,
    skill_name: str,
    max_step: int,
    step: int | None,
    phase: str | None,
    state_file: str | None = None,
    session_id: str | None = None,
    variant: str | None = None,
    search_dir: Path | None = None,
) -> int:
    """Resolve CLI ``--step`` / ``--phase`` / session inference to a step number."""
    skill = canonical_skill_name(skill_name)

    if step is not None and phase is not None:
        resolved = step_for_phase(skill, phase, variant=variant)
        if resolved != step:
            sys.exit(
                f"ERROR: --step {step} conflicts with --phase {phase!r} (resolves to step {resolved})"
            )
        return step

    if phase is not None:
        return step_for_phase(skill, phase, variant=variant)

    if step is not None:
        return step

    session = _load_session_dict(
        skill_name=skill,
        state_file=state_file,
        session_id=session_id,
        search_dir=search_dir,
    )
    if session is not None:
        var = variant or variant_from_session(session, skill)
        _ = var  # variant used when re-resolving phase-only invocations later
        return infer_resume_step(session)

    # New workflow: default to step 1.
    return 1


def format_phase_list(skill_name: str, variant: str | None = None) -> str:
    """Comma-separated phase slugs for argparse help text."""
    names = phase_names_for(skill_name, variant)
    return ", ".join(phase_slug(v) for v in names.values())
