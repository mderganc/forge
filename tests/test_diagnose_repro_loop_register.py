"""Tests for diagnose feedback-loop sidecar."""

from __future__ import annotations

import json
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.diagnose.repro_loop_register import (
    LOOP_TYPES,
    register_path,
    requires_override_to_proceed,
    summarize,
    validate,
)


def _valid_loop() -> dict:
    return {
        "version": 1,
        "loop_type": "failing_test",
        "command_or_path": "pytest tests/test_foo.py::test_bar -q",
        "deterministic": True,
        "runs_observed": 3,
        "failure_rate": 1.0,
        "symptom_captured": "AssertionError: expected 200 got 500",
        "matches_user_report": True,
        "minimal_repro_steps": ["Run pytest on test_bar"],
        "artifacts": ["logs/test.log"],
        "cannot_build_loop": False,
        "blocked_reason": None,
        "user_ask": None,
    }


def test_loop_types_count():
    assert "none" in LOOP_TYPES
    assert "failing_test" in LOOP_TYPES


def test_validate_missing_file():
    ok, issues = validate(None)
    assert ok is False
    assert any("feedback-loop" in i for i in issues)


def test_validate_valid_loop():
    ok, issues = validate(_valid_loop())
    assert ok is True
    assert issues == []


def test_validate_rejects_empty_symptom():
    data = _valid_loop()
    data["symptom_captured"] = ""
    ok, issues = validate(data)
    assert ok is False


def test_validate_rejects_matches_user_report_false():
    data = _valid_loop()
    data["matches_user_report"] = False
    ok, issues = validate(data)
    assert ok is False


def test_validate_cannot_build_loop():
    data = {
        "version": 1,
        "loop_type": "none",
        "cannot_build_loop": True,
        "blocked_reason": "Needs production credentials",
        "user_ask": "Provide staging access or HAR capture",
        "deterministic": False,
        "runs_observed": 0,
        "failure_rate": None,
        "symptom_captured": "",
        "matches_user_report": False,
        "minimal_repro_steps": [],
        "artifacts": [],
    }
    ok, issues = validate(data)
    assert ok is True
    assert requires_override_to_proceed(data) is True


def test_validate_cannot_build_missing_user_ask():
    data = {
        "version": 1,
        "loop_type": "none",
        "cannot_build_loop": True,
        "blocked_reason": "blocked",
        "user_ask": "",
    }
    ok, issues = validate(data)
    assert ok is False


def test_summarize_loaded_and_blocked():
    assert "failing_test" in summarize(_valid_loop())
    blocked = summarize({
        "cannot_build_loop": True,
        "blocked_reason": "no staging",
    })
    assert "Cannot build loop" in blocked


def test_step3_gate_missing_sidecar(tmp_path):
    from scripts.diagnose import diagnose_gates
    from scripts.diagnose.orchestrate import PHASE_NAMES
    from scripts.shared.orchestrator import SkillState

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "diagnose.json"
    state = SkillState(skill_name="diagnose")
    state.custom["repro_loop_regen_attempts"] = 0

    diagnose_gates.PHASE_NAMES = PHASE_NAMES
    result = diagnose_gates.check_repro_loop_gate(state, state_file, 3)
    assert result.passed is False
    assert result.next_step_override == 2
    assert "DIAGNOSE ARTIFACT GATE" in result.gate_body


def test_step3_gate_valid_loop(tmp_path):
    from scripts.diagnose import diagnose_gates
    from scripts.diagnose.orchestrate import PHASE_NAMES
    from scripts.shared.orchestrator import SkillState

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "diagnose.json"
    register_path(state_dir).write_text(json.dumps(_valid_loop()), encoding="utf-8")
    state = SkillState(skill_name="diagnose")

    diagnose_gates.PHASE_NAMES = PHASE_NAMES
    result = diagnose_gates.check_repro_loop_gate(state, state_file, 3)
    assert result.passed is True


def test_step3_gate_cannot_build_without_override(tmp_path):
    from scripts.diagnose import diagnose_gates
    from scripts.diagnose.orchestrate import PHASE_NAMES
    from scripts.shared.orchestrator import SkillState

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "diagnose.json"
    register_path(state_dir).write_text(
        json.dumps({
            "version": 1,
            "loop_type": "none",
            "cannot_build_loop": True,
            "blocked_reason": "prod only",
            "user_ask": "send HAR",
        }),
        encoding="utf-8",
    )
    state = SkillState(skill_name="diagnose")

    diagnose_gates.PHASE_NAMES = PHASE_NAMES
    result = diagnose_gates.check_repro_loop_gate(state, state_file, 3)
    assert result.passed is False
    assert "override" in result.gate_body.lower()


def test_step3_gate_override_bypasses(tmp_path):
    from scripts.diagnose import diagnose_gates
    from scripts.diagnose.orchestrate import PHASE_NAMES
    from scripts.shared.orchestrator import SkillState

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "diagnose.json"
    state = SkillState(skill_name="diagnose")
    state.custom["repro_loop_override_reason"] = "User provided HAR; proceeding without automated loop"

    diagnose_gates.PHASE_NAMES = PHASE_NAMES
    result = diagnose_gates.check_repro_loop_gate(state, state_file, 3)
    assert result.passed is True


def test_resume_sidecar_lines_warns_when_missing(tmp_path):
    from scripts.shared.resume_single_session import _diagnose_sidecar_lines

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    session = {
        "skill": "diagnose",
        "current_step": 3,
        "path": str(state_dir / "diagnose.json"),
    }
    (state_dir / "diagnose.json").write_text("{}", encoding="utf-8")
    lines = _diagnose_sidecar_lines(session)
    assert any("feedback-loop" in line for line in lines)
