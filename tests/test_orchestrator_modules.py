"""Smoke tests for split orchestrator submodules."""

from __future__ import annotations

from pathlib import Path

from scripts.shared import handoff_io, runtime_layout, session_hygiene, state_lifecycle
from scripts.shared.orchestrator import (
    build_skill_handoff_menu,
    detect_active_sessions,
    load_state,
    now_iso,
    read_handoff,
    runtime_state_path,
    save_state,
)


def test_submodules_export_core_api() -> None:
    assert callable(session_hygiene.detect_active_sessions)
    assert callable(handoff_io.write_handoff)
    assert callable(state_lifecycle.now_iso)
    assert callable(runtime_layout.save_state)


def test_orchestrator_reexports_match_submodules() -> None:
    assert detect_active_sessions is session_hygiene.detect_active_sessions
    assert read_handoff is handoff_io.read_handoff
    assert now_iso is state_lifecycle.now_iso


def test_runtime_state_roundtrip(tmp_path: Path, monkeypatch) -> None:
    from scripts.shared.skill_state import SkillState

    state_dir = tmp_path / ".codex" / "forge" / "state"
    state_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    state = SkillState(skill_name="plan", current_step=1, max_step=7)
    path = runtime_state_path("plan")
    save_state(state, path)
    loaded = load_state(path)
    assert loaded.skill_name == "plan"
    assert loaded.current_step == 1


def test_build_skill_handoff_menu_has_default(monkeypatch) -> None:
    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "dollar")
    menu = build_skill_handoff_menu("design")
    assert "WORKFLOW HANDOFF" in menu
    assert "$forge:" in menu
