"""Structural probes (knip, madge, pyscn) with agent-selected execution."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIDECAR_NAME = ".structural-probes.json"
INVENTORY_NAME = ".structural-probes-inventory.json"
PLAN_NAME = ".structural-probes-plan.json"
VALID_PROBE_TOOLS = frozenset({"knip", "madge", "pyscn"})

_NODE_MARKERS = (
    "package.json",
    "pnpm-workspace.yaml",
    "lerna.json",
    "nx.json",
)
_NODE_LOCKFILES = (
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
)
_NODE_SUBDIRS = (
    "apps",
    "packages",
    "integrations",
    "frontend",
    "web",
    "app",
    "client",
    "ui",
    "server",
)
_SKIP_PROBE_PARTS = frozenset({
    "node_modules",
    ".venv",
    "venv",
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "graphify-out",
    ".forge",
    "htmlcov",
    ".eggs",
    "site-packages",
    ".nox",
    ".ruff_cache",
    ".hypothesis",
    "coverage",
})

_COUNT_SUFFIXES = (".py", ".ts", ".tsx", ".js")


def _is_vendored_forge_snapshot_dir(part: str) -> bool:
    """PyPI extract trees like ``forge_next-0.14.9/`` (not the live ``forge_next/`` package)."""
    return part.startswith("forge_next-") and part != "forge_next"


def _probe_progress(message: str) -> None:
    """stderr progress so step output is not silent while inventory scans run."""
    print(f"forge: {message}", file=sys.stderr, flush=True)


def skip_structural_probes() -> bool:
    v = os.environ.get("FORGE_SKIP_STRUCTURAL_TOOLS", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def auto_run_structural_probes() -> bool:
    """When set, run probes immediately from heuristics/plan (CI/automation)."""
    v = os.environ.get("FORGE_STRUCTURAL_PROBES_AUTO", "").strip().lower()
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


def _should_prune_dirname(name: str) -> bool:
    """True if ``os.walk`` must not descend into this directory name."""
    if name in _SKIP_PROBE_PARTS:
        return True
    return _is_vendored_forge_snapshot_dir(name)


def _path_under_probe_ignore(path: Path, repo_root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return True
    for part in rel.parts:
        if part in _SKIP_PROBE_PARTS:
            return True
        if _is_vendored_forge_snapshot_dir(part):
            return True
    return False


def _walk_repo_files(
    repo_root: Path,
    *,
    suffix: str | None = None,
    basename: str | None = None,
) -> Iterator[Path]:
    """Walk the repo without descending into venv/node_modules/etc.

    ``Path.rglob`` matches files inside ignored trees first (very slow on ``.venv``).
    This prunes directory names in ``os.walk`` before recursion.
    """
    root = repo_root.resolve()
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [d for d in dirnames if not _should_prune_dirname(d)]
        current = Path(dirpath)
        if _path_under_probe_ignore(current, root):
            dirnames.clear()
            continue
        for name in filenames:
            if basename is not None and name != basename:
                continue
            if suffix is not None and not name.endswith(suffix):
                continue
            path = current / name
            if _path_under_probe_ignore(path, root):
                continue
            yield path


def _source_suffix_counts(
    repo_root: Path,
    *,
    limit_per_suffix: int = 250,
) -> dict[str, int]:
    """Count ``.py`` / ``.ts`` / ``.tsx`` / ``.js`` files in one pruned walk."""
    counts = {s: 0 for s in _COUNT_SUFFIXES}
    for path in _walk_repo_files(repo_root):
        suf = path.suffix
        if suf not in counts:
            continue
        if counts[suf] >= limit_per_suffix:
            if all(counts[s] >= limit_per_suffix for s in _COUNT_SUFFIXES):
                break
            continue
        counts[suf] += 1
    return counts


def _rel_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def _count_source_files(repo_root: Path, suffix: str, *, limit: int = 250) -> int:
    if suffix in _COUNT_SUFFIXES:
        return _source_suffix_counts(repo_root, limit_per_suffix=limit).get(suffix, 0)
    count = 0
    for _path in _walk_repo_files(repo_root, suffix=suffix):
        count += 1
        if count >= limit:
            return count
    return count


def _find_shallow_package_json(repo_root: Path, *, max_depth: int = 4) -> Path | None:
    best: Path | None = None
    best_depth = max_depth + 1
    root = repo_root.resolve()
    for pkg in _walk_repo_files(repo_root, basename="package.json"):
        try:
            depth = len(pkg.parent.relative_to(root).parts)
        except ValueError:
            continue
        if depth > max_depth:
            continue
        if depth < best_depth:
            best = pkg.parent
            best_depth = depth
    return best


def _list_package_json_roots(repo_root: Path, *, limit: int = 12) -> list[str]:
    roots: list[tuple[int, str]] = []
    root = repo_root.resolve()
    for pkg in _walk_repo_files(repo_root, basename="package.json"):
        try:
            depth = len(pkg.parent.relative_to(root).parts)
        except ValueError:
            continue
        if depth > 5:
            continue
        roots.append((depth, _rel_path(pkg.parent, repo_root)))
    roots.sort(key=lambda item: (item[0], item[1]))
    seen: set[str] = set()
    out: list[str] = []
    for _, rel in roots:
        if rel in seen:
            continue
        seen.add(rel)
        out.append(rel)
        if len(out) >= limit:
            break
    return out


def _has_node_project(repo_root: Path) -> bool:
    root = repo_root.resolve()
    for name in _NODE_MARKERS:
        if (root / name).is_file():
            return True
    for name in _NODE_LOCKFILES:
        if (root / name).is_file():
            return True
    if (root / "tsconfig.json").is_file() or (root / "jsconfig.json").is_file():
        return True
    for sub in _NODE_SUBDIRS:
        subdir = root / sub
        if subdir.is_dir() and (subdir / "package.json").is_file():
            return True
    return _find_shallow_package_json(root) is not None


def detect_stack(
    repo_root: Path,
    *,
    suffix_counts: dict[str, int] | None = None,
) -> dict[str, bool]:
    """Heuristic stack flags (hints only — agents choose tools via plan)."""
    root = repo_root.resolve()
    node = _has_node_project(root)
    counts = suffix_counts if suffix_counts is not None else _source_suffix_counts(root)
    py_count = counts.get(".py", 0)
    ts_count = counts.get(".ts", 0) + counts.get(".tsx", 0)
    has_py_project = (root / "pyproject.toml").is_file() or (root / "setup.py").is_file()

    if has_py_project:
        if node and ts_count > py_count:
            python = py_count >= 10
        else:
            python = True
    elif py_count >= 5:
        python = not node or py_count > ts_count
    else:
        python = False

    return {"python": python, "node": node}


def node_probe_root(repo_root: Path) -> Path:
    root = repo_root.resolve()
    if (root / "package.json").is_file():
        return root
    for sub in _NODE_SUBDIRS:
        candidate = root / sub
        if (candidate / "package.json").is_file():
            return candidate
    shallow = _find_shallow_package_json(root)
    return shallow if shallow is not None else root


def python_probe_root(repo_root: Path) -> Path:
    root = repo_root.resolve()
    if (root / "pyproject.toml").is_file() or (root / "setup.py").is_file():
        return root
    per_dir: dict[Path, int] = {}
    for path in _walk_repo_files(repo_root, suffix=".py"):
        per_dir[path.parent] = per_dir.get(path.parent, 0) + 1
    if not per_dir:
        return root
    best_dir, best_count = max(per_dir.items(), key=lambda item: item[1])
    return best_dir if best_count >= 3 else root


def _resolve_probe_root(repo_root: Path, hint: str | None, default: Path) -> Path:
    if not hint:
        return default
    candidate = Path(hint)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def build_stack_inventory(repo_root: Path) -> dict[str, Any]:
    """Factual repo signals for the agent to choose probes."""
    root = repo_root.resolve()
    suffix_counts = _source_suffix_counts(root)
    stack = detect_stack(root, suffix_counts=suffix_counts)
    n_root = node_probe_root(root)
    p_root = python_probe_root(root)
    graphify_report = root / "graphify-out" / "GRAPH_REPORT.md"
    return {
        "repo_root": str(root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stack_hints": stack,
        "counts": {
            "py": suffix_counts.get(".py", 0),
            "ts": suffix_counts.get(".ts", 0),
            "tsx": suffix_counts.get(".tsx", 0),
            "js": suffix_counts.get(".js", 0),
        },
        "markers": {
            "package_json_roots": _list_package_json_roots(root),
            "pyproject": (root / "pyproject.toml").is_file(),
            "setup_py": (root / "setup.py").is_file(),
            "tsconfig": (root / "tsconfig.json").is_file(),
            "workspace_files": [
                name for name in _NODE_MARKERS if (root / name).is_file()
            ],
        },
        "suggested_probe_roots": {
            "node": _rel_path(n_root, root),
            "python": _rel_path(p_root, root),
        },
        "graphify_report": str(graphify_report) if graphify_report.is_file() else None,
    }


def suggest_probe_plan(
    inventory: dict[str, Any],
    *,
    scope_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Heuristic starting plan — agents should confirm or override."""
    hints = inventory.get("stack_hints") or {}
    tools: list[str] = []
    notes: list[str] = []
    if hints.get("node"):
        tools.extend(["knip", "madge"])
        notes.append("Node/TS markers present → knip (dead exports) + madge (cycles).")
    if hints.get("python"):
        tools.append("pyscn")
        notes.append("Python markers present → pyscn (dead code / clones).")
    if not tools:
        notes.append("No strong stack signal — consider skipping all probes or scoping manually.")

    roots = inventory.get("suggested_probe_roots") or {}
    return {
        "tools": tools,
        "node_root": roots.get("node"),
        "python_root": roots.get("python") if "pyscn" in tools else None,
        "scope_paths": list(scope_paths or []),
        "reasoning": " ".join(notes) or "Heuristic suggestion only.",
        "source": "heuristic",
    }


def normalize_probe_tools(tools: object) -> list[str]:
    if not isinstance(tools, list):
        return []
    out: list[str] = []
    for item in tools:
        if not isinstance(item, str):
            continue
        slug = item.strip().lower()
        if slug in VALID_PROBE_TOOLS and slug not in out:
            out.append(slug)
    return out


def plan_path(state_dir: Path | None) -> Path | None:
    if state_dir is None:
        return None
    return Path(state_dir) / PLAN_NAME


def inventory_path(state_dir: Path | None) -> Path | None:
    if state_dir is None:
        return None
    return Path(state_dir) / INVENTORY_NAME


def load_probe_plan(state_dir: Path | None) -> dict[str, Any] | None:
    path = plan_path(state_dir)
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_probe_plan(state_dir: Path, plan: dict[str, Any]) -> Path:
    path = Path(state_dir) / PLAN_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return path


def write_stack_inventory(
    state_dir: Path,
    inventory: dict[str, Any],
    suggestion: dict[str, Any],
) -> Path:
    path = Path(state_dir) / INVENTORY_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"inventory": inventory, "heuristic_suggestion": suggestion}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def merge_plan_with_scope(
    plan: dict[str, Any] | None,
    *,
    scope_paths: list[str] | None,
) -> dict[str, Any]:
    merged = dict(plan or {})
    if scope_paths and not merged.get("scope_paths"):
        merged["scope_paths"] = list(scope_paths)
    merged["tools"] = normalize_probe_tools(merged.get("tools"))
    return merged


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


def _pyscn_check_command(resolved: list[str], *, target: str = ".") -> list[str]:
    if resolved[:1] == ["pyscn"] or (resolved and resolved[0].endswith("pyscn")):
        return ["pyscn", "check", target]
    if resolved and resolved[0] in ("uvx", "uv"):
        return [resolved[0], "pyscn@latest", "check", target]
    return [*resolved, "check", target]


def _madge_entry(node_root: Path, scope_paths: list[str] | None) -> str:
    if scope_paths:
        return scope_paths[0]
    for candidate in ("src", "lib", "app", "."):
        if (node_root / candidate).exists():
            return candidate
    return "."


def _skip_probe(tool: str, reason: str) -> dict[str, Any]:
    return {
        "tool": tool,
        "status": "skip",
        "command": [],
        "summary": reason,
        "findings": [],
    }


def run_probes(
    repo_root: Path,
    *,
    scope_paths: list[str] | None = None,
    state_dir: Path | None = None,
    timeout_per_tool: int = 300,
    quick_mode: bool = False,
    tools: list[str] | None = None,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run only the probes listed in ``plan`` / ``tools``; write results sidecar."""
    from forge_next.structural_tools import (
        resolve_knip_command,
        resolve_madge_command,
        resolve_pyscn_command,
        skip_structural_tools,
    )

    root = repo_root.resolve()
    stack = detect_stack(root)
    merged_plan = merge_plan_with_scope(plan, scope_paths=scope_paths)
    if tools is not None:
        selected = normalize_probe_tools(tools)
    elif merged_plan.get("tools"):
        selected = normalize_probe_tools(merged_plan["tools"])
    else:
        inventory = build_stack_inventory(root)
        selected = normalize_probe_tools(suggest_probe_plan(inventory, scope_paths=scope_paths)["tools"])

    node_root = _resolve_probe_root(
        root, merged_plan.get("node_root"), node_probe_root(root)
    )
    python_root = _resolve_probe_root(
        root, merged_plan.get("python_root"), python_probe_root(root)
    )
    effective_scope = merged_plan.get("scope_paths") or scope_paths
    probes: list[dict[str, Any]] = []

    if skip_structural_tools() or skip_structural_probes():
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
                    "summary": "FORGE_SKIP_STRUCTURAL_TOOLS=1",
                    "findings": [],
                }
            ],
        }
        _write_sidecar(state_dir, payload)
        return payload

    want_knip = "knip" in selected
    want_madge = "madge" in selected
    want_pyscn = "pyscn" in selected

    if want_knip:
        knip = resolve_knip_command()
        if knip:
            code, out = _run_cmd(knip, cwd=node_root, timeout=timeout_per_tool)
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
    else:
        probes.append(_skip_probe("knip", "not selected in probe plan"))

    if want_madge:
        madge = resolve_madge_command()
        if madge:
            entry = _madge_entry(node_root, effective_scope)
            cmd = [*madge, "--circular", entry]
            code, out = _run_cmd(cmd, cwd=node_root, timeout=timeout_per_tool)
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
        probes.append(_skip_probe("madge", "not selected in probe plan"))

    if want_pyscn:
        pyscn = resolve_pyscn_command()
        if pyscn:
            py_target = "."
            if python_root != root:
                try:
                    py_target = str(python_root.relative_to(root))
                except ValueError:
                    py_target = str(python_root)
            cmd = _pyscn_check_command(pyscn, target=py_target)
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
        probes.append(_skip_probe("pyscn", "not selected in probe plan"))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stack": stack,
        "plan": merged_plan,
        "selected_tools": selected,
        "probe_roots": {
            "node": str(node_root),
            "python": str(python_root),
        },
        "probes": probes,
    }
    _write_sidecar(state_dir, payload)
    return payload


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


def format_probe_results_banner(payload: dict[str, Any], sidecar: Path | None) -> str:
    if skip_structural_probes():
        return ""
    bar = ("=" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("━" * 60)
    lines = [
        bar,
        "STRUCTURAL PROBES — results (Pass B)",
        bar,
        "",
        "Read `templates/structural-quality-probes.md` and the results sidecar before structural findings.",
        "",
    ]
    if sidecar:
        lines.append(f"Results: `{sidecar}`")
    plan = payload.get("plan") or {}
    if plan.get("reasoning"):
        lines.append(f"Plan reasoning: {plan['reasoning'][:300]}")
    lines.append(f"Selected tools: {', '.join(payload.get('selected_tools') or []) or '(none)'}")
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


def format_probe_planning_banner(
    state_dir: Path,
    inventory: dict[str, Any],
    suggestion: dict[str, Any],
) -> str:
    if skip_structural_probes():
        return ""
    bar = ("=" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("━" * 60)
    inv_file = Path(state_dir) / INVENTORY_NAME
    plan_file = Path(state_dir) / PLAN_NAME
    run_cmd = f"forge structural-probes run --state-dir {state_dir}"
    lines = [
        bar,
        "STRUCTURAL PROBES — agent selects tools (Pass B)",
        bar,
        "",
        "Do **not** assume knip/madge/pyscn all apply. Use repo facts + your judgment.",
        "",
        "1. Read the inventory (and graphify report if listed):",
        f"   `{inv_file}`",
        "2. Edit the probe plan (start from the heuristic draft):",
        f"   `{plan_file}`",
        "",
        "   Plan fields:",
        "   - `tools`: subset of `knip`, `madge`, `pyscn` (empty `[]` = skip all)",
        "   - `node_root` / `python_root`: relative paths when not repo root",
        "   - `scope_paths`: optional paths for madge/knip focus (e.g. changed packages)",
        "   - `reasoning`: one short paragraph (required — documents your choice)",
        "",
        f"   Heuristic draft tools: {suggestion.get('tools')}",
        f"   Draft reasoning: {str(suggestion.get('reasoning', ''))[:240]}",
        "",
        "3. Run only the selected probes:",
        f"   `{run_cmd}`",
        "",
        "4. Read results sidecar before dispatching reviewers:",
        f"   `{Path(state_dir) / SIDECAR_NAME}`",
        "",
        "Full guide: `templates/structural-quality-probes.md`.",
        "",
        "_Automation (skip agent plan): `FORGE_STRUCTURAL_PROBES_AUTO=1` on the orchestrator step._",
        "_Skip eight subagents: `FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS=1`._",
        "_Full eight-agent dispatch (not default quick trio): `FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1`._",
        "",
    ]
    counts = inventory.get("counts") or {}
    hints = inventory.get("stack_hints") or {}
    lines.insert(
        8,
        f"Stack hints: node={hints.get('node')} python={hints.get('python')} "
        f"(counts: py={counts.get('py')} ts={counts.get('ts')} tsx={counts.get('tsx')})",
    )
    pkg_roots = (inventory.get("markers") or {}).get("package_json_roots") or []
    if pkg_roots:
        lines.insert(9, f"package.json roots: {', '.join(pkg_roots[:6])}")
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
    """Append planning or results banner; agent runs probes via ``forge structural-probes run``."""
    if not should_run_probes(skill_name, step, mode) or skip_structural_probes():
        return body, None, None

    from scripts.shared.repo_paths import equivalent_path_in_repo, resolve_repo_root

    scan_root = resolve_repo_root(repo_root)
    write_dir = equivalent_path_in_repo(Path(state_dir), scan_root)
    write_dir.mkdir(parents=True, exist_ok=True)

    _probe_progress(
        f"structural Pass B — scanning repo inventory ({skill_name} step {step})…"
    )
    inventory = build_stack_inventory(scan_root)
    suggestion = suggest_probe_plan(inventory, scope_paths=scope_paths)
    write_stack_inventory(write_dir, inventory, suggestion)

    plan_file = write_dir / PLAN_NAME
    if not plan_file.is_file():
        write_probe_plan(write_dir, suggestion)

    from scripts.shared.structural_eight_agents import (
        default_eight_agents_quick_mode,
        format_eight_agents_dispatch_banner,
        should_dispatch_eight_agents,
    )

    eight_banner = ""
    if should_dispatch_eight_agents(skill_name, step, mode):
        eight_quick = default_eight_agents_quick_mode(user_quick=quick_mode)
        eight_banner = "\n\n" + format_eight_agents_dispatch_banner(quick_mode=eight_quick)

    if auto_run_structural_probes():
        plan = load_probe_plan(write_dir) or suggestion
        payload = run_probes(
            scan_root,
            scope_paths=scope_paths,
            state_dir=write_dir,
            quick_mode=quick_mode,
            plan=plan,
        )
        sc = sidecar_path(write_dir)
        banner = format_probe_results_banner(payload, sc)
        return body + "\n\n" + banner + eight_banner, sc, payload

    banner = format_probe_planning_banner(write_dir, inventory, suggestion)
    return body + "\n\n" + banner + eight_banner, None, None


def run_probes_from_state_dir(
    repo_root: Path,
    state_dir: Path,
    *,
    tools: list[str] | None = None,
    scope_paths: list[str] | None = None,
) -> dict[str, Any]:
    plan = load_probe_plan(state_dir)
    if plan is None:
        inv_path = inventory_path(state_dir)
        if inv_path and inv_path.is_file():
            try:
                inv_payload = json.loads(inv_path.read_text(encoding="utf-8"))
                plan = inv_payload.get("heuristic_suggestion")
            except (OSError, json.JSONDecodeError):
                plan = None
    if plan is None:
        inventory = build_stack_inventory(repo_root)
        plan = suggest_probe_plan(inventory, scope_paths=scope_paths)
    return run_probes(
        repo_root,
        state_dir=state_dir,
        scope_paths=scope_paths,
        tools=tools,
        plan=plan,
    )


def cli_run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run agent-selected structural probes")
    parser.add_argument(
        "--state-dir",
        type=str,
        required=True,
        help="Workflow state directory (writes .structural-probes.json here)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Target repo root (default: auto-detect from cwd)",
    )
    parser.add_argument(
        "--tools",
        type=str,
        default=None,
        help="Override plan tools (comma-separated: knip,madge,pyscn)",
    )
    args = parser.parse_args(argv)

    state_dir = Path(args.state_dir).resolve()
    if not state_dir.is_dir():
        print(f"ERROR: state directory not found: {state_dir}", file=sys.stderr)
        return 1

    if args.repo:
        repo_root = Path(args.repo).resolve()
    else:
        from scripts.shared.orchestrator import _detect_repo_root

        repo_root = _detect_repo_root(Path.cwd())

    tools = None
    if args.tools:
        tools = normalize_probe_tools(args.tools.split(","))

    payload = run_probes_from_state_dir(repo_root, state_dir, tools=tools)
    sc = sidecar_path(state_dir)
    print(format_probe_results_banner(payload, sc))
    failed = [p for p in payload.get("probes") or [] if p.get("status") == "fail"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(cli_run())
