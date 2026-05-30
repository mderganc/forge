"""Repo root and path resolution for sandboxes (WSL /mnt/* vs Windows drive paths).

Codex and similar sandboxes often expose the same git worktree as:

- ``H:\\Code\\forge`` (writable)
- ``/mnt/h/Code/forge`` (read-only)

Forge must scan and write under the **writable** root and remap ``--state`` paths
that use the other spelling.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_writable_dir(path: Path) -> bool:
    """Return True if we can create and delete a probe file in ``path``."""
    target = path.resolve()
    if target.is_file():
        target = target.parent
    if not target.is_dir():
        return False
    probe = target / f".forge-write-probe-{os.getpid()}"
    try:
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def git_root_from(start: Path) -> Path | None:
    """Nearest ancestor containing ``.git/`` (directory), or None."""
    try:
        cur = start.resolve()
    except OSError:
        cur = start
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").is_dir():
            return candidate
    return None


def same_git_repo(a: Path, b: Path) -> bool:
    """True when both paths refer to the same git worktree."""
    ga = git_root_from(a)
    gb = git_root_from(b)
    if ga is None or gb is None:
        return False
    try:
        return (ga / ".git").resolve().samefile((gb / ".git").resolve())
    except OSError:
        return ga.resolve() == gb.resolve()


def alternate_mount_paths(path: Path) -> list[Path]:
    """Return path plus cross-mount spellings (``/mnt/h/...`` <-> ``H:\\...``)."""
    out: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        try:
            key = os.path.normcase(str(p.resolve()))
        except OSError:
            key = os.path.normcase(str(p))
        if key not in seen:
            seen.add(key)
            out.append(p)

    add(path)
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path

    if sys.platform == "win32":
        drive = resolved.drive
        if len(drive) == 2 and drive[1] == ":":
            letter = drive[0].lower()
            rest = resolved.parts[1:]
            mnt = Path("/mnt") / letter / Path(*rest)
            if mnt.exists():
                add(mnt)
    else:
        parts = resolved.parts
        if len(parts) >= 3 and parts[0] == "/" and parts[1] == "mnt" and len(parts[2]) == 1:
            letter = parts[2]
            win = Path(f"{letter.upper()}:") / Path(*parts[3:])
            if win.exists():
                add(win)

    return out


def _repo_candidates(start: Path) -> list[Path]:
    seeds: list[Path] = []
    for alt in alternate_mount_paths(start):
        seeds.append(alt)
    env = os.environ.get("FORGE_REPO", "").strip()
    if env:
        seeds.insert(0, Path(env).expanduser())

    roots: list[Path] = []
    seen: set[str] = set()
    for seed in seeds:
        root = git_root_from(seed)
        if root is None:
            continue
        try:
            key = os.path.normcase(str(root.resolve()))
        except OSError:
            key = os.path.normcase(str(root))
        if key not in seen:
            seen.add(key)
            roots.append(root)
    return roots


def resolve_repo_root(start: Path | None = None) -> Path:
    """Prefer a **writable** git root; fall back to first discovered root."""
    start_path = (start or Path.cwd()).expanduser()
    roots = _repo_candidates(start_path)
    if not roots:
        try:
            return start_path.resolve()
        except OSError:
            return start_path
    for root in roots:
        if is_writable_dir(root):
            return root
    return roots[0]


def equivalent_path_in_repo(path: Path, repo_root: Path | None = None) -> Path:
    """Map ``path`` onto ``repo_root``, using a writable mount alias when needed."""
    repo = (repo_root or resolve_repo_root()).resolve()
    raw = path.expanduser()
    try:
        resolved = raw.resolve()
    except OSError:
        resolved = raw

    try:
        resolved.relative_to(repo)
        check = resolved.parent if resolved.is_file() else resolved
        if is_writable_dir(check):
            return resolved
        rel = resolved.relative_to(repo)
    except ValueError:
        foreign_root = git_root_from(resolved)
        if foreign_root is None:
            return resolved
        rel = resolved.relative_to(foreign_root)
        if not same_git_repo(foreign_root, repo):
            return resolved
        for alt in _repo_candidates(repo):
            if same_git_repo(alt, foreign_root) and is_writable_dir(alt):
                return (alt / rel).resolve()
        return resolved

    for alt in _repo_candidates(repo):
        if same_git_repo(alt, repo) and is_writable_dir(alt):
            return (alt / rel).resolve()
    return resolved
