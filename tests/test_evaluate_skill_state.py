"""Evaluate state persists as SkillState JSON."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate.state import EvalState, clear_state, load_state, save_state


def test_evaluate_save_load_skill_state_format(tmp_path: Path) -> None:
    sp = tmp_path / ".evaluate-state.json"
    state = EvalState(plan_path=str(tmp_path / "plan.md"), plan_name="plan", mode="pre")
    state.current_step = 2
    state.add_finding("feasibility", "warning", "t", "d")
    save_state(state, sp)

    raw = json.loads(sp.read_text(encoding="utf-8"))
    assert raw["skill_name"] == "evaluate"
    assert raw["custom"]["plan_name"] == "plan"
    assert raw["findings"]

    loaded = load_state(sp)
    assert loaded.plan_name == "plan"
    assert loaded.mode == "pre"
    assert len(loaded.findings) == 1


def test_evaluate_legacy_json_upgrades(tmp_path: Path) -> None:
    sp = tmp_path / ".evaluate-state.json"
    legacy = {
        "plan_path": str(tmp_path / "p.md"),
        "plan_name": "p",
        "mode": "post",
        "current_step": 3,
        "last_completed_step": 2,
        "referenced_files": [],
        "findings": [],
        "review_round": 0,
        "review_findings": [],
        "custom": {"structural_probes_sidecar": "/tmp/x.json"},
    }
    sp.write_text(json.dumps(legacy), encoding="utf-8")
    state = load_state(sp)
    assert state.mode == "post"
    assert state.custom.get("structural_probes_sidecar") == "/tmp/x.json"
    save_state(state, sp)
    assert json.loads(sp.read_text(encoding="utf-8"))["skill_name"] == "evaluate"


def test_state_path_for_plan(tmp_path: Path) -> None:
    from scripts.evaluate.state import state_path_for_plan

    plan = tmp_path / "plans" / "x.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("# plan\n", encoding="utf-8")
    assert state_path_for_plan(str(plan)) == tmp_path / "plans" / ".evaluate-state.json"
