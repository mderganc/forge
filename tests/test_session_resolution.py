"""Shared resolve_step_state_path (--session, multi-session guard)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.shared.orchestrator import SkillState, resolve_step_state_path, save_state
from scripts.shared.session_store import create_session
from scripts.shared.skill_aliases import skills_match


def test_is_skill_state_filename_accepts_legacy_develop_json() -> None:
    from scripts.shared.runtime_layout import is_skill_state_filename

    assert is_skill_state_filename("develop.json", "design")
    assert is_skill_state_filename("design.json", "design")


def test_skills_match_design_develop_aliases() -> None:
    assert skills_match("develop", "design")
    assert skills_match("design", "develop")
    assert not skills_match("plan", "design")


def test_resolve_step_state_path_uses_session_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    sid, session_path = create_session("design", label="probe-session", search_dir=tmp_path)
    st = SkillState(skill_name="design", max_step=7, current_step=2)
    save_state(st, session_path)

    resolved = resolve_step_state_path("design", 2, session_id=sid)
    assert resolved.resolve() == session_path.resolve()


def test_resolve_step_state_path_matches_legacy_develop_skill_name(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    sid, session_path = create_session("develop", label="legacy", search_dir=tmp_path)
    st = SkillState(skill_name="develop", max_step=7, current_step=2)
    save_state(st, session_path)

    resolved = resolve_step_state_path("design", 2, session_id=sid)
    assert resolved.resolve() == session_path.resolve()


def test_resolve_step_state_path_errors_on_multiple_active(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    for label in ("a", "b"):
        st = SkillState(skill_name="design", max_step=7, current_step=2)
        _, path = create_session("design", label=label, search_dir=tmp_path)
        save_state(st, path)

    with pytest.raises(SystemExit) as exc:
        resolve_step_state_path("design", 2)
    assert "active" in str(exc.value).lower()
    assert "design" in str(exc.value).lower()
