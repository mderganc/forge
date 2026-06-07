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


def test_session_id_matches_directory_name(session_repo):
    """Session JSON must use the short directory id, not a random UUID."""
    sp = resolve_step1_state_path("plan", search_dir=session_repo, label="sync-test")
    sp.parent.mkdir(parents=True, exist_ok=True)
    state = SkillState(skill_name="plan", max_step=7)
    save_state(state, sp, label="sync-test")
    raw = json.loads(sp.read_text(encoding="utf-8"))
    assert raw["session_id"] == sp.parent.name


def test_find_session_after_runtime_root_fallback(session_repo, monkeypatch):
    """Sessions under read-only .codex/forge remain discoverable for step N."""
    from scripts.shared import repo_paths as rp
    from scripts.shared.runtime_layout import find_state_file, runtime_root

    canonical = session_repo / ".codex" / "forge"
    canonical.mkdir(parents=True)
    sid = "abc123"
    path = session_repo / ".codex" / "forge" / "sessions" / sid / SESSION_JSON
    path.parent.mkdir(parents=True)
    state = SkillState(skill_name="develop", max_step=7, session_id=sid)
    state.current_step = 1
    state.last_completed_step = 1
    save_state(state, path, label="develop-test")

    canonical_resolved = canonical.resolve()
    real_is_writable = rp.is_writable_dir

    def selective_writable(p: Path) -> bool:
        if p.resolve() == canonical_resolved:
            return False
        return real_is_writable(p)

    monkeypatch.setattr("scripts.shared.repo_paths.is_writable_dir", selective_writable)
    assert runtime_root(session_repo).name == ".forge"

    found = find_state_file("develop", session_repo)
    assert found is not None
    assert found.parent.name == sid


def test_save_state_relocates_read_only_session(session_repo, monkeypatch):
    """Step N saves migrate session state to the writable runtime root."""
    from scripts.shared import repo_paths as rp
    from scripts.shared.runtime_layout import runtime_root

    canonical = session_repo / ".codex" / "forge"
    canonical.mkdir(parents=True)
    sid = "def456"
    read_only_path = (
        session_repo / ".codex" / "forge" / "sessions" / sid / SESSION_JSON
    )
    read_only_path.parent.mkdir(parents=True)
    state = SkillState(skill_name="plan", max_step=7, session_id=sid)
    state.current_step = 2
    read_only_path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")

    canonical_resolved = canonical.resolve()
    real_is_writable = rp.is_writable_dir

    def selective_writable(p: Path) -> bool:
        if p.resolve() == canonical_resolved:
            return False
        return real_is_writable(p)

    monkeypatch.setattr("scripts.shared.repo_paths.is_writable_dir", selective_writable)
    assert runtime_root(session_repo).name == ".forge"

    state.current_step = 3
    save_state(state, read_only_path, label="plan-test")

    writable_path = runtime_root(session_repo) / "sessions" / sid / SESSION_JSON
    assert writable_path.is_file()
    saved = json.loads(writable_path.read_text(encoding="utf-8"))
    assert saved["current_step"] == 3
    assert saved["session_id"] == sid
    active = list_active_sessions(session_repo)
    assert len(active) == 1
    assert active[0].path.resolve() == writable_path.resolve()


def test_archive_session_moves_directory(session_repo):
    _write_session(session_repo, "diagnose", session_id="ccc333", label="x")
    dest = archive_session_dir("ccc333", session_repo)
    assert dest is not None
    assert dest.is_dir()
    assert not session_directory("ccc333", session_repo).exists()
    assert list_active_sessions(session_repo) == []
