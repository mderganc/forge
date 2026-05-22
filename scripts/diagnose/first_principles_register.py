"""First-principles sidecar for diagnose."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar

FILENAME = ".diagnose-first-principles.json"


def register_path(state_dir: Path) -> Path:
    return state_dir / FILENAME


def load_register(path: Path) -> dict | None:
    return load_sidecar(path)


def summarize(data: dict | None) -> str:
    if not data:
        return "(No first-principles sidecar loaded)"
    inv = data.get("invariants") or []
    viol = data.get("violations") or []
    return f"**{len(inv)}** invariants, **{len(viol)}** violations documented"


def validate(
    data: dict | None,
    *,
    path: Path | None = None,
    require_violation_link: bool = True,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    label = str(path) if path else FILENAME

    if data is None:
        issues.append(
            f"No first-principles file at {label}. "
            "Create `.diagnose-first-principles.json` in Phase 1–2."
        )
        return False, issues

    invariants = data.get("invariants")
    if not isinstance(invariants, list) or len(invariants) < 1:
        issues.append("At least one system invariant is required in 'invariants'.")

    violations = data.get("violations")
    if not isinstance(violations, list):
        issues.append("'violations' must be an array.")
        return False, issues

    if require_violation_link and len(violations) < 1:
        issues.append(
            "At least one invariant violation must be documented with observation_links."
        )

    for idx, v in enumerate(violations):
        if not isinstance(v, dict):
            issues.append(f"Violation {idx + 1} is not an object.")
            continue
        inv = v.get("invariant")
        obs = v.get("observation_links") or v.get("evidence")
        if not inv or not str(inv).strip():
            issues.append(f"Violation {idx + 1} missing 'invariant'.")
        if require_violation_link:
            if not obs or (isinstance(obs, list) and len(obs) < 1):
                issues.append(
                    f"Violation {idx + 1} missing observation_links (file:line, log, metric)."
                )

    return len(issues) == 0, issues
