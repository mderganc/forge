"""Helpers for structural probe gate validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.shared.structural_probes import (
    build_stack_inventory,
    inventory_stack_capabilities,
)


def probe_by_tool(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in payload.get("probes") or []:
        if isinstance(row, dict) and row.get("tool"):
            out[str(row["tool"])] = row
    return out


def stack_flags(payload: dict[str, Any], repo_root: Path) -> tuple[bool, bool]:
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


def tool_ran(probe: dict[str, Any] | None) -> bool:
    if not probe:
        return False
    return probe.get("status") in ("pass", "fail")


def missing_required_probes(
    by_tool: dict[str, dict[str, Any]],
    *,
    python_capable: bool,
    node_capable: bool,
    python_tools: tuple[str, ...],
    node_tools: tuple[str, ...],
) -> list[str]:
    missing: list[str] = []
    if python_capable:
        for tool in python_tools:
            probe = by_tool.get(tool)
            if not tool_ran(probe):
                reason = (probe or {}).get("summary", "probe not present")
                missing.append(f"{tool} ({reason})")
    if node_capable:
        for tool in node_tools:
            probe = by_tool.get(tool)
            if not tool_ran(probe):
                reason = (probe or {}).get("summary", "probe not present")
                missing.append(f"{tool} ({reason})")
    return missing
