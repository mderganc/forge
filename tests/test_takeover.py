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
    state_dir = tmp_path / ".codex" / "forge" / "state"
    state_dir.mkdir(parents=True)
    stale = state_dir / "plan.json"
    stale.write_text('{"skill_name":"plan","current_step":7,"max_step":7,"last_completed_step":7}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    run_cleanup(force=False, all_stale=False)
    assert stale.exists()
    out = capsys.readouterr().out
    assert "Would delete" in out or "dry-run" in out.lower() or "Would delete" in capsys.readouterr().err


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


def test_skill_chain_has_takeover():
    from scripts.shared.skill_chain import SKILL_CHAIN

    assert "takeover" in SKILL_CHAIN
    assert SKILL_CHAIN["takeover"].default == "ship"
    assert "iterate" not in SKILL_CHAIN
