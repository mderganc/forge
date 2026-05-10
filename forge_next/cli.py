from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import urllib.request
import zipfile
import shutil
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr


def _is_git_root(path: Path) -> bool:
    git_dir = path / ".git"
    return git_dir.is_dir()


def _is_readme_root(path: Path) -> bool:
    return (path / "README.md").is_file()


def resolve_repo_root(start: Path) -> Path | None:
    """Resolve a target repo root from a starting directory.

    Policy (pinned):
    - Prefer nearest ancestor containing `.git/`.
    - Fallback to nearest ancestor containing `README.md`.
    """
    start = start.resolve()
    readme_candidate: Path | None = None
    for cur in (start, *start.parents):
        if _is_git_root(cur):
            return cur
        if readme_candidate is None and _is_readme_root(cur):
            readme_candidate = cur
    return readme_candidate


def _run_module_main(module_name: str, argv: list[str], repo_root: Path) -> int:
    """Run a scripts/* orchestrator's main() with argv, rooted at repo_root."""
    old_cwd = Path.cwd()
    old_argv = sys.argv[:]
    try:
        os.chdir(repo_root)
        sys.argv = [module_name, *argv]
        mod = __import__(module_name, fromlist=["main"])
        main_fn = getattr(mod, "main", None)
        if not callable(main_fn):
            raise SystemExit(f"Internal error: {module_name} has no main()")
        main_fn()
        return 0
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="forge", description="Forge Codex launcher CLI")
    sub = p.add_subparsers(dest="command", required=True)

    def add_common_repo_flag(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--repo", type=str, default=None, help="Target repo root (defaults to cwd auto-detected)")

    def add_common_output_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--json", action="store_true", dest="json_output", help="Emit a JSON summary on stdout (human output on stderr)")
        sp.add_argument("--ascii", action="store_true", help="Prefer ASCII-only output")

    # evaluate
    ev = sub.add_parser("evaluate", help="Run the evaluate orchestrator")
    add_common_repo_flag(ev)
    add_common_output_flags(ev)
    ev.add_argument("--step", type=int, required=True)
    ev.add_argument("--plan", type=str)
    ev.add_argument("--state", type=str)
    ev.add_argument("--mode", choices=["pre", "post", "review"])
    ev.add_argument("--team", action="store_true")

    # develop
    dv = sub.add_parser("develop", help="Run the develop orchestrator")
    add_common_repo_flag(dv)
    add_common_output_flags(dv)
    dv.add_argument("--step", type=int, required=True)
    dv.add_argument("--state", type=str)
    dv.add_argument("--quick", action="store_true")
    dv.add_argument("--auto1", action="store_true")
    dv.add_argument("--auto2", action="store_true")
    dv.add_argument("--auto3", action="store_true")

    # plan
    pl = sub.add_parser("plan", help="Run the plan orchestrator")
    add_common_repo_flag(pl)
    add_common_output_flags(pl)
    pl.add_argument("--step", type=int, required=True)
    pl.add_argument("--state", type=str)
    pl.add_argument("--quick", action="store_true")
    pl.add_argument("--force", action="store_true")

    # implement
    im = sub.add_parser("implement", help="Run the implement orchestrator")
    add_common_repo_flag(im)
    add_common_output_flags(im)
    im.add_argument("--step", type=int, required=True)
    im.add_argument("--state", type=str)
    im.add_argument("--quick", action="store_true")
    im.add_argument("--plan", type=str, default=None, help="Path to plan file (implement step 1)")
    im.add_argument(
        "--branch-prefix",
        type=str,
        choices=("feat", "fix", "chore", "refactor", "docs", "hotfix"),
        default=None,
        help="Git branch prefix for feature/task branches (default: feat; stored in state on step 1)",
    )

    # code-review
    cr = sub.add_parser("code-review", help="Run the code-review orchestrator")
    add_common_repo_flag(cr)
    add_common_output_flags(cr)
    cr.add_argument("--step", type=int, required=True)
    cr.add_argument("--state", type=str)
    cr.add_argument("--quick", action="store_true")
    cr.add_argument(
        "--plan",
        type=str,
        default=None,
        help="Optional plan path or keywords (repo + native Cursor/Claude/Codex plan folders)",
    )
    cr.add_argument(
        "--mode", type=str, choices=["pr", "deep", "architecture"], default=None,
        help="Review mode (optional; auto-detected if omitted)",
    )
    cr.add_argument(
        "--target",
        type=str,
        default=None,
        help="PR number, branch name, or paths to review",
    )

    # test
    ts = sub.add_parser("test", help="Run the test orchestrator")
    add_common_repo_flag(ts)
    add_common_output_flags(ts)
    ts.add_argument("--step", type=int, required=True)
    ts.add_argument("--state", type=str)
    ts.add_argument("--quick", action="store_true")
    ts.add_argument("--mode", choices=["run", "flows"])

    # diagnose
    dg = sub.add_parser("diagnose", help="Run the diagnose orchestrator")
    add_common_repo_flag(dg)
    add_common_output_flags(dg)
    dg.add_argument("--step", type=int, required=True)
    dg.add_argument("--state", type=str)
    dg.add_argument("--quick", action="store_true")

    # iterate (meta-workflow)
    it = sub.add_parser("iterate", help="Run the iterate meta-workflow orchestrator")
    add_common_repo_flag(it)
    add_common_output_flags(it)
    it.add_argument("--step", type=int, required=True)
    it.add_argument("--state", type=str)
    it.add_argument("--goal", type=str)
    it.add_argument("--target", type=str)
    it.add_argument("--max-loops", type=int, dest="max_loops")
    it.add_argument("--metric-command", type=str, dest="metric_command")
    it.add_argument("--harness", type=str)
    it.add_argument("--text", type=str, help="Natural-language goal line")

    # status
    st = sub.add_parser("status", help="Show workflow status (dashboard)")
    add_common_repo_flag(st)
    add_common_output_flags(st)

    # doctor
    doc = sub.add_parser("doctor", help="Diagnose installation and environment issues")
    add_common_repo_flag(doc)
    add_common_output_flags(doc)

    # resume
    rs = sub.add_parser("resume", help="Resume an in-progress workflow")
    add_common_repo_flag(rs)
    add_common_output_flags(rs)
    rs.add_argument("--cleanup", action="store_true")
    rs.add_argument("--force", action="store_true")
    rs.add_argument("--all-stale", action="store_true", dest="all_stale")

    # install
    ins = sub.add_parser("install", help="Install integrations (Cursor/Claude/Codex) for this user")
    add_common_output_flags(ins)
    ins.add_argument("--ref", type=str, default="main", help="Git ref/branch for downloads (default: main)")
    ins.add_argument("--repo-url", type=str, default="https://github.com/mderganc/forge", help="Forge repo URL for integration downloads")
    ins.add_argument("--cursor", action="store_true", help="Install Cursor plugin")
    ins.add_argument("--claude", action="store_true", help="Install Claude command pack")
    ins.add_argument("--codex", action="store_true", help="Install Codex skill pack")
    ins.add_argument("--all", action="store_true", help="Install all integrations (default if none selected)")
    ins.add_argument("--cursor-dir", type=str, default=None, help="Override Cursor local plugins directory")
    ins.add_argument("--claude-dir", type=str, default=None, help="Override Claude commands install directory")
    ins.add_argument("--codex-dir", type=str, default=None, help="Override Codex skills install directory")

    # codex-agents — merge ~/.codex/config.toml delegation snippet for Forge skills
    ca = sub.add_parser(
        "codex-agents",
        help="Configure ~/.codex/config.toml so forge:* skills may use Codex sub-agents",
    )
    ca.add_argument("--config", type=str, default=None, help="Path to config.toml (default: ~/.codex/config.toml)")
    ca.add_argument("--force", action="store_true", help="Replace existing developer_instructions")
    ca.add_argument("--dry-run", action="store_true", help="Print actions without writing")

    # uninstall
    un = sub.add_parser("uninstall", help="Uninstall integrations (Cursor/Claude/Codex) for this user")
    add_common_output_flags(un)
    un.add_argument("--cursor", action="store_true", help="Uninstall Cursor plugin")
    un.add_argument("--claude", action="store_true", help="Uninstall Claude command pack")
    un.add_argument("--codex", action="store_true", help="Uninstall Codex skill pack")
    un.add_argument("--all", action="store_true", help="Uninstall all integrations (default if none selected)")
    un.add_argument("--cursor-dir", type=str, default=None, help="Override Cursor local plugins directory")
    un.add_argument("--claude-dir", type=str, default=None, help="Override Claude commands install directory")
    un.add_argument("--codex-dir", type=str, default=None, help="Override Codex skills install directory")

    return p


def _repo_root_from_args(repo_arg: str | None) -> Path:
    start = Path(repo_arg).expanduser() if repo_arg else Path.cwd()
    root = resolve_repo_root(start)
    if root is None:
        raise SystemExit("Not in a repo; pass --repo <path> (must contain .git/ or README.md).")
    return root


def main(argv: list[str] | None = None) -> None:
    os.environ.setdefault("FORGE_USE_LAUNCHER", "1")
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        # Ensure Unicode prompt output works on Windows terminals.
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = build_parser()
    args = parser.parse_args(argv)

    cmd = args.command
    if getattr(args, "ascii", False):
        os.environ["FORGE_ASCII"] = "1"

    if cmd == "codex-agents":
        from forge_next.codex_agents import apply_codex_agents_config, default_codex_config_path

        cfg = Path(getattr(args, "config", None)).expanduser() if getattr(args, "config", None) else default_codex_config_path()
        rc = apply_codex_agents_config(
            cfg,
            force=bool(getattr(args, "force", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
        raise SystemExit(rc)

    if cmd == "install":
        _run_install(
            json_output=getattr(args, "json_output", False),
            repo_url=getattr(args, "repo_url"),
            ref=getattr(args, "ref"),
            install_cursor=bool(getattr(args, "cursor", False)),
            install_claude=bool(getattr(args, "claude", False)),
            install_codex=bool(getattr(args, "codex", False)),
            install_all=bool(getattr(args, "all", False)),
            cursor_dir=getattr(args, "cursor_dir", None),
            claude_dir=getattr(args, "claude_dir", None),
            codex_dir=getattr(args, "codex_dir", None),
        )
        return

    if cmd == "uninstall":
        _run_uninstall(
            json_output=getattr(args, "json_output", False),
            uninstall_cursor=bool(getattr(args, "cursor", False)),
            uninstall_claude=bool(getattr(args, "claude", False)),
            uninstall_codex=bool(getattr(args, "codex", False)),
            uninstall_all=bool(getattr(args, "all", False)),
            cursor_dir=getattr(args, "cursor_dir", None),
            claude_dir=getattr(args, "claude_dir", None),
            codex_dir=getattr(args, "codex_dir", None),
        )
        return

    repo_root = _repo_root_from_args(getattr(args, "repo", None))

    if cmd == "doctor":
        _run_doctor(repo_root, json_output=getattr(args, "json_output", False))
        return

    if cmd == "status":
        _run_status(repo_root, json_output=getattr(args, "json_output", False))
        return

    module_map = {
        "evaluate": "scripts.evaluate.evaluate",
        "develop": "scripts.develop.develop",
        "plan": "scripts.plan.plan",
        "implement": "scripts.implement.implement",
        "code-review": "scripts.code_review.code_review",
        "test": "scripts.test.test",
        "diagnose": "scripts.diagnose.orchestrate",
        "iterate": "scripts.iterate.iterate",
        "resume": "scripts.shared.resume",
    }
    module_name = module_map[cmd]

    def add_flag(out: list[str], flag: str, value: object) -> None:
        if value is None:
            return
        if isinstance(value, bool):
            if value:
                out.append(flag)
            return
        out.extend([flag, str(value)])

    passthrough: list[str] = []
    add_flag(passthrough, "--step", getattr(args, "step", None))
    add_flag(passthrough, "--plan", getattr(args, "plan", None))
    add_flag(passthrough, "--branch-prefix", getattr(args, "branch_prefix", None))
    add_flag(passthrough, "--state", getattr(args, "state", None))
    add_flag(passthrough, "--mode", getattr(args, "mode", None))
    add_flag(passthrough, "--team", getattr(args, "team", None))
    add_flag(passthrough, "--quick", getattr(args, "quick", None))
    add_flag(passthrough, "--force", getattr(args, "force", None))
    add_flag(passthrough, "--cleanup", getattr(args, "cleanup", None))
    add_flag(passthrough, "--force", getattr(args, "force", None))
    add_flag(passthrough, "--all-stale", getattr(args, "all_stale", None))
    add_flag(passthrough, "--auto1", getattr(args, "auto1", None))
    add_flag(passthrough, "--auto2", getattr(args, "auto2", None))
    add_flag(passthrough, "--auto3", getattr(args, "auto3", None))
    add_flag(passthrough, "--goal", getattr(args, "goal", None))
    add_flag(passthrough, "--target", getattr(args, "target", None))
    add_flag(passthrough, "--max-loops", getattr(args, "max_loops", None))
    add_flag(passthrough, "--metric-command", getattr(args, "metric_command", None))
    add_flag(passthrough, "--harness", getattr(args, "harness", None))
    add_flag(passthrough, "--text", getattr(args, "text", None))
    add_flag(passthrough, "--target", getattr(args, "target", None))

    if getattr(args, "json_output", False):
        human_out, rc = _capture_human_output(module_name, passthrough, repo_root)
        summary = _summarize_orchestrator_output(
            repo_root=repo_root,
            command=cmd,
            human_output=human_out,
        )
        summary["error"] = None if rc == 0 else summary.get("error") or f"exit_code={rc}"
        print(json.dumps(summary, ensure_ascii=True))
        if human_out.strip():
            print(human_out, file=sys.stderr)
        raise SystemExit(rc)

    raise SystemExit(_run_module_main(module_name, passthrough, repo_root))


def _run_status(repo_root: Path, json_output: bool = False) -> None:
    """Render a lightweight workflow dashboard for the target repo."""
    from scripts.shared.orchestrator import (
        detect_active_sessions,
        runtime_memory_dir,
        runtime_state_dir,
    )

    old = Path.cwd()
    try:
        os.chdir(repo_root)
        mem_dir = runtime_memory_dir(repo_root)
        state_dir = runtime_state_dir(repo_root)
        sessions = detect_active_sessions(repo_root)

        if json_output:
            payload = {
                "command": "status",
                "repo_root": str(repo_root),
                "memory_dir": str(mem_dir),
                "state_dir": str(state_dir),
                "handoffs": [p.name for p in sorted(mem_dir.glob("handoff-*.md"))] if mem_dir.is_dir() else [],
                "active_sessions": [
                    {
                        "skill": s.get("skill"),
                        "current_step": s.get("current_step"),
                        "max_step": s.get("max_step"),
                        "path": str(s.get("path")),
                    }
                    for s in sessions
                ],
                "warnings": [],
                "error": None,
            }
            print(json.dumps(payload, ensure_ascii=True))
            return

        title = "forge - status" if os.environ.get("FORGE_ASCII") == "1" else "forge — status"
        print(title)
        print("=" * 60)
        print(f"Repo: {repo_root}")
        print(f"Memory: {mem_dir}")
        print(f"State:  {state_dir}")
        print("")

        handoffs = sorted(mem_dir.glob("handoff-*.md")) if mem_dir.is_dir() else []
        print(f"Handoffs: {len(handoffs)}")
        for p in handoffs:
            print(f"- {p.name}")

        print("")
        print(f"Active sessions: {len(sessions)}")
        for s in sessions:
            skill = s.get("skill")
            cur = s.get("current_step")
            mx = s.get("max_step")
            path = s.get("path")
            print(f"- {skill}: step {cur}/{mx} — {path}")
    finally:
        os.chdir(old)


def _run_doctor(repo_root: Path, json_output: bool = False) -> None:
    warnings: list[str] = []
    checks: dict[str, object] = {}

    checks["repo_root"] = str(repo_root)
    checks["python_executable"] = sys.executable
    checks["python_version"] = ".".join(map(str, sys.version_info[:3]))
    checks["pythonutf8"] = os.environ.get("PYTHONUTF8")
    checks["forge_use_launcher"] = os.environ.get("FORGE_USE_LAUNCHER")
    checks["forge_ascii"] = os.environ.get("FORGE_ASCII")

    # Runtime root checks
    codex_anchor = repo_root / ".codex"
    checks["codex_anchor_exists"] = codex_anchor.exists()
    checks["codex_anchor_is_dir"] = codex_anchor.is_dir()
    if codex_anchor.exists() and not codex_anchor.is_dir():
        warnings.append("`.codex` exists but is not a directory; forge will fall back to legacy `.forge` runtime.")

    # Write permission sanity: can we create the state directory?
    try:
        from scripts.shared.orchestrator import runtime_state_dir
        state_dir = runtime_state_dir(repo_root)
        state_dir.mkdir(parents=True, exist_ok=True)
        checks["runtime_state_dir"] = str(state_dir)
    except Exception as e:
        warnings.append(f"Failed to create runtime state dir: {e}")

    payload = {
        "command": "doctor",
        "repo_root": str(repo_root),
        "checks": checks,
        "warnings": warnings,
        "error": None,
    }

    if json_output:
        print(json.dumps(payload, ensure_ascii=True))
        return

    title = "forge - doctor" if os.environ.get("FORGE_ASCII") == "1" else "forge — doctor"
    print(title)
    print("=" * 60)
    for k, v in checks.items():
        print(f"{k}: {v}")
    if warnings:
        print("")
        print("Warnings:")
        for w in warnings:
            print(f"- {w}")


def _capture_human_output(module_name: str, argv: list[str], repo_root: Path) -> tuple[str, int]:
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    rc = 0
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        try:
            rc = _run_module_main(module_name, argv, repo_root)
        except SystemExit as e:
            rc = int(e.code) if isinstance(e.code, int) else 1
        except Exception:
            rc = 1
    # Preserve stderr content after stdout (human output still useful)
    human = buf_out.getvalue()
    if buf_err.getvalue():
        human += ("\n" if human and not human.endswith("\n") else "") + buf_err.getvalue()
    return human, rc


def _summarize_orchestrator_output(repo_root: Path, command: str, human_output: str) -> dict:
    """Best-effort JSON summary based on orchestrator output format."""
    warnings: list[str] = []
    error: str | None = None
    state_path: str | None = None
    next_cmd: str | None = None

    for line in human_output.splitlines():
        if line.startswith("STATE FILE:"):
            state_path = line.replace("STATE FILE:", "", 1).strip()

    # Next command appears on a line by itself, typically indented.
    for line in reversed(human_output.splitlines()):
        stripped = line.strip()
        if "--step" not in stripped:
            continue
        if (
            stripped.startswith("forge ")
            or stripped.startswith("$forge-")
            or stripped.startswith("/forge-")
            or stripped.startswith("$forge:")
        ):
            next_cmd = stripped
            break

    # Extract the first JSON block (phase todos), if present.
    phase_todos = []
    if "```json" in human_output:
        try:
            start = human_output.index("```json") + len("```json")
            end = human_output.index("```", start)
            block = human_output[start:end].strip()
            phase_todos = json.loads(block)
        except Exception:
            warnings.append("Failed to parse phase_todos JSON block.")

    return {
        "command": command,
        "repo_root": str(repo_root),
        "mode": None,
        "step": None,
        "max_step": None,
        "state_path": state_path,
        "next_cmd": next_cmd,
        "phase_todos": phase_todos,
        "warnings": warnings,
        "error": error,
    }


def _default_cursor_local_plugins_dir() -> Path:
    # Windows: %USERPROFILE%\.cursor\plugins\local
    # POSIX:   ~/.cursor/plugins/local
    home = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    return home / ".cursor" / "plugins" / "local"


def _default_claude_commands_dir() -> Path:
    # Opinionated default; can be overridden via --claude-dir.
    home = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    return home / ".claude" / "commands"


def _default_codex_skills_dir() -> Path:
    # Opinionated default; can be overridden via --codex-dir.
    home = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    return home / ".codex" / "skills"


def _download_repo_zip(repo_url: str, ref: str, out_path: Path) -> None:
    zip_url = repo_url.rstrip("/") + f"/archive/refs/heads/{ref}.zip"
    req = urllib.request.Request(zip_url, headers={"User-Agent": "forge-next"})
    with urllib.request.urlopen(req, timeout=30) as resp, out_path.open("wb") as f:
        shutil.copyfileobj(resp, f)


def _extract_zip(zip_path: Path, out_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)


def _copytree_replace(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def _run_install(
    *,
    json_output: bool,
    repo_url: str,
    ref: str,
    install_cursor: bool,
    install_claude: bool,
    install_codex: bool,
    install_all: bool,
    cursor_dir: str | None,
    claude_dir: str | None,
    codex_dir: str | None,
) -> None:
    # Default behavior: install all integrations if none were selected.
    if not (install_cursor or install_claude or install_codex or install_all):
        install_all = True
    if install_all:
        install_cursor = install_claude = install_codex = True

    warnings: list[str] = []
    installed: dict[str, str] = {}

    try:
        with tempfile.TemporaryDirectory(prefix="forge-install-") as td:
            td_path = Path(td)
            zip_path = td_path / "repo.zip"
            extract_dir = td_path / "extract"
            extract_dir.mkdir(parents=True, exist_ok=True)

            _download_repo_zip(repo_url, ref, zip_path)
            _extract_zip(zip_path, extract_dir)

            top = next((p for p in extract_dir.iterdir() if p.is_dir()), None)
            if top is None:
                raise SystemExit("Failed to locate extracted repo folder.")

            if install_cursor:
                src = top / "integrations" / "cursor-plugin"
                if not src.is_dir():
                    warnings.append("Cursor plugin folder not found in downloaded repo.")
                else:
                    base = Path(cursor_dir).expanduser() if cursor_dir else _default_cursor_local_plugins_dir()
                    dst = base / "forge"
                    _copytree_replace(src, dst)
                    installed["cursor_plugin"] = str(dst)

            if install_claude:
                src = top / "integrations" / "claude" / "commands"
                if not src.is_dir():
                    warnings.append("Claude commands folder not found in downloaded repo.")
                else:
                    base = Path(claude_dir).expanduser() if claude_dir else _default_claude_commands_dir()
                    dst = base / "forge"
                    _copytree_replace(src, dst)
                    installed["claude_commands"] = str(dst)

            if install_codex:
                src = top / "integrations" / "codex" / "skills"
                if not src.is_dir():
                    warnings.append("Codex skills folder not found in downloaded repo.")
                else:
                    base = Path(codex_dir).expanduser() if codex_dir else _default_codex_skills_dir()
                    dst = base / "forge"
                    _copytree_replace(src, dst)
                    installed["codex_skills"] = str(dst)
    except Exception as e:
        raise SystemExit(f"forge install failed (download/unpack): {e}")

    payload = {
        "command": "install",
        "repo_url": repo_url,
        "ref": ref,
        "installed": installed,
        "warnings": warnings,
        "error": None,
    }

    if json_output:
        print(json.dumps(payload, ensure_ascii=True))
        return

    title = "forge - install" if os.environ.get("FORGE_ASCII") == "1" else "forge — install"
    print(title)
    print("=" * 60)
    for k, v in installed.items():
        print(f"{k}: {v}")
    if warnings:
        print("")
        print("Warnings:")
        for w in warnings:
            print(f"- {w}")
    print("")
    print("Next steps:")
    print("- Restart your editor/agent environment(s) so new commands are picked up.")
    print("- Run: forge doctor")


def _run_uninstall(
    *,
    json_output: bool,
    uninstall_cursor: bool,
    uninstall_claude: bool,
    uninstall_codex: bool,
    uninstall_all: bool,
    cursor_dir: str | None,
    claude_dir: str | None,
    codex_dir: str | None,
) -> None:
    if not (uninstall_cursor or uninstall_claude or uninstall_codex or uninstall_all):
        uninstall_all = True
    if uninstall_all:
        uninstall_cursor = uninstall_claude = uninstall_codex = True

    removed: dict[str, str] = {}
    missing: list[str] = []
    warnings: list[str] = []

    def rm_tree(path: Path, key: str) -> None:
        if path.exists():
            try:
                shutil.rmtree(path)
                removed[key] = str(path)
            except Exception as e:
                warnings.append(f"Failed to remove {path}: {e}")
        else:
            missing.append(str(path))

    if uninstall_cursor:
        base = Path(cursor_dir).expanduser() if cursor_dir else _default_cursor_local_plugins_dir()
        rm_tree(base / "forge", "cursor_plugin")

    if uninstall_claude:
        base = Path(claude_dir).expanduser() if claude_dir else _default_claude_commands_dir()
        rm_tree(base / "forge", "claude_commands")

    if uninstall_codex:
        base = Path(codex_dir).expanduser() if codex_dir else _default_codex_skills_dir()
        rm_tree(base / "forge", "codex_skills")

    payload = {
        "command": "uninstall",
        "removed": removed,
        "missing": missing,
        "warnings": warnings,
        "error": None,
    }

    if json_output:
        print(json.dumps(payload, ensure_ascii=True))
        return

    title = "forge - uninstall" if os.environ.get("FORGE_ASCII") == "1" else "forge — uninstall"
    print(title)
    print("=" * 60)
    for k, v in removed.items():
        print(f"{k}: removed {v}")
    if missing:
        print("")
        print("Not found (already absent):")
        for p in missing:
            print(f"- {p}")
    if warnings:
        print("")
        print("Warnings:")
        for w in warnings:
            print(f"- {w}")

