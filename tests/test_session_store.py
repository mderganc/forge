"""Tests for session-per-directory workflow state."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.shared.orchestrator import SkillState, save_state
from scripts.shared.orchestrator import resolve_step1_state_path
from scripts.shared.session_store import (
    SESSION_JSON,
    archive_session_dir,
    auto_clean_expired_sessions,
    list_active_sessions,
    migrate_legacy_state_files,
    session_directory,
    sessions_archive_root,
    sessions_root,
)


@pytest.fixture
def session_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    return tmp_path


def _write_session(
    repo: Path,
    skill: str,
    *,
    session_id: str,
    label: str = "test",
    last_touched_at: str | None = None,
    current_step: int = 1,
) -> Path:
    sid = session_id
    path = session_directory(sid, repo) / SESSION_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    state = SkillState(skill_name=skill, max_step=7, session_id=sid)
    state.current_step = current_step
    state.started_at = now
    state.last_touched_at = last_touched_at or now
    save_state(state, path, label=label)
    return path


def test_step1_always_creates_new_session(session_repo):
    p1 = resolve_step1_state_path("plan", search_dir=session_repo, label="first")
    p2 = resolve_step1_state_path("plan", search_dir=session_repo, label="second")
    assert p1 != p2
    assert p1.is_file() is False  # create_session only allocates dir
    assert p1.parent != p2.parent
    assert p1.parent.parent == sessions_root(session_repo)


def test_parallel_sessions_listed(session_repo):
    _write_session(session_repo, "plan", session_id="aaa111", label="a")
    _write_session(session_repo, "plan", session_id="bbb222", label="b")
    active = list_active_sessions(session_repo)
    assert len(active) == 2
    labels = {s.label for s in active}
    assert labels == {"a", "b"}


def test_auto_clean_archives_old_sessions(session_repo, monkeypatch):
    old = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    path = _write_session(
        session_repo,
        "plan",
        session_id="old111",
        label="stale",
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    data["last_touched_at"] = old
    data["started_at"] = old
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    cleaned = auto_clean_expired_sessions(search_dir=session_repo, max_age_days=7)
    assert any(c[0] == "old111" for c in cleaned)
    assert not path.exists()
    assert (sessions_archive_root(session_repo) / "old111" / SESSION_JSON).is_file()


def test_migrate_legacy_plan_json(session_repo):
    from scripts.shared.runtime_layout import runtime_state_dir

    state_dir = runtime_state_dir(session_repo)
    state_dir.mkdir(parents=True, exist_ok=True)
    legacy = state_dir / "plan.json"
    legacy.write_text(
        json.dumps(
            {
                "skill_name": "plan",
                "current_step": 2,
                "last_completed_step": 1,
                "max_step": 7,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    migrated = migrate_legacy_state_files(session_repo)
    assert migrated
    assert not legacy.exists()
    active = list_active_sessions(session_repo)
    assert len(active) == 1
    assert active[0].skill == "plan"


def test_archive_session_moves_directory(session_repo):
    _write_session(session_repo, "diagnose", session_id="ccc333", label="x")
    dest = archive_session_dir("ccc333", session_repo)
    assert dest is not None
    assert dest.is_dir()
    assert not session_directory("ccc333", session_repo).exists()
    assert list_active_sessions(session_repo) == []
