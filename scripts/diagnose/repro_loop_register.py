"""Feedback-loop / reproduction sidecar (Phase 2 — Reproduce & Observe)."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar

FILENAME = ".diagnose-feedback-loop.json"

LOOP_TYPES = frozenset({
    "failing_test",
    "http_script",
    "cli",
    "browser",
    "replay",
    "harness",
    "fuzz",
    "bisect",
    "diff",
    "hitl",
    "none",
})


def register_path(state_dir: Path) -> Path:
    return state_dir / FILENAME


def load_register(path: Path) -> dict | None:
    return load_sidecar(path)


def summarize(data: dict | None) -> str:
    if not data:
        return "(No feedback-loop sidecar loaded)"
    if data.get("cannot_build_loop"):
        reason = data.get("blocked_reason") or "?"
        return f"**Cannot build loop** — {reason}"
    loop_type = data.get("loop_type") or "?"
    det = data.get("deterministic")
    runs = data.get("runs_observed", "?")
    match = data.get("matches_user_report")
    return (
        f"Loop: **{loop_type}**; deterministic: **{det}**; "
        f"runs: **{runs}**; matches user report: **{match}**"
    )


def validate(
    data: dict | None,
    *,
    path: Path | None = None,
    strict: bool = True,
) -> tuple[bool, list[str]]:
    from scripts.diagnose.register_validation import (
        finish_validation,
        missing_sidecar_issue,
        require_bool_field,
        require_enum,
        require_list_min,
        require_non_empty_str,
        require_version,
    )

    issues: list[str] = []
    label = str(path) if path else FILENAME

    if data is None:
        return missing_sidecar_issue(
            label,
            "Create `.diagnose-feedback-loop.json` in Phase 2 (Reproduce & Observe).",
        )

    require_version(data, issues)
    loop_type = require_enum(
        data,
        "loop_type",
        LOOP_TYPES,
        issues,
    )

    if bool(data.get("cannot_build_loop")):
        _validate_cannot_build_loop(data, issues, loop_type)
        return finish_validation(issues)

    if loop_type == "none":
        issues.append(
            "'loop_type' 'none' is only valid when 'cannot_build_loop' is true."
        )

    require_non_empty_str(
        data,
        "command_or_path",
        issues,
        message=(
            "Non-blocked loop requires non-empty 'command_or_path' "
            "(test command, script path, or harness entry)."
        ),
    )
    runs = data.get("runs_observed")
    if not isinstance(runs, int) or runs < 1:
        issues.append("'runs_observed' must be an integer >= 1 after running the loop.")
    require_non_empty_str(
        data,
        "symptom_captured",
        issues,
        message="'symptom_captured' required — verbatim error, wrong output, or metric.",
    )
    if data.get("matches_user_report") is not True:
        issues.append(
            "'matches_user_report' must be true — the loop must reproduce the user's "
            "failure mode, not a nearby failure."
        )
    require_list_min(
        data,
        "minimal_repro_steps",
        1,
        issues,
        item_check=lambda step, i: (
            None
            if step and str(step).strip()
            else f"minimal_repro_steps[{i}] must be non-empty."
        ),
    )
    if strict:
        require_bool_field(data, "deterministic", issues)

    return finish_validation(issues)


def _validate_cannot_build_loop(
    data: dict,
    issues: list[str],
    loop_type: str | None,
) -> None:
    from scripts.diagnose.register_validation import require_non_empty_str

    if loop_type != "none":
        issues.append("When 'cannot_build_loop' is true, 'loop_type' must be 'none'.")
    require_non_empty_str(
        data,
        "blocked_reason",
        issues,
        message="'cannot_build_loop' requires non-empty 'blocked_reason'.",
    )
    require_non_empty_str(
        data,
        "user_ask",
        issues,
        message="'cannot_build_loop' requires non-empty 'user_ask' for the user.",
    )


def requires_override_to_proceed(data: dict | None) -> bool:
    """True when the sidecar documents inability to build a loop (gate needs override)."""
    return bool(data and data.get("cannot_build_loop"))
