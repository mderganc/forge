"""Runtime adaptation: writable repo root, legacy migration, profile cache."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

from scripts.shared.state_lifecycle import now_iso

ADAPTATION_FILENAME = "adaptation.json"
MIGRATION_AUDIT_FILENAME = "migration.json"
LEGACY_RUNTIME_SOURCES = (
    (".codex", "forge"),
    (".codex", "forge-codex"),
)
MIGRATE_SUBDIRS = ("sessions", "memory", "state")


def writable_repo_root(search_dir: Path | None = None) -> Path:
    """Return the writable git root for Forge writes (no read-only alias)."""
    from scripts.shared.repo_paths import resolve_repo_root

    start = search_dir or Path.cwd()
    return resolve_repo_root(start)


def _legacy_runtime_sources(repo: Path) -> list[Path]:
    return [repo.joinpath(*parts) for parts in LEGACY_RUNTIME_SOURCES]


def migrate_legacy_runtime_trees(search_dir: Path | None = None) -> dict[str, Any]:
    """Copy ``.codex/forge*`` trees into ``.forge/`` before new writes."""
    repo = writable_repo_root(search_dir)
    target = repo / ".forge"
    target.mkdir(parents=True, exist_ok=True)
    state_dir = target / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    audit: dict[str, Any] = {
        "migrated_at": now_iso(),
        "target": str(target),
        "sources": [],
    }

    for src in _legacy_runtime_sources(repo):
        if not src.is_dir():
            continue
        entry: dict[str, Any] = {"path": str(src), "copied": []}
        for sub in MIGRATE_SUBDIRS:
            src_sub = src / sub
            if not src_sub.is_dir():
                continue
            dst_sub = target / sub
            dst_sub.mkdir(parents=True, exist_ok=True)
            for item in src_sub.iterdir():
                dst_item = dst_sub / item.name
                if dst_item.exists():
                    continue
                if item.is_dir():
                    shutil.copytree(item, dst_item)
                else:
                    shutil.copy2(item, dst_item)
                entry["copied"].append(f"{sub}/{item.name}")
        if entry["copied"]:
            audit["sources"].append(entry)

    audit_path = state_dir / MIGRATION_AUDIT_FILENAME
    try:
        audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    except OSError:
        pass
    return audit


def build_adaptation_profile(repo: Path) -> dict[str, Any]:
    """Probe mount aliases and writability; return profile dict."""
    from scripts.shared.repo_paths import alternate_mount_paths, is_writable_dir

    aliases: list[str] = []
    writable: str | None = None
    for alt in alternate_mount_paths(repo):
        aliases.append(str(alt))
        if writable is None and is_writable_dir(alt):
            writable = str(alt)

    mount_class = "native"
    if sys.platform != "win32":
        try:
            resolved = repo.resolve()
            parts = resolved.parts
            if len(parts) >= 3 and parts[1] == "mnt":
                mount_class = "wsl_bind"
        except OSError:
            mount_class = "unknown"

    if writable is None:
        mount_class = "sandbox_ro" if aliases else "unknown"

    return {
        "adapted_at": now_iso(),
        "writable_repo_root": writable or str(repo),
        "cwd_aliases": aliases,
        "mount_class": mount_class,
        "runtime_root": ".forge",
    }


def adapt_runtime(search_dir: Path | None = None) -> dict[str, Any]:
    """Migrate legacy trees, ensure ``.forge/``, write ``adaptation.json``."""
    from scripts.shared.runtime_layout import ensure_runtime_dirs, runtime_root

    repo = writable_repo_root(search_dir)
    migrate_legacy_runtime_trees(repo)
    ensure_runtime_dirs(repo)
    profile = build_adaptation_profile(repo)
    path = runtime_root(repo) / ADAPTATION_FILENAME
    try:
        path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    except OSError as exc:
        print(
            f"FORGE RUNTIME ERROR: cannot write {path}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    cwd = Path.cwd()
    try:
        cwd_resolved = str(cwd.resolve())
    except OSError:
        cwd_resolved = str(cwd)
    writable = profile["writable_repo_root"]
    if cwd_resolved != writable and mount_writable_mismatch(cwd, Path(writable)):
        print(
            f"FORGE_ADAPT: using writable root {writable} (cwd alias may be read-only)",
            file=sys.stderr,
        )
    return profile


def mount_writable_mismatch(cwd: Path, writable: Path) -> bool:
    from scripts.shared.repo_paths import same_git_repo

    try:
        return same_git_repo(cwd, writable)
    except Exception:
        return False


def load_adaptation_profile(search_dir: Path | None = None) -> dict[str, Any] | None:
    from scripts.shared.runtime_layout import runtime_root

    repo = writable_repo_root(search_dir)
    path = runtime_root(repo) / ADAPTATION_FILENAME
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
