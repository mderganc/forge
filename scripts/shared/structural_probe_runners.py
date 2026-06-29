"""Per-tool runners for structural Pass B probes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.shared.structural_probes import (
    SIDECAR_NAME,
    _extract_stdout_json,
    _jscn_analyze_command,
    _jscn_probe_targets,
    _madge_entry,
    _parse_jscn_json_findings,
    _parse_skylos_json_findings,
    _pyscn_analyze_command,
    _pyscn_check_command,
    _pyscn_probe_targets,
    _run_cmd,
    _skip_probe,
    _skylos_scan_command,
    _skylos_scan_targets,
    _tool_findings,
    build_stack_inventory,
    detect_stack,
    filter_applicable_probe_tools,
    is_broad_probe_scope,
    merge_plan_with_scope,
    node_probe_root,
    normalize_probe_tools,
    python_probe_root,
    repo_has_large_ignored_dirs,
    skylos_use_quick_scan,
    suggest_probe_plan,
)


def select_probe_tools(
    repo_root: Path,
    *,
    scope_paths: list[str] | None,
    tools: list[str] | None,
    plan: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    root = repo_root.resolve()
    inventory = build_stack_inventory(root)
    merged_plan = merge_plan_with_scope(plan, scope_paths=scope_paths)
    if tools is not None:
        selected = filter_applicable_probe_tools(normalize_probe_tools(tools), inventory)
    elif merged_plan.get("tools"):
        selected = filter_applicable_probe_tools(
            normalize_probe_tools(merged_plan["tools"]), inventory
        )
    else:
        selected = filter_applicable_probe_tools(
            normalize_probe_tools(
                suggest_probe_plan(inventory, scope_paths=scope_paths)["tools"]
            ),
            inventory,
        )
    return merged_plan, selected


def skipped_all_payload(
    repo_root: Path,
    merged_plan: dict[str, Any],
    selected: list[str],
    *,
    reason: str,
    state_dir: Path | None,
) -> dict[str, Any]:
    stack = detect_stack(repo_root.resolve())
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stack": stack,
        "plan": merged_plan,
        "selected_tools": selected,
        "probes": [
            {
                "tool": "none",
                "status": "skip",
                "command": [],
                "summary": reason,
                "findings": [],
            }
        ],
    }
    if state_dir is not None:
        path = Path(state_dir) / SIDECAR_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def run_knip_probe(
    *,
    node_root: Path,
    timeout: int,
) -> dict[str, Any]:
    from forge_next.structural_tools import resolve_knip_command

    knip = resolve_knip_command()
    if not knip:
        return _skip_probe("knip", "knip not on PATH and npx unavailable")
    code, out = _run_cmd(knip, cwd=node_root, timeout=timeout)
    return {
        "tool": "knip",
        "status": "pass" if code == 0 else "fail",
        "command": knip,
        "summary": (out.splitlines() or [f"exit {code}"])[0][:200],
        "findings": _tool_findings("knip", code, out),
    }


def run_madge_probe(
    *,
    node_root: Path,
    effective_scope: list[str] | None,
    timeout: int,
) -> dict[str, Any]:
    from forge_next.structural_tools import resolve_madge_command

    madge = resolve_madge_command()
    if not madge:
        return _skip_probe("madge", "madge not available")
    entry = _madge_entry(node_root, effective_scope)
    cmd = [*madge, "--circular", entry]
    code, out = _run_cmd(cmd, cwd=node_root, timeout=timeout)
    return {
        "tool": "madge",
        "status": "pass" if code == 0 else "fail",
        "command": cmd,
        "summary": (out.splitlines() or [f"exit {code}"])[0][:200],
        "findings": _tool_findings("madge", code, out),
    }


def run_pyscn_probe(
    *,
    repo_root: Path,
    python_root: Path,
    effective_scope: list[str] | None,
    timeout: int,
) -> dict[str, Any]:
    from forge_next.structural_tools import resolve_pyscn_command

    pyscn = resolve_pyscn_command()
    if not pyscn:
        return _skip_probe("pyscn", "pyscn not available — run forge structural-tools install")

    targets = _pyscn_probe_targets(
        repo_root,
        python_root=python_root,
        effective_scope=effective_scope,
    )
    if not targets:
        return _skip_probe(
            "pyscn",
            "skipped: no safe Python probe scope (repo root blocked by large ignored dirs)",
        )

    use_analyze = bool(effective_scope) or repo_has_large_ignored_dirs(repo_root)
    findings: list[dict[str, Any]] = []
    commands: list[list[str]] = []
    failed = False
    summaries: list[str] = []

    # One file per invocation — avoids batch hangs; each target gets the full timeout.
    for rel in targets:
        if use_analyze:
            cmd = _pyscn_analyze_command(pyscn, targets=[rel])
        else:
            cmd = _pyscn_check_command(pyscn, target=rel)
        commands.append(cmd)
        code, out = _run_cmd(cmd, cwd=repo_root, timeout=timeout)
        if code != 0:
            failed = True
        summaries.append((out.splitlines() or [f"exit {code}"])[0][:120])
        for row in _tool_findings("pyscn", code, out):
            row["id"] = f"P{len(findings) + 1}"
            findings.append(row)

    if len(commands) == 1:
        command: list[str] = commands[0]
        summary = summaries[0]
    else:
        command = commands[0]
        summary = (
            f"per-file pyscn x{len(commands)} "
            f"({timeout}s each); {summaries[0]}"
        )

    return {
        "tool": "pyscn",
        "status": "fail" if failed else "pass",
        "command": command,
        "summary": summary[:200],
        "findings": findings,
    }


def run_jscn_probe(
    *,
    repo_root: Path,
    node_root: Path,
    effective_scope: list[str] | None,
    timeout: int,
) -> dict[str, Any]:
    from forge_next.structural_tools import resolve_jscn_command

    jscn = resolve_jscn_command()
    if not jscn:
        return _skip_probe("jscn", "jscn not available — run forge structural-tools install")

    targets = _jscn_probe_targets(
        repo_root,
        node_root=node_root,
        effective_scope=effective_scope,
    )
    if not targets:
        return _skip_probe(
            "jscn",
            "skipped: no safe JS/TS probe scope (repo root blocked by large ignored dirs)",
        )

    use_per_file = bool(effective_scope) or repo_has_large_ignored_dirs(repo_root)
    findings: list[dict[str, Any]] = []
    commands: list[list[str]] = []
    failed = False
    summaries: list[str] = []

    run_targets = targets if use_per_file else targets[:1]
    for rel in run_targets:
        cmd = _jscn_analyze_command(jscn, targets=[rel])
        commands.append(cmd)
        code, out = _run_cmd(cmd, cwd=repo_root, timeout=timeout)
        if code not in (0, 1):
            failed = True
        parsed = _extract_stdout_json(out)
        if parsed is not None:
            for row in _parse_jscn_json_findings(out):
                row["id"] = f"J{len(findings) + 1}"
                findings.append(row)
        elif code != 0:
            failed = True
            for row in _tool_findings("jscn", code, out):
                row["id"] = f"J{len(findings) + 1}"
                findings.append(row)
        summaries.append((out.splitlines() or [f"exit {code}"])[0][:120])

    if len(commands) == 1:
        command: list[str] = commands[0]
        summary = summaries[0]
    else:
        command = commands[0]
        summary = (
            f"per-file jscn x{len(commands)} "
            f"({timeout}s each); {summaries[0]}"
        )

    return {
        "tool": "jscn",
        "status": "fail" if failed else "pass",
        "command": command,
        "summary": summary[:200],
        "findings": findings,
    }


def run_skylos_probe(
    *,
    repo_root: Path,
    python_root: Path,
    effective_scope: list[str] | None,
    timeout: int,
    quick_mode: bool,
    skill_name: str | None,
    step: int | None,
    exclude_paths: list[str] | None = None,
) -> dict[str, Any]:
    from forge_next.structural_tools import resolve_skylos_command

    skylos = resolve_skylos_command()
    if not skylos:
        return _skip_probe("skylos", "skylos not available — run forge structural-tools install")
    sky_targets = _skylos_scan_targets(
        repo_root=repo_root,
        python_root=python_root,
        scope_paths=effective_scope,
    )
    if (
        not effective_scope
        and repo_has_large_ignored_dirs(repo_root)
        and is_broad_probe_scope(sky_targets)
    ):
        return _skip_probe(
            "skylos",
            "skipped: no safe Python probe scope (repo root blocked by large ignored dirs)",
        )
    quick_scan = quick_mode or skylos_use_quick_scan(
        skill_name, step, scope_paths=effective_scope
    )
    cmd = _skylos_scan_command(
        skylos,
        sky_targets,
        quick_scan=quick_scan,
        exclude_folders=exclude_paths,
        repo_root=repo_root,
    )
    code, out = _run_cmd(cmd, cwd=repo_root, timeout=timeout)
    parsed = _extract_stdout_json(out)
    findings = _parse_skylos_json_findings(out) if parsed is not None else []
    if parsed is None:
        findings = [
            f for f in _tool_findings("skylos", code, out)
            if "Installed " not in (f.get("detail") or "")
        ]
    return {
        "tool": "skylos",
        "status": "pass" if code == 0 else "fail",
        "command": cmd,
        "summary": (out.splitlines() or [f"exit {code}"])[0][:200],
        "findings": findings,
    }
