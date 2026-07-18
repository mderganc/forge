"""Gate: structural probes — user pause, code-review tool completeness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.code_review.structural_probes_gate_helpers import (
    missing_required_probes,
    probe_by_tool,
    stack_flags,
)
from scripts.shared.structural_probes import (
    SIDECAR_NAME,
    skip_structural_probes,
)
from scripts.shared.structural_probes_gate import (
    load_probe_gate_sidecar,
    probe_gate_is_pending,
    validate_probe_gate_at_step_entry,
)
from scripts.shared.workflow_gate import (
    exit_if_gate_fails,
    validate_override_bypass,
)

REQUIRED_PYTHON_TOOLS = ("pyscn",)
REQUIRED_NODE_TOOLS = ("knip", "jscn")


def sidecar_path(state_dir: Path) -> Path:
    return Path(state_dir) / SIDECAR_NAME


def load_probe_payload(state_dir: Path) -> dict[str, Any] | None:
    path = sidecar_path(state_dir)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _probe_by_tool(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return probe_by_tool(payload)


def _stack_flags(payload: dict[str, Any], repo_root: Path) -> tuple[bool, bool]:
    return stack_flags(payload, repo_root)


def _tool_ran(probe: dict[str, Any] | None) -> bool:
    from scripts.code_review.structural_probes_gate_helpers import tool_ran

    return tool_ran(probe)


def _gate_missing_sidecar(path: Path) -> tuple[bool, str]:
    return (
        False,
        "STRUCTURAL PROBES GATE: missing `.structural-probes.json`.\n"
        f"Run `forge code-review --step 3` first (expected sidecar: `{path}`).",
    )


def _gate_pending_status(top_status: str) -> tuple[bool, str]:
    return (
        False,
        f"STRUCTURAL PROBES GATE: probe status is {top_status} — "
        "clear the gate (retry, override, or defer to ship) before continuing.",
    )


def validate_structural_probes_gate(
    state_dir: Path,
    repo_root: Path,
    *,
    allow_incomplete: bool = False,
    override_reason: str = "",
    override_follow_up: str = "",
    override_timestamp: str = "",
) -> tuple[bool, str]:
    """Return (ok, message). Steps 4+ require step-3 probe sidecar with pyscn/knip executed."""
    ok_gate, gate_msg = validate_probe_gate_at_step_entry(
        state_dir,
        allow_incomplete=allow_incomplete,
        override_reason=override_reason,
        override_follow_up=override_follow_up,
    )
    if not ok_gate:
        return False, gate_msg

    if skip_structural_probes():
        return True, "Structural probes suppressed (`FORGE_SKIP_STRUCTURAL_TOOLS=1`)."

    ok_override, override_msg = validate_override_bypass(
        allow_incomplete,
        override_reason,
        override_follow_up,
        reason_field_label="--structural-probes-override-reason",
        follow_up_field_label="--structural-probes-override-follow-up",
        success_message="Structural probes gate OVERRIDDEN.",
        override_timestamp=override_timestamp,
    )
    if allow_incomplete:
        return ok_override, override_msg

    path = sidecar_path(state_dir)
    payload = load_probe_payload(state_dir)
    if payload is None:
        return _gate_missing_sidecar(path)

    top_status = str(payload.get("status") or "").upper()
    if top_status and top_status != "OK":
        gate = load_probe_gate_sidecar(state_dir)
        if probe_gate_is_pending(state_dir) or (gate and gate.get("gate_state") == "pending"):
            return _gate_pending_status(top_status)

    python_capable, node_capable = _stack_flags(payload, repo_root)
    missing = missing_required_probes(
        _probe_by_tool(payload),
        python_capable=python_capable,
        node_capable=node_capable,
        python_tools=REQUIRED_PYTHON_TOOLS,
        node_tools=REQUIRED_NODE_TOOLS,
    )

    if missing:
        return (
            False,
            "STRUCTURAL PROBES GATE: required probes did not run:\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n\nRe-run `forge code-review --step 3` after `forge structural-tools install`, "
            "or bypass with `--allow-structural-probes-incomplete` and override reason/follow-up.",
        )

    return True, "Structural probes gate passed (pyscn/jscn/knip executed per stack)."


def exit_if_structural_probes_gate_fails(
    state_dir: Path,
    repo_root: Path,
    *,
    allow_incomplete: bool = False,
    override_reason: str = "",
    override_follow_up: str = "",
) -> None:
    ok, msg = validate_structural_probes_gate(
        state_dir,
        repo_root,
        allow_incomplete=allow_incomplete,
        override_reason=override_reason,
        override_follow_up=override_follow_up,
    )
    exit_if_gate_fails(ok, msg, error_prefix="", echo_msg_on_success=False)
