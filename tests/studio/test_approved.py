from pathlib import Path

import stat

import pytest

from forge_next.studio import approved as studio_approved
from forge_next.studio import session as studio_session


def test_lock_screen_and_block_push(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    session = repo / ".codex" / "forge" / "studio" / "sess-1"
    content = session / "content"
    content.mkdir(parents=True)
    screen = content / "gate1.html"
    d = "d" + "iv"
    screen.write_text(
        f'<{d} data-studio-gate="gate1_hmw"><p>UI mock</p></{d}>',
        encoding="utf-8",
    )

    meta = studio_approved.lock_current_screen(repo, session)
    assert meta["gate"] == "gate1_hmw"
    locked = studio_approved.locked_html_path(repo, "gate1_hmw")
    assert locked.is_file()
    assert "UI mock" in locked.read_text(encoding="utf-8")

    blocked = studio_approved.check_push_allowed(repo, screen)
    assert blocked is not None
    assert "already approved" in blocked.lower()

    with pytest.raises(FileExistsError):
        studio_approved.lock_current_screen(repo, session)

    meta2 = studio_approved.lock_current_screen(repo, session, replace=True)
    assert meta2["gate"] == "gate1_hmw"

    index = studio_approved.index_path(repo)
    assert index.is_file()
    assert "gate1_hmw" in index.read_text(encoding="utf-8")

    mode = locked.stat().st_mode
    assert not (mode & stat.S_IWUSR)

    unlocked = studio_approved.unlock_gate(repo, "gate1_hmw")
    assert unlocked["gate"] == "gate1_hmw"
    assert not studio_approved.is_gate_locked(repo, "gate1_hmw")
    assert not studio_approved.locked_html_path(repo, "gate1_hmw").is_file()


def test_session_repo_root_backfill(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    session_dir = repo / ".codex" / "forge" / "studio" / "legacy-1"
    session_dir.mkdir(parents=True)
    (session_dir / "session.json").write_text(
        '{"v": 1, "session_id": "legacy-1", "workflow": "develop"}',
        encoding="utf-8",
    )
    data = studio_session.load_session(session_dir)
    assert data is not None
    assert data.get("repo_root") == str(repo.resolve())
