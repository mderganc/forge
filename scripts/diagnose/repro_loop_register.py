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
    issues: list[str] = []
    label = str(path) if path else FILENAME

    if data is None:
        issues.append(
            f"No feedback-loop sidecar at {label}. "
            "Create `.diagnose-feedback-loop.json` in Phase 2 (Reproduce & Observe)."
        )
        return False, issues

    version = data.get("version")
    if version is not None and version != 1:
        issues.append("'version' must be 1 when present.")

    loop_type = data.get("loop_type")
    if not loop_type or str(loop_type).strip() not in LOOP_TYPES:
        issues.append(
            "'loop_type' required — one of: " + ", ".join(sorted(LOOP_TYPES)) + "."
        )

    cannot = bool(data.get("cannot_build_loop"))
    if cannot:
        if str(loop_type).strip() != "none":
            issues.append("When 'cannot_build_loop' is true, 'loop_type' must be 'none'.")
        blocked = data.get("blocked_reason")
        if not blocked or not str(blocked).strip():
            issues.append("'cannot_build_loop' requires non-empty 'blocked_reason'.")
        user_ask = data.get("user_ask")
        if not user_ask or not str(user_ask).strip():
            issues.append("'cannot_build_loop' requires non-empty 'user_ask' for the user.")
        return len(issues) == 0, issues

    if loop_type == "none":
        issues.append(
            "'loop_type' 'none' is only valid when 'cannot_build_loop' is true."
        )

    cmd = data.get("command_or_path")
    if not cmd or not str(cmd).strip():
        issues.append(
            "Non-blocked loop requires non-empty 'command_or_path' "
            "(test command, script path, or harness entry)."
        )

    runs = data.get("runs_observed")
    if not isinstance(runs, int) or runs < 1:
        issues.append("'runs_observed' must be an integer >= 1 after running the loop.")

    symptom = data.get("symptom_captured")
    if not symptom or not str(symptom).strip():
        issues.append(
            "'symptom_captured' required — verbatim error, wrong output, or metric."
        )

    if data.get("matches_user_report") is not True:
        issues.append(
            "'matches_user_report' must be true — the loop must reproduce the user's "
            "failure mode, not a nearby failure."
        )

    steps = data.get("minimal_repro_steps")
    if not isinstance(steps, list) or len(steps) < 1:
        issues.append(
            "'minimal_repro_steps' must be a non-empty array of human-readable steps."
        )
    else:
        for i, step in enumerate(steps):
            if not step or not str(step).strip():
                issues.append(f"minimal_repro_steps[{i}] must be non-empty.")

    if strict:
        det = data.get("deterministic")
        if det is not True and det is not False:
            issues.append("'deterministic' must be true or false.")

    return len(issues) == 0, issues


def requires_override_to_proceed(data: dict | None) -> bool:
    """True when the sidecar documents inability to build a loop (gate needs override)."""
    return bool(data and data.get("cannot_build_loop"))
