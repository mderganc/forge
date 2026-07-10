"""Runtime adaptation: writable repo root, legacy migration, profile cache."""

from __future__ import annotations

import json
import os
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
# Prefer copying known runtime subtrees first; remaining top-level items follow.
MIGRATE_SUBDIRS = ("sessions", "memory", "state", "studio", "adr")
KEEP_LEGACY_ENV = "FORGE_KEEP_LEGACY_RUNTIME"


def writable_repo_root(search_dir: Path | None = None) -> Path:
    """Return the writable git root for Forge writes (no read-only alias)."""
    from scripts.shared.repo_paths import resolve_repo_root

    start = search_dir or Path.cwd()
    return resolve_repo_root(start)


def _legacy_runtime_sources(repo: Path) -> list[Path]:
    return [repo.joinpath(*parts) for parts in LEGACY_RUNTIME_SOURCES]


def _copy_item(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def _merge_tree_into(src: Path, dst: Path) -> list[str]:
    """Copy missing items from ``src`` into ``dst``. Returns relative paths copied."""
    copied: list[str] = []
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir(), key=lambda p: p.name):
        dst_item = dst / item.name
        if item.is_dir():
            if not dst_item.exists():
                shutil.copytree(item, dst_item)
                copied.append(item.name)
            else:
                for nested in _merge_tree_into(item, dst_item):
                    copied.append(f"{item.name}/{nested}")
        elif not dst_item.exists():
            shutil.copy2(item, dst_item)
            copied.append(item.name)
    return copied


def archive_legacy_runtime_trees(
    search_dir: Path | None = None,
    *,
    force: bool = False,
) -> list[dict[str, str]]:
    """Move ``.codex/forge*`` trees under ``.forge/_archive/`` after migration.

    Set ``FORGE_KEEP_LEGACY_RUNTIME=1`` to leave legacy trees in place (tests / debug).
    """
    if not force and os.environ.get(KEEP_LEGACY_ENV, "").strip() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return []

    repo = writable_repo_root(search_dir)
    target = repo / ".forge"
    if not target.is_dir():
        return []

    archive_root = target / "_archive"
    archived: list[dict[str, str]] = []
    stamp = now_iso().replace(":", "").replace("+", "")

    for src in _legacy_runtime_sources(repo):
        if not src.is_dir():
            continue
        archive_root.mkdir(parents=True, exist_ok=True)
        dest = archive_root / f"legacy-{src.name}-{stamp}"
        # Avoid clobbering an existing archive slot (same-second double call).
        n = 0
        while dest.exists():
            n += 1
            dest = archive_root / f"legacy-{src.name}-{stamp}-{n}"
        try:
            shutil.move(str(src), str(dest))
        except OSError as exc:
            print(
                f"FORGE_ADAPT: could not archive {src}: {exc}",
                file=sys.stderr,
            )
            continue
        archived.append({"from": str(src), "to": str(dest)})
        print(
            f"FORGE_ADAPT: archived legacy runtime {src} → {dest}",
            file=sys.stderr,
        )
    return archived


def migrate_legacy_runtime_trees(search_dir: Path | None = None) -> dict[str, Any]:
    """Copy ``.codex/forge*`` trees into ``.forge/``, then archive the sources."""
    repo = writable_repo_root(search_dir)
    target = repo / ".forge"
    target.mkdir(parents=True, exist_ok=True)
    state_dir = target / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    audit: dict[str, Any] = {
        "migrated_at": now_iso(),
        "target": str(target),
        "sources": [],
        "archived": [],
    }

    for src in _legacy_runtime_sources(repo):
        if not src.is_dir():
            continue
        entry: dict[str, Any] = {"path": str(src), "copied": []}
        # Prefer known subdirs for stable relative paths in the audit log.
        for sub in MIGRATE_SUBDIRS:
            src_sub = src / sub
            if not src_sub.is_dir():
                continue
            for rel in _merge_tree_into(src_sub, target / sub):
                entry["copied"].append(f"{sub}/{rel}")
        # Copy any remaining top-level items (e.g. backlog.md).
        for item in sorted(src.iterdir(), key=lambda p: p.name):
            if item.name in MIGRATE_SUBDIRS:
                continue
            dst_item = target / item.name
            if dst_item.exists():
                continue
            _copy_item(item, dst_item)
            entry["copied"].append(item.name)
        if entry["copied"]:
            audit["sources"].append(entry)

    audit["archived"] = archive_legacy_runtime_trees(repo)

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
