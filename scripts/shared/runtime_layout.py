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

CANONICAL_RUNTIME_PARTS = (".codex", "forge")  # legacy (pre-.forge primary)
LEGACY_FORGE_CODEX_RUNTIME_PARTS = (".codex", "forge-codex")  # older legacy name
LEGACY_RUNTIME_DIRNAME = ".forge"  # historical flat-root alias (same as primary today)
PRIMARY_RUNTIME_DIRNAME = ".forge"
EVALUATE_STATE_FILENAME = ".evaluate-state.json"
RUN_HISTORY_MAX_ENTRIES = 30


def detect_repo_root(start: Path | None = None) -> Path:
    """Detect the target repo root (writable, sandbox-safe)."""
    from scripts.shared.repo_paths import resolve_repo_root

    return resolve_repo_root(start or Path.cwd())


# Runtime defaults are anchored to the detected target repo root (cwd-based).
REPO_ROOT = detect_repo_root()


def blocked_runtime_anchor(base_dir: Path) -> bool:
    """True when Forge must not write under ``.codex/`` (file anchor or read-only)."""
    from scripts.shared.repo_paths import is_writable_dir

    anchor = base_dir / CANONICAL_RUNTIME_PARTS[0]
    if anchor.exists() and not anchor.is_dir():
        return True
    if anchor.is_dir() and not is_writable_dir(anchor):
        return True
    return False


def runtime_root(search_dir: Path | None = None) -> Path:
    """Return the repo-local Forge runtime root (always ``.forge/``)."""
    base_dir = search_dir or detect_repo_root()
    return base_dir / PRIMARY_RUNTIME_DIRNAME


def runtime_root_candidates(search_dir: Path | None = None) -> list[Path]:
    """Return runtime roots for reads: primary ``.forge/`` first, then legacy trees."""
    base_dir = search_dir or detect_repo_root()
    primary = base_dir / PRIMARY_RUNTIME_DIRNAME
    legacy_canonical = base_dir.joinpath(*CANONICAL_RUNTIME_PARTS)
    legacy_fc = base_dir.joinpath(*LEGACY_FORGE_CODEX_RUNTIME_PARTS)
    return _dedupe_runtime_roots([primary, legacy_canonical, legacy_fc])


def _dedupe_runtime_roots(roots: list[Path]) -> list[Path]:
    """Keep first occurrence of each existing runtime root."""
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir() and root != roots[0]:
            continue
        try:
            key = str(root.resolve())
        except OSError:
            key = str(root)
        if key in seen:
            continue
        seen.add(key)
        out.append(root)
    if not out:
        return [roots[0]]
    return out


def legacy_runtime_root(search_dir: Path | None = None) -> Path:
    """Former ``.codex/forge`` layout (read and migrate only)."""
    base_dir = search_dir or detect_repo_root()
    return base_dir.joinpath(*CANONICAL_RUNTIME_PARTS)


def legacy_flat_runtime_root(search_dir: Path | None = None) -> Path:
    """Flat ``.forge/`` at repo root (pre-session-directory layout)."""
    base_dir = search_dir or detect_repo_root()
    return base_dir / LEGACY_RUNTIME_DIRNAME


def repo_relative_path(path: Path, search_dir: Path | None = None) -> str:
    """Return a repo-relative path using forward slashes (for prompts and agents)."""
    base = (search_dir or detect_repo_root()).resolve()
    try:
        rel = path.resolve().relative_to(base)
    except ValueError:
        rel = path
    return rel.as_posix()


def runtime_dir_relative(search_dir: Path | None = None) -> str:
    """Repo-relative Forge runtime root (e.g. ``.forge``)."""
    return repo_relative_path(runtime_root(search_dir), search_dir)


def runtime_memory_dir_relative(search_dir: Path | None = None) -> str:
    """Repo-relative Forge memory directory (e.g. ``.forge/memory``)."""
    return repo_relative_path(runtime_memory_dir(search_dir), search_dir)


def template_runtime_variables(search_dir: Path | None = None) -> dict[str, str]:
    """Variables injected into workflow prompt templates."""
    return {
        "RUNTIME_DIR": runtime_dir_relative(search_dir),
        "MEMORY_DIR": runtime_memory_dir_relative(search_dir),
    }


def runtime_memory_dir(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / "memory"


def legacy_memory_dir(search_dir: Path | None = None) -> Path:
    return legacy_runtime_root(search_dir) / "memory"


def runtime_state_dir(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / "state"


def legacy_state_dir(search_dir: Path | None = None) -> Path:
    return legacy_flat_runtime_root(search_dir)


def runtime_adr_dir(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / "adr"


def runtime_backlog_path(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / "backlog.md"


def ensure_runtime_dirs(search_dir: Path | None = None) -> None:
    """Create the canonical runtime directory structure if missing."""
    runtime_state_dir(search_dir).mkdir(parents=True, exist_ok=True)
    runtime_memory_dir(search_dir).mkdir(parents=True, exist_ok=True)
    runtime_adr_dir(search_dir).mkdir(parents=True, exist_ok=True)
    from scripts.shared.session_store import sessions_root

    sessions_root(search_dir).mkdir(parents=True, exist_ok=True)


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
    from scripts.shared.skill_aliases import skill_name_variants

    for variant in skill_name_variants(skill_name):
        if name in {state_filename(variant), legacy_state_filename(variant)}:
            return True
        if name.startswith(f"{variant}-") and name.endswith(".json"):
            return True
    return False


def state_path_candidates(skill_name: str, search_dir: Path | None = None) -> list[Path]:
    """Return deduplicated candidate paths for a skill's state files."""
    cwd = search_dir or Path.cwd()
    dirs = [
        runtime_state_dir(cwd),
        legacy_state_dir(cwd),
        cwd,
    ]
    from scripts.shared.skill_aliases import skill_name_variants, skills_match
    from scripts.shared.session_store import iter_session_json_paths, sessions_root

    candidates: list[Path] = []
    seen: set[Path] = set()

    for variant in skill_name_variants(skill_name):
        for path in (
            runtime_state_path(variant, cwd),
            cwd / state_filename(variant),
            legacy_state_dir(cwd) / legacy_state_filename(variant),
            cwd / legacy_state_filename(variant),
        ):
            if path not in seen:
                candidates.append(path)
                seen.add(path)

        for dir_path in dirs:
            if not dir_path.exists():
                continue
            for path in sorted(dir_path.glob(f"{variant}-*.json")):
                if path not in seen:
                    candidates.append(path)
                    seen.add(path)

    root = sessions_root(cwd)
    if root.is_dir():
        for path in iter_session_json_paths(cwd, include_archive=False):
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if skills_match(str(state.get("skill_name", "")), skill_name) and path not in seen:
                candidates.append(path)
                seen.add(path)

    return candidates


# Private alias used by orchestrator and session_hygiene
_state_path_candidates = state_path_candidates
_is_skill_state_filename = is_skill_state_filename


def save_state(state: SkillState, path: Path, *, label: str | None = None) -> None:
    """Write state to JSON file atomically."""
    from scripts.shared.session_store import (
        enrich_state_dict_for_save,
        ensure_writable_state_path,
        is_session_state_path,
        session_id_from_state_path,
        update_index_for_session,
    )

    path = ensure_writable_state_path(path)
    state.last_touched_at = now_iso()
    sid_from_path = session_id_from_state_path(path)
    if sid_from_path:
        state.session_id = sid_from_path
    elif not state.session_id:
        state.session_id = str(uuid4())

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = enrich_state_dict_for_save(state, path, label=label)
    content = json.dumps(payload, indent=2, default=str)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.close(fd)
        Path(tmp).write_text(content, encoding="utf-8")
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    if is_session_state_path(path):
        update_index_for_session(
            state, path, label=label, search_dir=_repo_root_for_path(path)
        )
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
    data = json.loads(path.read_text(encoding="utf-8"))
    if "skill_name" not in data:
        raise KeyError("State file missing required field: skill_name")
    return SkillState.from_dict(data)


def clear_state_file(path: Path) -> None:
    """Remove a state file; archive session directory when applicable."""
    from scripts.shared.session_store import (
        archive_session_dir,
        is_session_state_path,
        session_id_from_state_path,
    )

    if is_session_state_path(path):
        sid = session_id_from_state_path(path)
        if sid:
            archive_session_dir(sid, search_dir=_repo_root_for_path(path))
            return
    path.unlink(missing_ok=True)


def _repo_root_for_path(path: Path) -> Path | None:
    """Best-effort repo root from a state path (``.../repo/.codex/forge/...``)."""
    parts = path.resolve().parts
    for i, part in enumerate(parts):
        if part in (".codex", LEGACY_RUNTIME_DIRNAME) and i > 0:
            return Path(*parts[:i])
    return None


def find_state_file(
    skill_name: str,
    search_dir: Path | None = None,
    *,
    include_completed: bool = False,
    include_stale: bool = False,
) -> Path | None:
    """Find the best state file for a skill."""
    from scripts.shared.session_store import list_active_sessions

    from scripts.shared.skill_aliases import skills_match

    session_matches = [
        s.path
        for s in list_active_sessions(search_dir)
        if skills_match(s.skill, skill_name)
    ]
    if session_matches:
        return session_matches[0]

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
        from scripts.shared.skill_aliases import skills_match

        if not skills_match(state.skill_name, skill_name):
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
