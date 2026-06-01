"""Run pytest for forge:test step 3 and parse summary into state.custom."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


_FORGE_SUBPROCESS_ENV_STRIP = (
    "FORGE_SKIP_TEST_AUTO_RUN",
    "FORGE_SKIP_AUTO_CLOSE",
    "FORGE_SKIP_SESSION_OPTIN",
    "FORGE_SKIP_GRAPHIFY",
    "FORGE_SKIP_SUBAGENT_LIFECYCLE",
)


def skip_test_auto_run() -> bool:
    v = os.environ.get("FORGE_SKIP_TEST_AUTO_RUN", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def force_test_rerun() -> bool:
    v = os.environ.get("FORGE_TEST_FORCE_RERUN", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def should_run_pytest(custom: dict[str, Any]) -> bool:
    """Whether step 3 should invoke pytest (skip if results exist unless forced)."""
    if skip_test_auto_run():
        return False
    if force_test_rerun():
        return True
    tr = custom.get("test_results") or {}
    return not tr.get("total")


def pytest_subprocess_env() -> dict[str, str]:
    """Environment for pytest — omit Forge debug skips inherited from the parent shell."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    for key in _FORGE_SUBPROCESS_ENV_STRIP:
        env.pop(key, None)
    return env


def default_pytest_command(repo_root: Path, target_tokens: list[str] | None = None) -> str:
    """Build the default pytest invocation for this repo."""
    if target_tokens:
        args = " ".join(target_tokens)
        return f"{sys.executable} -m pytest {args}"
    tests_dir = repo_root / "tests"
    if tests_dir.is_dir():
        return f"{sys.executable} -m pytest tests/ -q --tb=no"
    return f"{sys.executable} -m pytest -q --tb=no"


def discover_pytest_command(repo_root: Path, target_tokens: list[str] | None = None) -> str:
    """Prefer explicit target; else pytest.ini layout; else default."""
    return default_pytest_command(repo_root, target_tokens)


def parse_pytest_argv(command: str) -> list[str]:
    """Split an orchestrator-built pytest command for shell-free execution."""
    return shlex.split(command, posix=(os.name != "nt"))


def _parse_pytest_summary(stdout: str, stderr: str, exit_code: int) -> dict[str, Any]:
    combined = f"{stdout}\n{stderr}"
    passed = failed = skipped = error = 0
    total = 0

    # e.g. "358 passed in 132.97s" or "6 failed, 352 passed in 8.08s"
    m = re.search(
        r"(?:(\d+)\s+failed,?\s*)?(?:(\d+)\s+passed,?\s*)?(?:(\d+)\s+skipped,?\s*)?(?:(\d+)\s+error,?\s*)?",
        combined,
    )
    if m:
        failed = int(m.group(1) or 0)
        passed = int(m.group(2) or 0)
        skipped = int(m.group(3) or 0)
        error = int(m.group(4) or 0)
        total = passed + failed + skipped + error

    if total == 0:
        # short test summary info block
        for line in combined.splitlines():
            if " passed" in line and " in " in line:
                m2 = re.search(
                    r"(\d+)\s+failed.*?(\d+)\s+passed|(\d+)\s+passed",
                    line,
                )
                if m2:
                    if m2.group(1) is not None:
                        failed = int(m2.group(1))
                        passed = int(m2.group(2) or 0)
                    else:
                        passed = int(m2.group(3) or 0)
                    total = passed + failed + skipped + error
                    break

    duration_s = None
    dm = re.search(r"in\s+([\d.]+)s", combined)
    if dm:
        try:
            duration_s = float(dm.group(1))
        except ValueError:
            duration_s = None

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "error": error,
        "total": total,
        "exit_code": exit_code,
        "duration_s": duration_s,
        "ok": exit_code == 0 and failed == 0 and error == 0,
    }


def format_execution_log(result: dict[str, Any]) -> str:
    """Markdown block for report template variable TEST_EXECUTION_LOG."""
    cmd = result.get("command", "(unknown)")
    lines = [
        f"**Command:** `{cmd}`",
        f"**Exit code:** {result.get('exit_code', '?')}",
        f"**Passed:** {result.get('passed', 0)} | **Failed:** {result.get('failed', 0)} | "
        f"**Skipped:** {result.get('skipped', 0)} | **Errors:** {result.get('error', 0)} | "
        f"**Total:** {result.get('total', 0)}",
    ]
    if result.get("duration_s") is not None:
        lines.append(f"**Duration:** {result['duration_s']}s")
    tail = (result.get("stdout_tail") or "").strip()
    if tail:
        lines.extend(["", "**Output (tail):**", "", "```text", tail[-8000:], "```"])
    return "\n".join(lines) + "\n"


def run_pytest(
    repo_root: Path,
    command: str | None = None,
    *,
    timeout_s: float = 600.0,
) -> dict[str, Any]:
    """Execute pytest in repo_root and return parsed summary + log tail."""
    repo_root = repo_root.resolve()
    cmd_str = command or default_pytest_command(repo_root)
    argv = parse_pytest_argv(cmd_str)
    proc = subprocess.run(
        argv,
        shell=False,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=pytest_subprocess_env(),
    )
    parsed = _parse_pytest_summary(proc.stdout, proc.stderr, proc.returncode)
    parsed["command"] = cmd_str
    parsed["argv"] = argv
    parsed["stdout_tail"] = (proc.stdout or "")[-12000:] + (
        ("\n" + (proc.stderr or "")[-4000:]) if proc.stderr else ""
    )
    return parsed


def apply_results_to_state_custom(custom: dict[str, Any], result: dict[str, Any]) -> None:
    custom["test_results"] = {
        "passed": result.get("passed", 0),
        "failed": result.get("failed", 0),
        "skipped": result.get("skipped", 0),
        "total": result.get("total", 0),
        "coverage_pct": custom.get("test_results", {}).get("coverage_pct", "N/A"),
        "exit_code": result.get("exit_code"),
        "command": result.get("command"),
        "duration_s": result.get("duration_s"),
    }
    custom["test_execution_log"] = format_execution_log(result)
