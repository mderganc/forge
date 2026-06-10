"""Tests for forge sketch orchestrator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKETCH_SCRIPT = REPO_ROOT / "scripts" / "sketch" / "sketch.py"


def _run_sketch(step: int, *, state_dir: Path | None = None, with_domain_docs: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SKETCH_SCRIPT), "--step", str(step)]
    if state_dir is not None:
        state = state_dir / "sketch.json"
        if step > 1:
            cmd.extend(["--state", str(state)])
    if with_domain_docs and step == 1:
        cmd.append("--with-domain-docs")
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_sketch_step1_outputs_startup(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_CODEX_ROOT", str(tmp_path / ".codex" / "forge-codex"))
    (tmp_path / ".codex" / "forge-codex").mkdir(parents=True)
    proc = _run_sketch(1, with_domain_docs=True)
    assert proc.returncode == 0, proc.stderr
    assert "forge sketch" in proc.stdout.lower() or "Sketch" in proc.stdout
    assert "sketch-decisions" in proc.stdout or "sketch" in proc.stdout.lower()
    assert "design spec" in proc.stdout.lower() or "docs/forge/specs" in proc.stdout


def test_sketch_handoff_menu_defaults_to_design(tmp_path, monkeypatch):
    from scripts.shared.orchestrator import SkillState, build_skill_handoff_menu, runtime_state_path

    monkeypatch.setenv("FORGE_CODEX_ROOT", str(tmp_path / ".codex" / "forge-codex"))
    sp = runtime_state_path("sketch", tmp_path)
    state = SkillState(skill_name="sketch", max_step=3)
    menu = build_skill_handoff_menu("sketch", state, sp)
    assert "$forge:design" in menu
    assert "WORKFLOW HANDOFF — sketch complete" in menu


def test_skill_chain_sketch_entry():
    from scripts.shared.skill_chain import SKILL_CHAIN

    assert "sketch" in SKILL_CHAIN
    assert SKILL_CHAIN["sketch"].default == "design"
    assert "sketch" in SKILL_CHAIN["design"].alternatives


@pytest.mark.parametrize("prompt", ["sketch/startup", "sketch/session", "sketch/handoff"])
def test_sketch_prompt_templates_exist(prompt: str):
    path = REPO_ROOT / "prompts" / f"{prompt}.md"
    assert path.is_file(), path
    packaged = REPO_ROOT / "forge_next" / "assets" / "prompts" / f"{prompt}.md"
    assert packaged.is_file(), packaged


def test_integration_spec_includes_sketch():
    spec = json.loads(
        (REPO_ROOT / "integrations" / "spec" / "commands.json").read_text(encoding="utf-8")
    )
    ids = [c["id"] for c in spec["commands"]]
    assert "forge:sketch" in ids
