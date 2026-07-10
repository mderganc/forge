"""Parallel session isolation + shared global context."""

from __future__ import annotations

from pathlib import Path

from scripts.shared import handoff_io, resume_context
from scripts.shared.orchestrator import build_next_command, parse_continuation_command
from scripts.shared.runtime_layout import save_state
from scripts.shared.session_store import create_session
from scripts.shared.skill_state import SkillState


def test_parse_continuation_understands_session(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    sid, path = create_session("plan", search_dir=tmp_path)
    cmd = f"/forge:plan --step 2 --session {sid}"
    step, state = parse_continuation_command(cmd)
    assert step == 2
    assert state is not None
    assert sid in state.replace("\\", "/")


def test_build_next_command_emits_session(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    sid, path = create_session("diagnose", search_dir=tmp_path)
    cmd = build_next_command(
        Path("scripts/diagnose/orchestrate.py"),
        1,
        7,
        state=str(path),
    )
    assert f"--session {sid}" in cmd


def test_handoff_pointer_preserves_session_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    sid, path = create_session("design", search_dir=tmp_path)
    state = SkillState(skill_name="design", max_step=8)
    state.session_id = sid
    save_state(state, path)
    hp = handoff_io.write_handoff(
        "design",
        state,
        {"Scope": "test"},
        "plan",
        state_path=path,
    )
    raw = hp.read_text(encoding="utf-8")
    assert "forge_handoff_pointer:" in raw
    session_hp = path.parent / "handoff.md"
    assert session_hp.is_file()
    body = handoff_io.consume_handoff("design", search_dir=tmp_path)
    assert "Scope" in body
    assert session_hp.is_file()  # session handoff not deleted
    assert not hp.exists()  # global pointer cleared


def test_resume_v1_migrates_to_v2_index(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    from scripts.shared.runtime_layout import runtime_state_dir

    state_dir = runtime_state_dir(tmp_path)
    state_dir.mkdir(parents=True)
    v1 = {
        "schema_version": 1,
        "skill": "plan",
        "current_step": 2,
        "last_completed_step": 1,
        "max_step": 7,
        "state_path": str(tmp_path / ".forge" / "sessions" / "abc" / "session.json"),
        "updated_at": "2026-07-10T00:00:00+00:00",
    }
    (state_dir / "resume-context.json").write_text(
        __import__("json").dumps(v1), encoding="utf-8"
    )
    data, warn = resume_context.load_resume_snapshot(tmp_path)
    assert warn is None
    assert data is not None
    assert data["schema_version"] == 2
    assert isinstance(data["sessions"], list)
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["skill"] == "plan"


def test_implement_step1_uses_resolved_session_path(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    from scripts.implement import implement as impl
    from scripts.shared.orchestrator import resolve_step1_state_path

    sp = resolve_step1_state_path("implement", search_dir=tmp_path, label="t")
    state, used = impl._load_or_init_state(None, quick=True, resolved_path=sp)
    assert used == sp
    assert ".forge" in str(used).replace("\\", "/")
    assert "sessions" in str(used).replace("\\", "/")
    flat = tmp_path / ".forge" / "state" / "implement.json"
    assert used != flat
