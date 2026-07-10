"""Shared helpers for diagnose JSON sidecars and combined orchestrator gates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DiagnoseGateResult:
    """Outcome of one or more diagnose artifact gate checks."""

    passed: bool
    gate_body: str = ""
    next_step_override: int | None = None
    require_confirmation: bool = False
    failed_sections: list[str] = field(default_factory=list)


@dataclass
class GateSection:
    """One validator block inside a combined gate."""

    title: str
    issues: list[str]
    override_key: str | None = None
    bypassed: bool = False


def load_sidecar(path: Path) -> dict | None:
    """Load JSON sidecar. Returns None if missing or unparseable."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def state_dir_from_state_path(state_path: Path) -> Path:
    """Directory for diagnose sidecars (prefer ``sidecars/`` when present)."""
    parent = state_path.parent
    sidecars = parent / "sidecars"
    if sidecars.is_dir():
        return sidecars
    return parent


def resolve_sidecar_path(state_path: Path, filename: str) -> Path:
    """Path for a diagnose sidecar: prefer sidecars/, fall back to session root."""
    parent = state_path.parent
    sidecars = parent / "sidecars"
    preferred = sidecars / filename
    legacy = parent / filename
    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    if sidecars.is_dir():
        return preferred
    return legacy


def has_override(state_custom: dict, key: str) -> bool:
    reason = state_custom.get(key)
    return bool(reason and str(reason).strip())


def format_combined_gate(
    sections: list[GateSection],
    *,
    phase: str,
    retry_step: int | None = None,
    attempt: int = 0,
    max_attempts: int = 1,
    state_path: str | None = None,
    non_overridable_issues: list[str] | None = None,
) -> str:
    """Single markdown gate block aggregating multiple artifact failures."""
    bar = "━" * 60
    active = [s for s in sections if s.issues and not s.bypassed]
    lines = [
        "",
        bar,
        "DIAGNOSE ARTIFACT GATE",
        bar,
        "",
        f"**Phase:** {phase}",
        "",
    ]
    if not active and not non_overridable_issues:
        return ""

    if non_overridable_issues:
        lines.append("**Cannot override (policy / high-severity):**")
        lines.append("")
        for issue in non_overridable_issues:
            lines.append(f"- {issue}")
        lines.append("")

    for section in active:
        lines.append(f"### {section.title}")
        lines.append("")
        for issue in section.issues:
            lines.append(f"- {issue}")
        lines.append("")
        if section.override_key:
            lines.append(
                f"_Override for this section only: set `{section.override_key}` "
                "in session state with a documented reason._"
            )
            lines.append("")

    if retry_step is not None and attempt < max_attempts:
        lines.append(
            f"**Automatic retry ({attempt + 1} of {max_attempts}):** "
            f"Return to **step {retry_step}** and fix the artifacts above, then re-run this step."
        )
        lines.append("")
    elif attempt >= max_attempts:
        lines.append(
            "Retry budget exhausted. Fix the artifacts, or set the per-section override keys "
            "listed above (not permitted for policy-blocked items)."
        )
        lines.append("")

    lines.append(
        "**Pause here.** Present the issues to the user and **wait for approval** before proceeding."
    )
    lines.append("")
    lines.append(
        "Reply **yes** when ready, or document an override reason in session state for the "
        "section(s) you are intentionally proceeding under."
    )
    if state_path:
        lines.extend(["", f"Resume context: `{state_path}`"])
    return "\n".join(lines)


def merge_gate_results(
    sections: list[GateSection],
    *,
    phase: str,
    retry_step: int | None,
    attempt: int,
    max_attempts: int,
    state_path: str,
    non_overridable: list[str] | None = None,
) -> DiagnoseGateResult:
    """Build DiagnoseGateResult from gate sections."""
    blocked = [s for s in sections if s.issues and not s.bypassed]
    policy_block = bool(non_overridable)
    if not blocked and not policy_block:
        return DiagnoseGateResult(passed=True)

    body = format_combined_gate(
        sections,
        phase=phase,
        retry_step=retry_step if (blocked or policy_block) else None,
        attempt=attempt,
        max_attempts=max_attempts,
        state_path=state_path,
        non_overridable_issues=non_overridable,
    )
    return DiagnoseGateResult(
        passed=False,
        gate_body=body,
        next_step_override=retry_step,
        require_confirmation=True,
        failed_sections=[s.title for s in blocked],
    )
