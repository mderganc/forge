"""Run knip, madge, pyscn and write `.structural-probes.json` for workflow steps."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIDECAR_NAME = ".structural-probes.json"

_NODE_MARKERS = (
    "package.json",
    "pnpm-workspace.yaml",
    "lerna.json",
    "nx.json",
)


def skip_structural_probes() -> bool:
    v = os.environ.get("FORGE_SKIP_STRUCTURAL_TOOLS", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def should_run_probes(skill_name: str, step: int, mode: str | None = None) -> bool:
    slug = skill_name.strip().lower()
    if slug == "code-review" and step == 3:
        return True
    if slug == "evaluate" and step == 4 and mode == "post":
        return True
    if slug == "evaluate" and step == 1 and mode == "review":
        return True
    return False


def detect_stack(repo_root: Path) -> dict[str, bool]:
    root = repo_root.resolve()
    node = False
    for name in _NODE_MARKERS:
        if (root / name).is_file():
            node = True
            break
    if not node:
        for sub in ("apps", "packages", "integrations", "frontend", "web"):
            if (root / sub).is_dir() and list((root / sub).rglob("package.json")):
                node = True
                break
    python = (root / "pyproject.toml").is_file() or (root / "setup.py").is_file()
    if not python:
        py_files = list(root.glob("**/*.py"))
        python = len(py_files) >= 3
    return {"python": python, "node": node}


def _run_cmd(cmd: list[str], *, cwd: Path, timeout: int) -> tuple[int, str]:
    import subprocess

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def _tool_findings(tool: str, code: int, out: str, *, max_findings: int = 8) -> list[dict[str, Any]]:
    if code == 0 and len(out) < 200:
        return []
    findings: list[dict[str, Any]] = []
    prefix = {"knip": "K", "madge": "M", "pyscn": "P"}.get(tool, "X")
    lines = [ln for ln in out.splitlines() if ln.strip()]
    for i, line in enumerate(lines[:max_findings], start=1):
        path = ""
        m = re.search(r"([\w./\\-]+\.(?:py|ts|tsx|js|jsx|mjs|cjs))", line)
        if m:
            path = m.group(1)
        findings.append(
            {
                "id": f"{prefix}{i}",
                "severity": "warning" if code != 0 else "suggestion",
                "path": path,
                "detail": line[:500],
            }
        )
    if not findings and code != 0:
        findings.append(
            {
                "id": f"{prefix}0",
                "severity": "warning",
                "path": "",
                "detail": out[:1500] or f"{tool} exited {code}",
            }
        )
    return findings


def _pyscn_check_command(resolved: list[str]) -> list[str]:
    """Build a CI-style pyscn check argv from resolve_pyscn_command() output."""
    if resolved[:1] == ["pyscn"] or (resolved and resolved[0].endswith("pyscn")):
        return ["pyscn", "check", "."]
    if resolved and resolved[0] in ("uvx", "uv"):
        return [resolved[0], "pyscn@latest", "check", "."]
    return [*resolved, "check", "."]


def _madge_entry(repo_root: Path, scope_paths: list[str] | None) -> str:
    if scope_paths:
        return scope_paths[0]
    for candidate in ("src", "lib", "app", "."):
        if (repo_root / candidate).exists():
            return candidate
    return "."


def run_probes(
    repo_root: Path,
    *,
    scope_paths: list[str] | None = None,
    state_dir: Path | None = None,
    timeout_per_tool: int = 300,
    quick_mode: bool = False,
) -> dict[str, Any]:
    """Run applicable probes; write sidecar; return payload."""
    from forge_next.structural_tools import (
        resolve_knip_command,
        resolve_madge_command,
        resolve_pyscn_command,
        skip_structural_tools,
    )

    root = repo_root.resolve()
    stack = detect_stack(root)
    probes: list[dict[str, Any]] = []

    if skip_structural_tools() or skip_structural_probes():
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stack": stack,
            "probes": [
                {
                    "tool": "none",
                    "status": "skip",
                    "command": [],
                    "summary": "FORGE_SKIP_STRUCTURAL_TOOLS=1",
                    "findings": [],
                }
            ],
        }
        _write_sidecar(state_dir, payload)
        return payload

    if stack["node"]:
        knip = resolve_knip_command()
        if knip:
            code, out = _run_cmd(knip, cwd=root, timeout=timeout_per_tool)
            probes.append(
                {
                    "tool": "knip",
                    "status": "pass" if code == 0 else "fail",
                    "command": knip,
                    "summary": (out.splitlines() or [f"exit {code}"])[0][:200],
                    "findings": _tool_findings("knip", code, out),
                }
            )
        else:
            probes.append(_skip_probe("knip", "knip not on PATH and npx unavailable"))

        madge = resolve_madge_command()
        if madge:
            entry = _madge_entry(root, scope_paths)
            cmd = [*madge, "--circular", entry]
            code, out = _run_cmd(cmd, cwd=root, timeout=timeout_per_tool)
            probes.append(
                {
                    "tool": "madge",
                    "status": "pass" if code == 0 else "fail",
                    "command": cmd,
                    "summary": (out.splitlines() or [f"exit {code}"])[0][:200],
                    "findings": _tool_findings("madge", code, out),
                }
            )
        else:
            probes.append(_skip_probe("madge", "madge not available"))
    else:
        probes.append(_skip_probe("knip", "no Node.js project detected"))
        probes.append(_skip_probe("madge", "no Node.js project detected"))

    if stack["python"]:
        pyscn = resolve_pyscn_command()
        if pyscn:
            cmd = _pyscn_check_command(pyscn)
            code, out = _run_cmd(cmd, cwd=root, timeout=timeout_per_tool)
            probes.append(
                {
                    "tool": "pyscn",
                    "status": "pass" if code == 0 else "fail",
                    "command": cmd,
                    "summary": (out.splitlines() or [f"exit {code}"])[0][:200],
                    "findings": _tool_findings("pyscn", code, out),
                }
            )
        else:
            probes.append(_skip_probe("pyscn", "pyscn not available — run forge structural-tools install"))
    else:
        probes.append(_skip_probe("pyscn", "no Python project detected"))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stack": stack,
        "probes": probes,
    }
    _write_sidecar(state_dir, payload)
    return payload


def _skip_probe(tool: str, reason: str) -> dict[str, Any]:
    return {
        "tool": tool,
        "status": "skip",
        "command": [],
        "summary": reason,
        "findings": [],
    }


def _write_sidecar(state_dir: Path | None, payload: dict[str, Any]) -> Path | None:
    if state_dir is None:
        return None
    path = Path(state_dir) / SIDECAR_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def sidecar_path(state_dir: Path | None) -> Path | None:
    if state_dir is None:
        return None
    p = Path(state_dir) / SIDECAR_NAME
    return p if p.is_file() else None


def format_probe_banner(payload: dict[str, Any], sidecar: Path | None) -> str:
    if skip_structural_probes():
        return ""
    bar = ("=" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("━" * 60)
    lines = [
        bar,
        "STRUCTURAL PROBES — knip / madge / pyscn (Pass B)",
        bar,
        "",
        "Read `templates/structural-quality-probes.md` and the sidecar before listing structural findings.",
        "",
    ]
    if sidecar:
        lines.append(f"Sidecar: `{sidecar}`")
    stack = payload.get("stack") or {}
    lines.append(f"Stack: python={stack.get('python')} node={stack.get('node')}")
    for probe in payload.get("probes") or []:
        tool = probe.get("tool", "?")
        status = probe.get("status", "?")
        summary = probe.get("summary", "")
        n = len(probe.get("findings") or [])
        lines.append(f"- {tool}: {status} ({n} finding(s)) — {summary[:120]}")
    lines.append("")
    lines.append("_Suppress: `FORGE_SKIP_STRUCTURAL_TOOLS=1`._")
    lines.append("")
    return "\n".join(lines)


def inject_structural_probes_section(
    body: str,
    *,
    skill_name: str,
    step: int,
    repo_root: Path,
    state_dir: Path,
    mode: str | None = None,
    scope_paths: list[str] | None = None,
    quick_mode: bool = False,
) -> tuple[str, Path | None, dict[str, Any] | None]:
    """Append probe banner to step body when applicable; return sidecar path."""
    if not should_run_probes(skill_name, step, mode):
        return body, None, None
    payload = run_probes(
        repo_root,
        scope_paths=scope_paths,
        state_dir=state_dir,
        quick_mode=quick_mode,
    )
    sc = sidecar_path(state_dir) or (Path(state_dir) / SIDECAR_NAME)
    banner = format_probe_banner(payload, sc if sc.is_file() else None)
    if not banner:
        return body, sc if sc.is_file() else None, payload
    return body + "\n\n" + banner, sc if sc.is_file() else None, payload
