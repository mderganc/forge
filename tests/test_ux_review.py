"""Smoke tests for forge ux-review skill."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
UX_SCRIPT = REPO_ROOT / "scripts" / "ux_review" / "ux_review.py"


@pytest.fixture()
def repo_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FORGE_SKIP_GRAPHIFY", "1")
    monkeypatch.setenv("FORGE_SKIP_SESSION_OPTIN", "1")
    (tmp_path / ".forge").mkdir()
    return tmp_path


def test_ux_review_in_skill_chain():
    from scripts.shared.skill_chain import COMMAND_DESCRIPTIONS, SKILL_CHAIN

    assert "ux-review" in SKILL_CHAIN
    assert SKILL_CHAIN["ux-review"].default == "ship"
    assert "ux-review" in COMMAND_DESCRIPTIONS
    assert "ux-review" in SKILL_CHAIN["implement"].alternatives
    assert "ux-review" in SKILL_CHAIN["code-review"].alternatives
    assert "ux-review" in SKILL_CHAIN["test"].alternatives


def test_ux_review_prompts_exist():
    from scripts.shared.template_engine import load_template

    for name in (
        "ux_review/orient",
        "ux_review/plan",
        "ux_review/walkthrough",
        "ux_review/states",
        "ux_review/findings",
        "ux_review/report",
    ):
        text = load_template(name)
        assert len(text) > 50


def test_ux_review_step1_prints_orient(repo_cwd: Path):
    env = os.environ.copy()
    env["FORGE_SKIP_GRAPHIFY"] = "1"
    env["FORGE_SKIP_SESSION_OPTIN"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(UX_SCRIPT),
            "--step",
            "1",
            "--base-url",
            "http://localhost:3000",
        ],
        cwd=repo_cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    out = (proc.stdout or "").lower()
    assert "orient" in out or "purpose" in out
    assert "http://localhost:3000" in (proc.stdout or "")


def test_ux_review_handoff_diagnose_on_high_findings(tmp_path: Path):
    from scripts.shared.handoff_menu import resolve_handoff_commands
    from scripts.shared.skill_state import SkillState

    state = SkillState(skill_name="ux-review", max_step=6)
    state.custom["findings"] = [
        {
            "title": "Broken save",
            "severity": "high",
            "location": "/settings",
            "impact": "cannot save",
            "steps": ["1. open"],
            "recommendation": "fix handler",
        }
    ]
    default, alts = resolve_handoff_commands(
        "ux-review",
        state,
        default_cmd="ship",
        alternatives=["diagnose", "implement", "code-review", "test"],
    )
    assert default == "diagnose"
    assert "diagnose" not in alts


def test_ux_review_findings_gate_requires_clean_or_coverage():
    from scripts.shared.skill_state import SkillState
    from scripts.ux_review.ux_review import _check_findings_gate

    state = SkillState(skill_name="ux-review", max_step=6)
    state.custom["findings"] = []
    state.custom["coverage"] = {"pages": [], "controls": [], "workflows": []}
    missing = _check_findings_gate(state)
    assert any("clean_review" in m for m in missing)
    assert any("pages/controls/workflows" in m for m in missing)

    state.custom["coverage"] = {
        "pages": ["/home"],
        "controls": [],
        "workflows": [],
        "clean_review": True,
    }
    assert _check_findings_gate(state) == []


def test_ux_review_plan_gate_blocks_without_base_url(repo_cwd: Path):
    """Step 3 with empty plan/base_url exits 1 and prints PLAN GATE."""
    env = os.environ.copy()
    env["FORGE_SKIP_GRAPHIFY"] = "1"
    env["FORGE_SKIP_SESSION_OPTIN"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)
    # step 1
    subprocess.run(
        [sys.executable, str(UX_SCRIPT), "--step", "1"],
        cwd=repo_cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    sessions = list((repo_cwd / ".forge" / "sessions").glob("*/session.json"))
    assert sessions, "expected session after step 1"
    state_path = sessions[0]
    proc = subprocess.run(
        [sys.executable, str(UX_SCRIPT), "--step", "3", "--state", str(state_path)],
        cwd=repo_cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert proc.returncode == 1, proc.stderr + proc.stdout
    assert "PLAN GATE" in (proc.stdout + proc.stderr)


def test_commands_json_includes_ux_review():
    spec = json.loads(
        (REPO_ROOT / "integrations" / "spec" / "commands.json").read_text(encoding="utf-8")
    )
    ids = [c["id"] for c in spec["commands"]]
    assert "forge:ux-review" in ids
