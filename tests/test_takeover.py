"""Tests for forge takeover."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.takeover.cleanup import cleanup_candidates, run_cleanup
from scripts.takeover.deviations import empty_deviations, record_inference, write_deviations
from scripts.takeover.router import build_route_plan


def test_router_design_flag(tmp_path, monkeypatch):
    spec = tmp_path / "docs" / "forge" / "specs"
    spec.mkdir(parents=True)
    design = spec / "2026-06-20-foo-design.md"
    design.write_text("# design\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    plan, inferences = build_route_plan(
        repo_root=tmp_path,
        design=str(design),
        goal=None,
    )
    assert plan.entry_skill == "plan"
    assert plan.design_path == str(design)
    assert any(i["field"] == "design" for i in inferences)


def test_router_issue_bug_routes_diagnose(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan, _ = build_route_plan(repo_root=tmp_path, issue="fix login bug", goal=None)
    assert plan.entry_skill == "diagnose"
    assert "diagnose" in plan.upstream_skills or plan.entry_skill == "diagnose"


def test_router_latest_design_when_no_sessions(tmp_path, monkeypatch):
    spec = tmp_path / "docs" / "forge" / "specs"
    spec.mkdir(parents=True)
    design = spec / "2026-06-20-foo-design.md"
    design.write_text("# design\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    plan, inferences = build_route_plan(repo_root=tmp_path, issue=None, design=None, goal=None)
    assert plan.entry_skill == "plan"
    assert any(i["field"] == "design_spec" for i in inferences)


def test_deviations_write(tmp_path):
    dev = empty_deviations()
    record_inference(dev, "epic", "abc", "test")
    path = tmp_path / ".takeover-deviations.json"
    write_deviations(path, dev)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["inferences"][0]["chosen"] == "abc"


def test_cleanup_dry_run_no_delete(tmp_path, monkeypatch, capsys):
    from tests.helpers.session_fixtures import write_stale_flat_state

    stale = write_stale_flat_state(tmp_path, "plan")
    monkeypatch.chdir(tmp_path)
    run_cleanup(force=False, all_stale=False)
    assert stale.exists()
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "Would delete" in combined or "dry-run" in combined.lower()


def test_takeover_step1_routes(monkeypatch, tmp_path):
    monkeypatch.chdir(REPO)
    from scripts.takeover.takeover import handle_step_1
    import argparse

    sp = tmp_path / "session.json"
    args = argparse.Namespace(
        cleanup=False,
        force=False,
        all_stale=False,
        issue=None,
        design="docs/forge/specs/2026-06-20-forge-takeover-design.md",
        goal=None,
    )
    handle_step_1(args, sp)
    assert sp.exists()
    data = json.loads(sp.read_text(encoding="utf-8"))
    assert data["skill_name"] == "takeover"
    assert data["custom"]["route_plan"]["entry_skill"] == "plan"


def test_router_active_session_path_is_str(tmp_path, monkeypatch):
    session_path = tmp_path / ".forge" / "sessions" / "abc123" / "session.json"
    session_path.parent.mkdir(parents=True)
    session_path.write_text(
        '{"skill_name":"plan","current_step":2,"max_step":7,"last_completed_step":1}',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    def _fake_detect(_search_dir=None):
        return [
            {
                "skill": "plan",
                "session_id": "abc123",
                "path": session_path,
                "started_at": "2026-06-01T00:00:00Z",
            }
        ]

    monkeypatch.setattr("scripts.takeover.router.detect_active_sessions", _fake_detect)
    plan, _ = build_route_plan(repo_root=tmp_path, issue=None, design=None, goal=None)
    assert plan.entry_skill == "plan"
    assert isinstance(plan.active_session_path, str)
    assert plan.active_session_path == str(session_path)


def test_save_state_serializes_path_values(tmp_path):
    from scripts.shared.orchestrator import SkillState, save_state

    sp = tmp_path / "session.json"
    state = SkillState(skill_name="takeover", current_step=1, max_step=7)
    state.custom["route_plan"] = {"active_session_path": tmp_path / "nested" / "session.json"}
    save_state(state, sp)
    data = json.loads(sp.read_text(encoding="utf-8"))
    assert data["custom"]["route_plan"]["active_session_path"] == str(tmp_path / "nested" / "session.json")


def test_gates_dir_under_forge_runtime(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from scripts.takeover.takeover import (
        _ensure_gates_dir,
        _legacy_gates_dir,
        gates_dir,
        gates_dir_relative,
    )

    assert gates_dir(tmp_path) == tmp_path / ".forge" / ".takeover-gates"
    assert gates_dir_relative(tmp_path) == ".forge/.takeover-gates"

    legacy = _legacy_gates_dir(tmp_path)
    legacy.mkdir(parents=True)
    (legacy / "plan.json").write_text('{"status":"pass"}', encoding="utf-8")
    gd = _ensure_gates_dir(tmp_path)
    assert gd == tmp_path / ".forge" / ".takeover-gates"
    assert (gd / "plan.json").exists()
    assert json.loads((gd / "plan.json").read_text(encoding="utf-8"))["status"] == "pass"


def test_skill_chain_has_takeover():
    from scripts.shared.skill_chain import SKILL_CHAIN

    assert "takeover" in SKILL_CHAIN
    assert SKILL_CHAIN["takeover"].default == "ship"
    assert "iterate" not in SKILL_CHAIN
