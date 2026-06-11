"""Gitignore and graphifyignore policy for structural probe scans.

``ProbeIgnorePolicy.is_ignored(..., for_scope=False)`` is used during inventory
``os.walk`` scans: hard-coded noise dirs plus fast ``.graphifyignore`` directory
name checks only (no per-path ``git check-ignore`` — too slow on large repos).

``for_scope=True`` applies the full policy for explicit probe targets: hard skips,
``.graphifyignore`` (graphify semantics when installed), and ``git check-ignore``.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


def _is_vendored_forge_snapshot_dir(part: str) -> bool:
    return part.startswith("forge_next-") and part != "forge_next"


@dataclass
class ProbeIgnorePolicy:
    """Skip paths that are gitignored or graphifyignored (plus hard probe skips)."""

    repo_root: Path
    hard_skip_parts: frozenset[str]
    _git_cache: dict[str, bool] = field(default_factory=dict)
    _graphify_patterns: list[tuple[Path, str]] = field(default_factory=list)
    _git_available: bool = False

    def __post_init__(self) -> None:
        self.repo_root = self.repo_root.resolve()
        self._git_available = self._detect_git()
        self._graphify_patterns = self._load_graphify_patterns()

    def _detect_git(self) -> bool:
        try:
            proc = subprocess.run(
                ["git", "-C", str(self.repo_root), "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return proc.returncode == 0

    def _load_graphify_patterns(self) -> list[tuple[Path, str]]:
        try:
            from graphify.detect import _load_graphifyignore

            return _load_graphifyignore(self.repo_root)
        except ImportError:
            return _load_graphifyignore_fallback(self.repo_root)

    def _rel_posix(self, path: Path) -> str | None:
        try:
            return path.resolve().relative_to(self.repo_root).as_posix()
        except ValueError:
            return None

    def _hard_skip_rel(self, rel: str) -> bool:
        for part in Path(rel).parts:
            if part in self.hard_skip_parts:
                return True
            if _is_vendored_forge_snapshot_dir(part):
                return True
        return False

    def is_gitignored(self, path: Path) -> bool:
        rel = self._rel_posix(path)
        if rel is None:
            return True
        if rel in self._git_cache:
            return self._git_cache[rel]
        if not self._git_available:
            self._git_cache[rel] = False
            return False
        try:
            proc = subprocess.run(
                ["git", "-C", str(self.repo_root), "check-ignore", "-q", "--", rel],
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            self._git_cache[rel] = False
            return False
        ignored = proc.returncode == 0
        self._git_cache[rel] = ignored
        return ignored

    def is_graphifyignored(self, path: Path) -> bool:
        if not self._graphify_patterns:
            return False
        try:
            from graphify.detect import _is_ignored

            return _is_ignored(path.resolve(), self.repo_root, self._graphify_patterns)
        except ImportError:
            return _is_graphifyignored_fallback(
                path.resolve(), self.repo_root, self._graphify_patterns
            )

    def _fast_graphify_dir_skip(self, rel: str) -> bool:
        """Cheap directory-name checks for inventory walks (no full pattern eval)."""
        parts = Path(rel).parts
        for _anchor, pattern in self._graphify_patterns:
            if pattern.startswith("!"):
                continue
            p = pattern.lstrip("/").rstrip("/")
            if not p or "/" in p or "*" in p:
                continue
            if rel == p or rel.startswith(p + "/") or p in parts:
                return True
        return False

    def is_ignored(self, path: Path, *, for_scope: bool = False) -> bool:
        rel = self._rel_posix(path)
        if rel is None:
            return True
        if self._hard_skip_rel(rel):
            return True
        if for_scope:
            if self.is_graphifyignored(path):
                return True
            if self.is_gitignored(path):
                return True
        elif self._fast_graphify_dir_skip(rel):
            return True
        return False

    def rel_is_ignored(self, rel: str, *, for_scope: bool = False) -> bool:
        rel = rel.strip().replace("\\", "/").lstrip("./")
        if not rel:
            return True
        return self.is_ignored(self.repo_root / rel, for_scope=for_scope)

    def filter_paths(self, paths: list[str], *, for_scope: bool = True) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw in paths:
            tok = str(raw).strip().replace("\\", "/").lstrip("./")
            if not tok or tok in seen:
                continue
            if self.rel_is_ignored(tok, for_scope=for_scope):
                continue
            seen.add(tok)
            out.append(tok)
        return out

    def skylos_exclude_folders(self, defaults: tuple[str, ...]) -> list[str]:
        """Folder names for skylos ``--exclude-folder`` on broad scans."""
        names: list[str] = []
        seen: set[str] = set()
        for item in (*defaults, *self._graphify_folder_names()):
            name = item.strip().strip("/")
            if not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
        return names

    def _graphify_folder_names(self) -> list[str]:
        names: list[str] = []
        for _anchor, pattern in self._graphify_patterns:
            raw = pattern[1:] if pattern.startswith("!") else pattern
            raw = raw.strip("/")
            if not raw or "/" in raw or raw.startswith("*"):
                continue
            names.append(raw)
        return names


def _find_vcs_root(start: Path) -> Path | None:
    markers = (".git", ".hg", ".svn", "_darcs", ".fossil")
    current = start.resolve()
    home = Path.home()
    while True:
        if any((current / marker).exists() for marker in markers):
            return current
        parent = current.parent
        if parent == current or current == home:
            return None
        current = parent


def _parse_ignore_line(raw: str) -> str:
    line = raw.rstrip("\n\r").lstrip()
    if not line or line.startswith("#"):
        return ""
    if " #" in line:
        line = line.split(" #", 1)[0].rstrip()
    return line


def _load_graphifyignore_fallback(root: Path) -> list[tuple[Path, str]]:
    """Minimal .graphifyignore reader when graphify is not installed."""
    root = root.resolve()
    ceiling = _find_vcs_root(root) or root
    dirs: list[Path] = []
    current = root
    while True:
        dirs.append(current)
        if current == ceiling:
            break
        current = current.parent
    dirs.reverse()

    patterns: list[tuple[Path, str]] = []
    for directory in dirs:
        ignore_file = directory / ".graphifyignore"
        if not ignore_file.is_file():
            continue
        try:
            text = ignore_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for raw in text.splitlines():
            line = _parse_ignore_line(raw)
            if line:
                patterns.append((directory, line))
    return patterns


def _is_graphifyignored_fallback(
    path: Path,
    root: Path,
    patterns: list[tuple[Path, str]],
) -> bool:
    """Simple last-match-wins fallback (no negation re-includes)."""
    if not patterns:
        return False
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return True

    ignored = False
    for _anchor, pattern in patterns:
        if pattern.startswith("!"):
            continue
        p = pattern.lstrip("/").rstrip("/")
        if not p:
            continue
        if rel == p or rel.startswith(p + "/") or path.name == p:
            ignored = True
    return ignored


@lru_cache(maxsize=16)
def get_probe_ignore_policy(repo_root: str, hard_skip_key: str) -> ProbeIgnorePolicy:
    parts = frozenset(hard_skip_key.split("\0")) if hard_skip_key else frozenset()
    return ProbeIgnorePolicy(Path(repo_root), hard_skip_parts=parts)
