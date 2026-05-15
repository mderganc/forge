"""Design spec completion gate for develop step 7 (handoff).

Reads `.develop-spec-gate.json` beside the develop state file when
``spec_required`` is true. Medium/large scope tiers require a committed design
spec and explicit user approval recorded in the sidecar.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SPEC_GATE_FILE = ".develop-spec-gate.json"


def gate_sidecar_path(state_path: Path) -> Path:
    return state_path.parent / SPEC_GATE_FILE


def load_gate_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _repo_root_from_state(state_path: Path) -> Path:
    """Walk up from the state file until a `.git` directory is found."""
    cur = state_path.resolve().parent
    for p in [cur, *cur.parents]:
        if (p / ".git").is_dir():
            return p
    # Fallback: canonical layout `.codex/forge/state/<skill>.json` → repo is 4 levels up
    try:
        return state_path.resolve().parents[3]
    except IndexError:
        return Path.cwd().resolve()


def _resolve_spec_path(repo_root: Path, raw: str) -> Path | None:
    s = (raw or "").strip()
    if not s:
        return None
    p = Path(s).expanduser()
    if p.is_absolute():
        return p if p.is_file() else None
    cand = (repo_root / p).resolve()
    return cand if cand.is_file() else None


def validate_spec_gate(
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

    if allow_incomplete:
        reason = (override_reason or "").strip()
        if not reason:
            return (
                False,
                "Spec gate bypass requires --spec-override-reason (non-empty).",
            )
        follow = (override_follow_up or "").strip()
        if not follow:
            return (
                False,
                "Spec gate bypass requires --spec-override-follow-up (non-empty).",
            )
        return True, f"Spec gate overridden — reason recorded (timestamp={override_timestamp})."

    side = gate_sidecar_path(state_path)
    data = load_gate_json(side)
    if not data:
        return (
            False,
            f"Missing or invalid `{SPEC_GATE_FILE}` next to the develop state file "
            f"({side}). Complete the spec workflow from step 6 before running step 7.",
        )

    repo = _repo_root_from_state(state_path)
    spec_raw = str(data.get("spec_path", "")).strip()
    spec_path = _resolve_spec_path(repo, spec_raw)
    if spec_path is None:
        return (
            False,
            f"Design spec file not found or path invalid: `{spec_raw!r}` "
            f"(resolved from repo root `{repo}`).",
        )

    for key in ("spec_written", "self_review_passed", "user_approved"):
        if not data.get(key):
            return (
                False,
                f"Spec gate: `{key}` must be true in `{SPEC_GATE_FILE}`.",
            )

    return True, ""


def exit_if_gate_fails(ok: bool, msg: str) -> None:
    if ok:
        return
    print(f"ERROR: Develop spec gate failed — {msg}", file=sys.stderr)
    sys.exit(1)


def handoff_spec_summary(gate_data: dict[str, Any] | None) -> dict[str, str]:
    """Flatten spec gate fields for handoff context."""
    if not gate_data:
        return {"Spec path": "(n/a)", "Spec approved": "(n/a)"}
    return {
        "Spec path": str(gate_data.get("spec_path", "")).strip() or "(unknown)",
        "Spec approved": "yes" if gate_data.get("user_approved") else "no",
    }
