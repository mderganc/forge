"""Tests for diagnose methodology sidecars and coverage validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

import sys

sys.path.insert(0, str(REPO_ROOT))

from scripts.diagnose.diagnose_registers import format_combined_gate, GateSection, merge_gate_results
from scripts.diagnose.five_whys_register import validate_chains
from scripts.diagnose.first_principles_register import validate as validate_fp
from scripts.diagnose.mece_tree_register import validate as validate_mece
from scripts.diagnose.problem_spec_register import validate as validate_problem_spec
from scripts.diagnose.technique_coverage import (
    catalog_technique_names,
    load_catalog_technique_names,
    validate_coverage,
)


def test_catalog_has_twenty_techniques():
    names = catalog_technique_names()
    assert len(names) == 20
    assert names[0] == "5 Whys"
    assert "FMEA" in names
    assert "Barrier Analysis" in names


def _valid_five_whys() -> dict:
    return {
        "version": 1,
        "symptom": "API returns 500 on login",
        "chains": [
            {
                "id": "chain-1",
                "hypothesis_id": "H01",
                "layers": [
                    {
                        "level": 1,
                        "because": "Login handler throws when user record is missing",
                        "why_question": "Why is the user record missing in the login handler?",
                        "evidence": "auth.py:47 stack trace",
                        "verdict": "confirmed",
                    },
                    {
                        "level": 2,
                        "because": "Query uses email column but form sends username field",
                        "why_question": "Why is the user record missing from the login handler query result?",
                        "evidence": "diff auth login vs register",
                        "verdict": "confirmed",
                    },
                    {
                        "level": 3,
                        "because": "Migration 20260325 renamed column without updating login SQL",
                        "why_question": "Why does the login query use the email column when the form submits username?",
                        "evidence": "git log db/migrations",
                        "verdict": "confirmed",
                    },
                ],
                "root_cause": "Migration 20260325 omitted login query update",
                "stop_reason": "defect",
                "but_for": "Without that migration gap, login would succeed",
            }
        ],
    }


class TestFiveWhys:
    def test_valid_chain_passes(self):
        ok, issues = validate_chains(_valid_five_whys(), require_confirmed_link=True, confirmed_ids={"H01"})
        assert ok is True
        assert issues == []

    def test_disconnected_why_fails(self):
        data = _valid_five_whys()
        data["chains"][0]["layers"][1]["why_question"] = "Why is the weather bad today?"
        ok, issues = validate_chains(data)
        assert ok is False
        assert any("link" in i.lower() or "causal" in i.lower() for i in issues)

    def test_shallow_chain_fails(self):
        data = _valid_five_whys()
        data["chains"][0]["layers"] = data["chains"][0]["layers"][:1]
        ok, issues = validate_chains(data)
        assert ok is False


class TestTechniqueCoverage:
    def _full_matrix(self, **extra) -> dict:
        rows = []
        for i, name in enumerate(catalog_technique_names(), start=1):
            rows.append({
                "id": i,
                "name": name,
                "status": "skipped",
                "rationale": f"Not needed for smoke test {name}",
            })
        data = {
            "version": 1,
            "incident_profile": ["simple"],
            "routing_preferred": ["5 Whys"],
            "techniques": rows,
        }
        data.update(extra)
        return data

    def test_twenty_rows_valid_skip(self):
        ok, issues, policy = validate_coverage(self._full_matrix())
        assert ok is True
        assert policy == []

    def test_applied_requires_pointer(self):
        data = self._full_matrix()
        data["techniques"][0]["status"] = "applied"
        data["techniques"][0]["rationale"] = ""
        ok, issues, _ = validate_coverage(data)
        assert ok is False
        assert any("evidence_pointer" in i for i in issues)

    def test_highlight_profile_not_high_severity(self):
        data = self._full_matrix(incident_profile=["highlight_regression"])
        for row in data["techniques"]:
            row["status"] = "skipped"
            row["rationale"] = "not needed"
        ok, _, policy = validate_coverage(data, allow_override_skips=False)
        assert ok is True
        assert policy == []

    def test_high_severity_mandatory(self):
        data = self._full_matrix(incident_profile=["high_severity"])
        for row in data["techniques"]:
            if row["name"] == "FMEA":
                row["status"] = "applied"
                row["evidence_pointer"] = "fmea.out"
            elif row["name"] in ("Kepner-Tregoe Problem Analysis", "Barrier Analysis"):
                row["status"] = "skipped"
                row["rationale"] = "skipped wrongly"
        ok, _, policy = validate_coverage(data, allow_override_skips=False)
        assert ok is False
        assert policy


class TestCombinedGate:
    def test_merge_gate_formats_single_block(self):
        sections = [
            GateSection("Hypothesis register", ["too few hypotheses"], "hypothesis_override_reason"),
        ]
        result = merge_gate_results(
            sections,
            phase="Analyze & Rank",
            retry_step=3,
            attempt=0,
            max_attempts=1,
            state_path="/tmp/state.json",
        )
        assert result.passed is False
        assert "DIAGNOSE ARTIFACT GATE" in result.gate_body
        assert "Hypothesis register" in result.gate_body


class TestQuartetRegisters:
    def test_first_principles_requires_violation(self):
        ok, issues = validate_fp({"invariants": ["API returns 2xx for valid auth"]})
        assert ok is False

    def test_mece_min_nodes(self):
        ok, issues = validate_mece({"nodes": [{"id": "n1", "label": "only"}]})
        assert ok is False

    def test_problem_spec_is_isnot(self):
        ok, issues = validate_problem_spec({"cynefin_domain": "Complicated"})
        assert ok is False
        assert any("is_isnot" in i.lower() for i in issues)


class TestOrchestratorBundleGates:
    """Step 5/7 gate wiring (mirrors test_diagnose_hypothesis_register step-4 pattern)."""

    FISHBONE = [
        "CODE", "CONFIG", "DATA", "INFRASTRUCTURE", "DEPENDENCIES", "ENVIRONMENT",
    ]

    @staticmethod
    def _hypothesis(i: int, category: str, status: str = "open") -> dict:
        return {
            "id": f"H{i:02d}",
            "statement": f"Bundle gate candidate {i} in {category} subsystem",
            "category": category,
            "invariant_violated": "invariant",
            "predictions": ["observable"],
            "falsification_test": "test",
            "status": status,
            "evidence": "",
            "ruled_out_reason": "ruled out" if status == "ruled_out" else "",
        }

    def _write_eliminated_register(self, state_dir: Path) -> None:
        from scripts.diagnose.hypothesis_register import register_path

        hyps = [self._hypothesis(i + 1, self.FISHBONE[i % len(self.FISHBONE)]) for i in range(10)]
        for h in hyps:
            h["status"] = "ruled_out"
        hyps[0]["status"] = "confirmed"
        hyps[0]["ruled_out_reason"] = ""
        register_path(state_dir).write_text(
            json.dumps({"min_required": 10, "hypotheses": hyps}),
            encoding="utf-8",
        )

    def test_step5_gate_bad_five_whys_retries_step4(self, tmp_path):
        from scripts.diagnose import diagnose_gates
        from scripts.diagnose.five_whys_register import register_path as five_whys_path
        from scripts.diagnose.orchestrate import PHASE_NAMES
        from scripts.diagnose.technique_coverage import coverage_path
        from scripts.shared.orchestrator import SkillState

        state_dir = tmp_path / "state"
        state_dir.mkdir()
        state_file = state_dir / "diagnose.json"
        state = SkillState(skill_name="diagnose")
        state.custom["step5_bundle_attempts"] = 0

        self._write_eliminated_register(state_dir)
        bad = _valid_five_whys()
        bad["chains"][0]["layers"][1]["why_question"] = "Why is the weather bad today?"
        five_whys_path(state_dir).write_text(json.dumps(bad), encoding="utf-8")

        cov = TestTechniqueCoverage()._full_matrix()
        coverage_path(state_dir).write_text(json.dumps(cov), encoding="utf-8")

        diagnose_gates.PHASE_NAMES = PHASE_NAMES
        result = diagnose_gates.check_step5_bundle_gate(state, state_file, 5)
        assert result.passed is False
        assert result.next_step_override == 4
        assert result.require_confirmation is True
        assert "DIAGNOSE ARTIFACT GATE" in result.gate_body
        assert "Five Whys" in result.gate_body
        assert state.custom["step5_bundle_attempts"] == 1

    def test_step7_gate_incomplete_matrix_retries(self, tmp_path):
        from scripts.diagnose import diagnose_gates
        from scripts.diagnose.orchestrate import PHASE_NAMES
        from scripts.diagnose.technique_coverage import coverage_path
        from scripts.shared.orchestrator import SkillState

        state_dir = tmp_path / "state"
        state_dir.mkdir()
        state_file = state_dir / "diagnose.json"
        state = SkillState(skill_name="diagnose")
        state.custom["step7_closure_attempts"] = 0

        incomplete = {
            "version": 1,
            "incident_profile": ["simple"],
            "routing_preferred": [],
            "techniques": [
                {"id": 1, "name": "5 Whys", "status": "skipped", "rationale": "incomplete"},
            ],
        }
        coverage_path(state_dir).write_text(json.dumps(incomplete), encoding="utf-8")

        diagnose_gates.PHASE_NAMES = PHASE_NAMES
        result = diagnose_gates.check_step7_closure_gate(state, state_file, 7)
        assert result.passed is False
        assert result.next_step_override in (4, 5)
        assert "DIAGNOSE ARTIFACT GATE" in result.gate_body
        assert "Technique coverage" in result.gate_body
        assert state.custom["step7_closure_attempts"] == 1
