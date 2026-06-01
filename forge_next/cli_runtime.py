"""Repo root resolution and orchestrator module dispatch for the forge CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_git_root(path: Path) -> bool:
    return (path / ".git").is_dir()


def _is_readme_root(path: Path) -> bool:
    return (path / "README.md").is_file()


def resolve_repo_root(start: Path) -> Path | None:
    """Resolve a writable target repo root (sandbox-safe path aliases)."""
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.shared.repo_paths import resolve_repo_root as _resolve

    try:
        return _resolve(start)
    except Exception:
        pass
    start = start.resolve()
    readme_candidate: Path | None = None
    for cur in (start, *start.parents):
        if _is_git_root(cur):
            return cur
        if readme_candidate is None and _is_readme_root(cur):
            readme_candidate = cur
    return readme_candidate


def repo_root_from_args(repo_arg: str | None) -> Path:
    start = Path(repo_arg).expanduser() if repo_arg else Path.cwd()
    root = resolve_repo_root(start)
    if root is None:
        raise SystemExit(
            "Not in a repo; pass --repo <path> (must contain .git/ or README.md)."
        )
    return root


def run_module_main(module_name: str, argv: list[str], repo_root: Path) -> int:
    """Run a scripts/* orchestrator's main() with argv, rooted at repo_root."""
    old_cwd = Path.cwd()
    old_argv = sys.argv[:]
    try:
        os.chdir(repo_root)
        sys.argv = [module_name, *argv]
        mod = __import__(module_name, fromlist=["main"])
        main_fn = getattr(mod, "main", None)
        if not callable(main_fn):
            raise SystemExit(f"Internal error: {module_name} has no main()")
        main_fn()
        return 0
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
