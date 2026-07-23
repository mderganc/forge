"""Design spec → issues gate for develop step 8 (handoff).

Reads `.design-spec-issues.json` beside the design state file when
``spec_required`` is true. Medium/large scope tiers require the approved
design spec decomposed into plan-ready issues (beads when available).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.develop import spec_gate
from scripts.shared.workflow_gate import (
    exit_if_gate_fails as _exit_if_gate_fails,
    gate_sidecar_path as _gate_sidecar_path,
    load_gate_json,
    validate_override_bypass,
)

SPEC_ISSUES_FILE = ".design-spec-issues.json"

__all__ = [
    "SPEC_ISSUES_FILE",
    "gate_sidecar_path",
    "load_gate_json",
    "validate_spec_issues_gate",
    "exit_if_gate_fails",
    "handoff_issues_summary",
    "issues_status_block",
]


def gate_sidecar_path(state_path: Path) -> Path:
    return _gate_sidecar_path(state_path, SPEC_ISSUES_FILE)


def _validate_issues_list(issues: Any) -> list[str]:
    problems: list[str] = []
    if not isinstance(issues, list):
        return ["`issues` must be a non-empty array."]
    if not issues:
        return ["`issues` must contain at least one entry."]

    for idx, item in enumerate(issues, start=1):
        if not isinstance(item, dict):
            problems.append(f"Issue {idx}: must be an object.")
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            problems.append(f"Issue {idx}: missing non-empty `title`.")
        summary = str(item.get("summary", "")).strip()
        if not summary:
            problems.append(f"Issue {idx}: missing non-empty `summary`.")
        sections = item.get("spec_sections")
        if not isinstance(sections, list) or not sections:
            problems.append(f"Issue {idx}: `spec_sections` must be a non-empty array.")
        criteria = item.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria:
            problems.append(
                f"Issue {idx}: `acceptance_criteria` must be a non-empty array."
            )
    return problems


def validate_spec_issues_gate(
    state_path: Path,
    spec_required: bool,
    *,
    allow_incomplete: bool = False,
    override_reason: str = "",
    override_requested_by: str = "",
    override_follow_up: str = "",
    override_timestamp: str = "",
) -> tuple[bool, str]:
    """Return (ok, message). When ``spec_required`` is false, always ok."""
    if not spec_required:
        return True, ""

    ok, msg = validate_override_bypass(
        allow_incomplete,
        override_reason,
        override_follow_up,
        reason_field_label="--issues-override-reason (non-empty)",
        follow_up_field_label="--issues-override-follow-up (non-empty)",
        success_message=(
            f"Spec issues gate overridden — reason recorded "
            f"(timestamp={override_timestamp})."
        ),
        override_timestamp=override_timestamp,
    )
    if allow_incomplete:
        return ok, msg

    side = gate_sidecar_path(state_path)
    data = load_gate_json(side)
    if not data:
        return (
            False,
            f"Missing or invalid `{SPEC_ISSUES_FILE}` next to the design state file "
            f"({side}). Complete spec → issues decomposition on step 7 before step 8.",
        )

    spec_gate_data = load_gate_json(spec_gate.gate_sidecar_path(state_path))
    expected_spec = ""
    if spec_gate_data:
        expected_spec = str(spec_gate_data.get("spec_path", "")).strip()

    spec_raw = str(data.get("spec_path", "")).strip()
    if not spec_raw:
        return False, f"Spec issues gate: `spec_path` must be set in `{SPEC_ISSUES_FILE}`."
    if expected_spec and spec_raw != expected_spec:
        return (
            False,
            f"Spec issues gate: `spec_path` ({spec_raw!r}) must match "
            f"`.design-spec-gate.json` ({expected_spec!r}).",
        )

    for key in ("issues_written", "user_confirmed"):
        if not data.get(key):
            return (
                False,
                f"Spec issues gate: `{key}` must be true in `{SPEC_ISSUES_FILE}`.",
            )

    mode = str(data.get("beads_mode", "")).strip().lower()
    if mode not in ("active", "degraded", "none"):
        return (
            False,
            f"Spec issues gate: `beads_mode` must be one of active|degraded|none "
            f"in `{SPEC_ISSUES_FILE}`.",
        )

    issue_problems = _validate_issues_list(data.get("issues"))
    if issue_problems:
        return False, "Spec issues gate:\n- " + "\n- ".join(issue_problems)

    return True, ""


def exit_if_gate_fails(ok: bool, msg: str) -> None:
    _exit_if_gate_fails(ok, msg, error_label="Design spec issues gate failed — ")


def handoff_issues_summary(gate_data: dict[str, Any] | None) -> dict[str, str]:
    """Flatten spec issues fields for handoff context."""
    if not gate_data:
        return {
            "Issues sidecar": "(n/a)",
            "Issue count": "(n/a)",
            "Beads mode": "(n/a)",
            "Epic": "(n/a)",
        }
    issues = gate_data.get("issues") or []
    count = len(issues) if isinstance(issues, list) else 0
    return {
        "Issues sidecar": SPEC_ISSUES_FILE,
        "Issue count": str(count),
        "Beads mode": str(gate_data.get("beads_mode", "")).strip() or "(unknown)",
        "Epic": str(gate_data.get("epic_id", "")).strip() or "none",
    }


def issues_status_block(state_path: Path) -> str:
    """Human-readable spec issues gate status for templates."""
    side = gate_sidecar_path(state_path)
    data = load_gate_json(side)
    if not data:
        return (
            f"**Spec issues gate:** required — sidecar missing or invalid "
            f"(`{side.name}`).\n"
        )
    issues = data.get("issues") or []
    count = len(issues) if isinstance(issues, list) else 0
    parts = [
        "**Spec issues gate:** required",
        f"- `spec_path`: {data.get('spec_path', '')}",
        f"- `issues_written`: {data.get('issues_written', False)}",
        f"- `user_confirmed`: {data.get('user_confirmed', False)}",
        f"- `beads_mode`: {data.get('beads_mode', '')}",
        f"- `issue_count`: {count}",
        f"- `epic_id`: {data.get('epic_id', 'none')}",
    ]
    return "\n".join(parts) + "\n"
