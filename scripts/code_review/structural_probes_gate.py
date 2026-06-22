"""Gate: code-review steps 4+ require structural probes (pyscn/knip) from step 3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.shared.structural_probes import (
    SIDECAR_NAME,
    build_stack_inventory,
    inventory_stack_capabilities,
    skip_structural_probes,
)
from scripts.shared.workflow_gate import (
    exit_if_gate_fails,
    validate_override_bypass,
)

REQUIRED_PYTHON_TOOLS = ("pyscn",)
REQUIRED_NODE_TOOLS = ("knip",)


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
    out: dict[str, dict[str, Any]] = {}
    for row in payload.get("probes") or []:
        if isinstance(row, dict) and row.get("tool"):
            out[str(row["tool"])] = row
    return out


def _stack_flags(payload: dict[str, Any], repo_root: Path) -> tuple[bool, bool]:
    plan = payload.get("plan") or {}
    applicable = plan.get("stack_applicable")
    if isinstance(applicable, dict):
        return bool(applicable.get("python")), bool(applicable.get("node"))

    stack = payload.get("stack") or {}
    python_capable = bool(stack.get("python"))
    node_capable = bool(stack.get("node"))
    if python_capable or node_capable:
        return python_capable, node_capable

    inventory = build_stack_inventory(repo_root)
    return inventory_stack_capabilities(inventory)


def _tool_ran(probe: dict[str, Any] | None) -> bool:
    if not probe:
        return False
    return probe.get("status") in ("pass", "fail")


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
        return (
            False,
            "STRUCTURAL PROBES GATE: missing `.structural-probes.json`.\n"
            f"Run `forge code-review --step 3` first (expected sidecar: `{path}`).",
        )

    python_capable, node_capable = _stack_flags(payload, repo_root)
    by_tool = _probe_by_tool(payload)

    missing: list[str] = []
    if python_capable:
        for tool in REQUIRED_PYTHON_TOOLS:
            probe = by_tool.get(tool)
            if not _tool_ran(probe):
                reason = (probe or {}).get("summary", "probe not present")
                missing.append(f"{tool} ({reason})")
    if node_capable:
        for tool in REQUIRED_NODE_TOOLS:
            probe = by_tool.get(tool)
            if not _tool_ran(probe):
                reason = (probe or {}).get("summary", "probe not present")
                missing.append(f"{tool} ({reason})")

    if missing:
        return (
            False,
            "STRUCTURAL PROBES GATE: required probes did not run:\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n\nRe-run `forge code-review --step 3` after `forge structural-tools install`, "
            "or bypass with `--allow-structural-probes-incomplete` and override reason/follow-up.",
        )

    return True, "Structural probes gate passed (pyscn/knip executed per stack)."


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
