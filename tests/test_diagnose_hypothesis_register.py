"""Tests for diagnose hypothesis register validation and orchestrator gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT))

from scripts.diagnose.hypothesis_register import (  # noqa: E402
    format_gate_block,
    register_path,
    validate_elimination,
    validate_register,
)

FISHBONE = [
    "CODE", "CONFIG", "DATA", "INFRASTRUCTURE", "DEPENDENCIES", "ENVIRONMENT",
]


def _hypothesis(i: int, category: str, status: str = "open", **extra) -> dict:
    return {
        "id": f"H{i:02d}",
        "statement": f"Unique failure mode {i}: upstream defect in {category} subsystem alpha{i}",
        "category": category,
        "invariant_violated": "invariant",
        "predictions": ["observable"],
        "falsification_test": "test",
        "status": status,
        "evidence": "",
        "ruled_out_reason": extra.get("ruled_out_reason", ""),
        **{k: v for k, v in extra.items() if k != "ruled_out_reason"},
    }


def _valid_register(count: int = 10) -> dict:
    hyps = []
    for i in range(count):
        hyps.append(_hypothesis(i + 1, FISHBONE[i % len(FISHBONE)]))
    return {"min_required": 10, "hypotheses": hyps}


class TestValidateRegister:
    def test_accepts_ten_valid(self):
        ok, issues = validate_register(_valid_register())
        assert ok is True
        assert issues == []

    def test_rejects_nine(self):
        ok, issues = validate_register(_valid_register(9))
        assert ok is False
        assert any("minimum" in i.lower() or "9" in i for i in issues)

    def test_rejects_duplicate_ids(self):
        data = _valid_register()
        data["hypotheses"][1]["id"] = "H01"
        ok, issues = validate_register(data)
        assert ok is False
        assert any("duplicate" in i.lower() for i in issues)

    def test_rejects_invalid_status(self):
        data = _valid_register()
        data["hypotheses"][0]["status"] = "bogus"
        ok, issues = validate_register(data)
        assert ok is False
        assert any("invalid status" in i.lower() for i in issues)

    def test_rejects_few_categories(self):
        data = _valid_register()
        for h in data["hypotheses"]:
            h["category"] = "CODE"
        ok, issues = validate_register(data)
        assert ok is False
        assert any("categories" in i.lower() for i in issues)

    def test_rejects_near_duplicate_statements(self):
        data = _valid_register()
        data["hypotheses"][1]["statement"] = data["hypotheses"][0]["statement"]
        ok, issues = validate_register(data)
        assert ok is False
        assert any("duplicate" in i.lower() or "identical" in i.lower() for i in issues)

    def test_missing_register(self):
        ok, issues = validate_register(None)
        assert ok is False
        assert any("phase 3" in i.lower() for i in issues)


class TestValidateElimination:
    def test_requires_confirmed(self):
        data = _valid_register()
        for h in data["hypotheses"]:
            h["status"] = "ruled_out"
            h["ruled_out_reason"] = "not the cause"
        ok, issues = validate_elimination(data)
        assert ok is False
        assert any("confirmed" in i.lower() for i in issues)

    def test_accepts_one_confirmed(self):
        data = _valid_register()
        for h in data["hypotheses"]:
            h["status"] = "ruled_out"
            h["ruled_out_reason"] = "ruled out"
        data["hypotheses"][0]["status"] = "confirmed"
        ok, issues = validate_elimination(data)
        assert ok is True

    def test_rejects_confirmed_symptom_statement(self):
        data = _valid_register()
        for h in data["hypotheses"]:
            h["status"] = "ruled_out"
            h["ruled_out_reason"] = "ruled out"
        data["hypotheses"][0]["status"] = "confirmed"
        data["hypotheses"][0]["statement"] = "API returns 500 on login"
        data["symptom"] = "API returns 500 on login"
        ok, issues = validate_elimination(data)
        assert ok is False
        assert any("symptom" in i.lower() for i in issues)


class TestFormatGateBlock:
    def test_includes_retry_and_confirmation(self):
        block = format_gate_block(
            ["too few hypotheses"],
            phase="Analyze & Rank",
            retry_step=3,
            attempt=0,
            max_attempts=1,
        )
        assert "HYPOTHESIS REGISTER GATE" in block
        assert "step 3" in block
        assert "wait for approval" in block.lower()
        assert "yes" in block.lower()


class TestOrchestratorGate:
    def test_step4_gate_short_register_retries_step3(self, tmp_path):
        from scripts.diagnose import diagnose_gates
        from scripts.diagnose.orchestrate import PHASE_NAMES
        from scripts.diagnose.problem_spec_register import register_path as problem_spec_path
        from scripts.shared.orchestrator import SkillState, format_step_output

        state_dir = tmp_path / "state"
        state_dir.mkdir()
        state_file = state_dir / "diagnose.json"
        problem_spec_path(state_dir).write_text(
            json.dumps(
                {
                    "framing_entry": "evidence_snapshot",
                    "problem_statement": "Flaky failure under load",
                    "activated_techniques": ["Hypothesis-driven problem solving"],
                }
            ),
            encoding="utf-8",
        )
        state = SkillState(skill_name="diagnose")
        state.max_step = 7
        state.current_step = 3
        state.last_completed_step = 3
        state.custom["autonomy_mode"] = "guided"
        state.custom["hypothesis_min"] = 10
        state.custom["hypothesis_regen_attempts"] = 0

        reg = {
            "min_required": 10,
            "hypotheses": [
                _hypothesis(i, FISHBONE[i % len(FISHBONE)]) for i in range(1, 8)
            ],
        }
        register_path(state_dir).write_text(json.dumps(reg), encoding="utf-8")

        diagnose_gates.PHASE_NAMES = PHASE_NAMES
        result = diagnose_gates.check_register_gate(state, state_file, 4)
        assert result.passed is False
        assert result.next_step_override == 3
        assert result.require_confirmation is True
        assert "DIAGNOSE ARTIFACT GATE" in result.gate_body

        output = format_step_output(
            "diagnose",
            4,
            7,
            PHASE_NAMES[4],
            result.gate_body,
            next_cmd="$forge:diagnose --step 3",
            require_confirmation=True,
        )
        assert "Should I continue" in output
        assert state.custom["hypothesis_regen_attempts"] == 1

    def test_step4_gate_exhausted_retry_no_step3_redirect(self, tmp_path):
        from scripts.diagnose import diagnose_gates
        from scripts.diagnose.orchestrate import PHASE_NAMES
        from scripts.diagnose.problem_spec_register import register_path as problem_spec_path
        from scripts.shared.orchestrator import SkillState

        state_dir = tmp_path / "state"
        state_dir.mkdir()
        state_file = state_dir / "diagnose.json"
        problem_spec_path(state_dir).write_text(
            json.dumps(
                {
                    "framing_entry": "evidence_snapshot",
                    "problem_statement": "Flaky failure under load",
                    "activated_techniques": ["Hypothesis-driven problem solving"],
                }
            ),
            encoding="utf-8",
        )
        state = SkillState(skill_name="diagnose")
        state.custom["hypothesis_min"] = 10
        state.custom["hypothesis_regen_attempts"] = 1

        reg = {
            "min_required": 10,
            "hypotheses": [
                _hypothesis(i, FISHBONE[i % len(FISHBONE)]) for i in range(1, 8)
            ],
        }
        register_path(state_dir).write_text(json.dumps(reg), encoding="utf-8")

        diagnose_gates.PHASE_NAMES = PHASE_NAMES
        result = diagnose_gates.check_register_gate(state, state_file, 4)
        assert result.passed is False
        assert result.next_step_override is None
        assert "hypothesis_override_reason" in result.gate_body
        assert state.custom["hypothesis_regen_attempts"] == 1

    def test_step4_gate_skipped_when_override_reason_set(self, tmp_path):
        from scripts.diagnose import diagnose_gates
        from scripts.diagnose.orchestrate import PHASE_NAMES
        from scripts.shared.orchestrator import SkillState

        state_dir = tmp_path / "state"
        state_dir.mkdir()
        state_file = state_dir / "diagnose.json"
        state = SkillState(skill_name="diagnose")
        state.custom["hypothesis_override_reason"] = "User approved short register for smoke test"

        diagnose_gates.PHASE_NAMES = PHASE_NAMES
        result = diagnose_gates.check_register_gate(state, state_file, 4)
        assert result.passed is True
        assert result.gate_body == ""
