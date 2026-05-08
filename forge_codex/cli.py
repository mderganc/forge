from __future__ import annotations

import argparse
import io
import json
import os
import sys
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

    # code-review
    cr = sub.add_parser("code-review", help="Run the code-review orchestrator")
    add_common_repo_flag(cr)
    add_common_output_flags(cr)
    cr.add_argument("--step", type=int, required=True)
    cr.add_argument("--state", type=str)
    cr.add_argument("--quick", action="store_true")

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
    repo_root = _repo_root_from_args(getattr(args, "repo", None))

    cmd = args.command
    if getattr(args, "ascii", False):
        os.environ["FORGE_ASCII"] = "1"

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
        if stripped.startswith("forge ") and "--step" in stripped:
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

