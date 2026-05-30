"""Sandbox-safe repo root and path aliasing."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.shared import repo_paths as rp


def test_resolve_repo_root_prefers_writable_git_root(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    assert rp.is_writable_dir(tmp_path)
    assert rp.resolve_repo_root(tmp_path) == tmp_path.resolve()


def test_equivalent_path_remaps_under_same_repo(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    state_dir = tmp_path / ".codex" / "forge" / "state"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "code-review.json"
    state_file.write_text("{}", encoding="utf-8")
    mapped = rp.equivalent_path_in_repo(state_file, tmp_path)
    assert mapped.resolve() == state_file.resolve()


def test_alternate_mount_paths_windows_drive_to_mnt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rp.sys, "platform", "win32")
    mnt = tmp_path / "mnt" / "h" / "Code" / "forge"
    mnt.mkdir(parents=True)
    (mnt / ".git").mkdir()
    alts = rp.alternate_mount_paths(mnt)
    assert any("mnt" in str(p).replace("\\", "/") for p in alts)
