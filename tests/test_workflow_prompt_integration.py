"""Real orchestrator subprocess tests — rendered prompt content on stdout."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKETCH_SCRIPT = REPO_ROOT / "scripts" / "sketch" / "sketch.py"
DESIGN_SCRIPT = REPO_ROOT / "scripts" / "develop" / "develop.py"


def _run_orchestrator(script: Path, step: int, *, cwd: Path | None = None, extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(script), "--step", str(step)]
    if extra:
        cmd.extend(extra)
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _state_path_from_stderr(stderr: str) -> str:
    m = re.search(r"STATE FILE:\s*(.+)", stderr)
    assert m, f"STATE FILE not found in stderr:\n{stderr}"
    return m.group(1).strip()


def _assert_repo_relative_memory_paths(stdout: str) -> None:
    assert re.search(r"\.(?:codex/forge|forge)/memory/sketch-decisions\.md", stdout)
    assert not re.search(r"[A-Za-z]:\\.*memory", stdout)
    assert "backend-architect" not in stdout.lower()


def test_sketch_step1_real_prompt_memory_paths():
    proc = _run_orchestrator(SKETCH_SCRIPT, 1)
    assert proc.returncode == 0, proc.stderr
    _assert_repo_relative_memory_paths(proc.stdout)
    assert "Dialogue only" not in proc.stdout  # startup prompt; skill md has that


def test_sketch_step2_real_prompt_no_agent_roster_spawn():
    r1 = _run_orchestrator(SKETCH_SCRIPT, 1)
    assert r1.returncode == 0, r1.stderr
    sp = _state_path_from_stderr(r1.stderr)
    r2 = _run_orchestrator(SKETCH_SCRIPT, 2, extra=["--state", sp])
    assert r2.returncode == 0, r2.stderr
    _assert_repo_relative_memory_paths(r2.stdout)
    assert "backend-architect" not in r2.stdout.lower()


def test_design_step3_real_prompt_lists_canonical_agents_only():
    r1 = _run_orchestrator(DESIGN_SCRIPT, 1)
    assert r1.returncode == 0, r1.stderr
    sp = _state_path_from_stderr(r1.stderr)
    r3 = _run_orchestrator(DESIGN_SCRIPT, 3, extra=["--state", sp])
    assert r3.returncode == 0, r3.stderr
    assert "forge-agent-roster.md" in r3.stdout
    assert "Investigator" in r3.stdout and "Architect" in r3.stdout
    assert "never invent `backend-architect`" in r3.stdout.lower()
    assert re.search(r"dispatch\s+backend-architect", r3.stdout, re.I) is None


def test_sketch_protocol_template_has_no_unexpanded_placeholders():
    text = (REPO_ROOT / "templates" / "sketch-protocol.md").read_text(encoding="utf-8")
    assert "{{MEMORY_DIR}}" not in text
    assert ".codex/forge/memory" in text or ".forge/memory" in text
