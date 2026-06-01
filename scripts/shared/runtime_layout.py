"""Forge runtime directory layout and skill state file persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from scripts.shared.skill_state import SkillState
from scripts.shared.state_lifecycle import (
    is_state_effectively_complete,
    is_state_stale,
    now_iso,
)

CANONICAL_RUNTIME_PARTS = (".codex", "forge")
LEGACY_FORGE_CODEX_RUNTIME_PARTS = (".codex", "forge-codex")
LEGACY_RUNTIME_DIRNAME = ".forge"
EVALUATE_STATE_FILENAME = ".evaluate-state.json"
RUN_HISTORY_MAX_ENTRIES = 30


def detect_repo_root(start: Path | None = None) -> Path:
    """Detect the target repo root (writable, sandbox-safe)."""
    from scripts.shared.repo_paths import resolve_repo_root

    return resolve_repo_root(start or Path.cwd())


# Runtime defaults are anchored to the detected target repo root (cwd-based).
REPO_ROOT = detect_repo_root()


def blocked_runtime_anchor(base_dir: Path) -> bool:
    """True when the canonical `.codex` anchor exists but is not a directory."""
    anchor = base_dir / CANONICAL_RUNTIME_PARTS[0]
    return anchor.exists() and not anchor.is_dir()


def runtime_root(search_dir: Path | None = None) -> Path:
    """Return the runtime root for Forge artifacts under the target repo."""
    base_dir = search_dir or detect_repo_root()
    if blocked_runtime_anchor(base_dir):
        return base_dir / LEGACY_RUNTIME_DIRNAME
    canonical = base_dir.joinpath(*CANONICAL_RUNTIME_PARTS)
    legacy_fc = base_dir.joinpath(*LEGACY_FORGE_CODEX_RUNTIME_PARTS)
    if legacy_fc.is_dir() and not canonical.exists():
        return legacy_fc
    return canonical


def legacy_runtime_root(search_dir: Path | None = None) -> Path:
    """Return the legacy runtime root used by the original copied workflow."""
    base_dir = search_dir or detect_repo_root()
    return base_dir / LEGACY_RUNTIME_DIRNAME


def runtime_memory_dir(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / "memory"


def legacy_memory_dir(search_dir: Path | None = None) -> Path:
    return legacy_runtime_root(search_dir) / "memory"


def runtime_state_dir(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / "state"


def legacy_state_dir(search_dir: Path | None = None) -> Path:
    return legacy_runtime_root(search_dir)


def runtime_adr_dir(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / "adr"


def runtime_backlog_path(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / "backlog.md"


def ensure_runtime_dirs(search_dir: Path | None = None) -> None:
    """Create the canonical runtime directory structure if missing."""
    runtime_state_dir(search_dir).mkdir(parents=True, exist_ok=True)
    runtime_memory_dir(search_dir).mkdir(parents=True, exist_ok=True)
    runtime_adr_dir(search_dir).mkdir(parents=True, exist_ok=True)


def state_filename(skill_name: str) -> str:
    return f"{skill_name}.json"


def legacy_state_filename(skill_name: str) -> str:
    return f".forge-{skill_name}-state.json"


def runtime_state_path(skill_name: str, search_dir: Path | None = None) -> Path:
    return runtime_state_dir(search_dir) / state_filename(skill_name)


def is_skill_state_filename(name: str, skill_name: str) -> bool:
    """True when ``name`` is a valid state filename for ``skill_name``."""
    if skill_name == "evaluate":
        return name == EVALUATE_STATE_FILENAME or (
            name.startswith(".evaluate-state-") and name.endswith(".json")
        )
    if name in {state_filename(skill_name), legacy_state_filename(skill_name)}:
        return True
    return name.startswith(f"{skill_name}-") and name.endswith(".json")


def state_path_candidates(skill_name: str, search_dir: Path | None = None) -> list[Path]:
    """Return deduplicated candidate paths for a skill's state files."""
    cwd = search_dir or Path.cwd()
    dirs = [
        runtime_state_dir(cwd),
        legacy_state_dir(cwd),
        cwd,
    ]
    candidates: list[Path] = []
    seen: set[Path] = set()

    for path in (
        runtime_state_path(skill_name, cwd),
        cwd / state_filename(skill_name),
        legacy_state_dir(cwd) / legacy_state_filename(skill_name),
        cwd / legacy_state_filename(skill_name),
    ):
        if path not in seen:
            candidates.append(path)
            seen.add(path)

    for dir_path in dirs:
        if not dir_path.exists():
            continue
        for path in sorted(dir_path.glob(f"{skill_name}-*.json")):
            if path not in seen:
                candidates.append(path)
                seen.add(path)

    return candidates


# Private alias used by orchestrator and session_hygiene
_state_path_candidates = state_path_candidates
_is_skill_state_filename = is_skill_state_filename


def save_state(state: SkillState, path: Path) -> None:
    """Write state to JSON file atomically."""
    state.last_touched_at = now_iso()
    if not state.session_id:
        state.session_id = str(uuid4())
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(state.to_dict(), indent=2)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.close(fd)
        Path(tmp).write_text(content)
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    try:
        from scripts.shared import resume_context

        resume_context.write_skill_resume_snapshot(state, path)
    except Exception:
        pass
    try:
        from scripts.shared import memory_synthesis

        memory_synthesis.write_memory_synthesis_from_skill_state(state, path)
    except Exception:
        pass


def load_state(path: Path) -> SkillState:
    """Load state from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"No state file at {path}")
    data = json.loads(path.read_text())
    if "skill_name" not in data:
        raise KeyError("State file missing required field: skill_name")
    return SkillState.from_dict(data)


def clear_state_file(path: Path) -> None:
    """Remove a state file if it exists."""
    path.unlink(missing_ok=True)


def find_state_file(
    skill_name: str,
    search_dir: Path | None = None,
    *,
    include_completed: bool = False,
    include_stale: bool = False,
) -> Path | None:
    """Find the best state file for a skill."""
    active_fresh: list[Path] = []
    active_stale: list[Path] = []
    complete: list[Path] = []

    for candidate in state_path_candidates(skill_name, search_dir):
        if not candidate.exists():
            continue
        try:
            state = load_state(candidate)
        except Exception:
            continue
        if state.skill_name != skill_name:
            continue
        if is_state_effectively_complete(state):
            complete.append(candidate)
        elif is_state_stale(state, candidate):
            active_stale.append(candidate)
        else:
            active_fresh.append(candidate)

    if active_fresh:
        return max(active_fresh, key=lambda p: p.stat().st_mtime)
    if include_stale and active_stale:
        return max(active_stale, key=lambda p: p.stat().st_mtime)
    if include_completed and complete:
        return max(complete, key=lambda p: p.stat().st_mtime)
    return None


# Backward-compatible private names
_detect_repo_root = detect_repo_root
_blocked_runtime_anchor = blocked_runtime_anchor
