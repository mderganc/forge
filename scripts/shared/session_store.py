"""Session-per-directory workflow state (parallel-first, minimal index).

Layout under ``.codex/forge/sessions/``::

    {session_id}/
        session.json    # SkillState + index fields (v, label, status)
        handoff.md      # per-session handoff
        sidecars/       # optional step artifacts
    index.json          # fast listing registry
    _archive/{session_id}/  # completed or auto-cleaned sessions
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.shared.runtime_layout import detect_repo_root, runtime_root
from scripts.shared.skill_state import SkillState
from scripts.shared.state_lifecycle import (
    is_state_effectively_complete,
    is_state_stale,
    now_iso,
    parse_iso_timestamp,
)

SESSION_SCHEMA_VERSION = 1
SESSIONS_DIRNAME = "sessions"
ARCHIVE_DIRNAME = "_archive"
INDEX_FILENAME = "index.json"
SESSION_JSON = "session.json"
SIDECARS_DIRNAME = "sidecars"
HANDOFF_FILENAME = "handoff.md"

RESERVED_SESSION_DIRS = frozenset({ARCHIVE_DIRNAME})


def skip_session_cleanup() -> bool:
    v = os.environ.get("FORGE_SKIP_SESSION_CLEANUP", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def session_max_age_days() -> float:
    raw = os.environ.get("FORGE_SESSION_MAX_AGE_DAYS", "7").strip()
    try:
        days = float(raw)
    except ValueError:
        days = 7.0
    if days <= 0:
        days = 7.0
    return days


def sessions_root(search_dir: Path | None = None) -> Path:
    return runtime_root(search_dir) / SESSIONS_DIRNAME


def sessions_archive_root(search_dir: Path | None = None) -> Path:
    return sessions_root(search_dir) / ARCHIVE_DIRNAME


def index_path(search_dir: Path | None = None) -> Path:
    return sessions_root(search_dir) / INDEX_FILENAME


def session_directory(session_id: str, search_dir: Path | None = None) -> Path:
    return sessions_root(search_dir) / session_id


def session_json_path(session_id: str, search_dir: Path | None = None) -> Path:
    return session_directory(session_id, search_dir) / SESSION_JSON


def session_handoff_path(session_id: str, search_dir: Path | None = None) -> Path:
    return session_directory(session_id, search_dir) / HANDOFF_FILENAME


def session_sidecars_dir(session_id: str, search_dir: Path | None = None) -> Path:
    return session_directory(session_id, search_dir) / SIDECARS_DIRNAME


def is_session_state_path(path: Path) -> bool:
    """True when ``path`` is ``.../sessions/<id>/session.json``."""
    try:
        return path.name == SESSION_JSON and path.parent.parent.name == SESSIONS_DIRNAME
    except (IndexError, AttributeError):
        return False


def session_id_from_state_path(path: Path) -> str | None:
    if not is_session_state_path(path):
        return None
    return path.parent.name


def ensure_writable_state_path(path: Path, search_dir: Path | None = None) -> Path:
    """Return ``path`` or relocate a session file to the active writable runtime root."""
    import shutil

    from scripts.shared.repo_paths import is_writable_dir
    from scripts.shared.runtime_layout import runtime_root

    repo = search_dir or _repo_root_for_state_path(path) or detect_repo_root()

    if is_session_state_path(path):
        sid = session_id_from_state_path(path)
        if sid:
            active = session_json_path(sid, repo)
            current_root = _runtime_root_for_state_path(path)
            target_root = runtime_root(repo)
            needs_relocate = (
                current_root is not None
                and current_root.resolve() != target_root.resolve()
            ) or (path.is_file() and not is_writable_dir(path.parent))
            if needs_relocate:
                active.parent.mkdir(parents=True, exist_ok=True)
                if path.is_file() and not active.is_file():
                    shutil.copy2(path, active)
                return active

    parent = path.parent
    if not path.is_file():
        parent.mkdir(parents=True, exist_ok=True)
        if is_writable_dir(parent):
            return path
    elif is_writable_dir(parent):
        return path
    return path


def _runtime_root_for_state_path(path: Path) -> Path | None:
    """Return ``.../.codex/forge`` (or ``.forge``) for a ``session.json`` path."""
    parts = path.resolve().parts
    for i, part in enumerate(parts):
        if part == SESSIONS_DIRNAME and i >= 1:
            return Path(*parts[:i])
    return None


def _repo_root_for_state_path(path: Path) -> Path | None:
    parts = path.resolve().parts
    for i, part in enumerate(parts):
        if part in (".codex", ".forge") and i > 0:
            return Path(*parts[:i])
    return None


def _new_session_id(search_dir: Path | None = None) -> str:
    root = sessions_root(search_dir)
    for _ in range(32):
        sid = secrets.token_hex(3)
        if sid not in RESERVED_SESSION_DIRS and not (root / sid).exists():
            return sid
    raise RuntimeError("Unable to allocate unique session id")


def _default_label(skill: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{skill}-{stamp}"


def _session_age_seconds(data: dict[str, Any], path: Path) -> float:
    touched = (
        parse_iso_timestamp(data.get("last_touched_at"))
        or parse_iso_timestamp(data.get("started_at"))
        or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    )
    return (datetime.now(timezone.utc) - touched).total_seconds()


def _format_age(seconds: float) -> str:
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h"
    return f"{int(seconds // 86400)}d"


@dataclass
class SessionInfo:
    session_id: str
    skill: str
    label: str
    current_step: int
    last_completed_step: int
    max_step: int
    status: str
    path: Path
    started_at: str | None = None
    last_touched_at: str | None = None
    is_complete: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "skill": self.skill,
            "label": self.label,
            "current_step": self.current_step,
            "last_completed_step": self.last_completed_step,
            "max_step": self.max_step,
            "status": self.status,
            "path": str(self.path),
            "started_at": self.started_at,
            "last_touched_at": self.last_touched_at,
            "is_complete": self.is_complete,
        }


def load_index(search_dir: Path | None = None) -> dict[str, Any]:
    path = index_path(search_dir)
    if not path.is_file():
        return {"v": 1, "active": [], "archived": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"v": 1, "active": [], "archived": []}
    if not isinstance(data, dict):
        return {"v": 1, "active": [], "archived": []}
    data.setdefault("v", 1)
    data.setdefault("active", [])
    data.setdefault("archived", [])
    return data


def save_index(data: dict[str, Any], search_dir: Path | None = None) -> None:
    root = sessions_root(search_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = index_path(search_dir)
    content = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=root, suffix=".tmp")
    try:
        os.close(fd)
        Path(tmp).write_text(content, encoding="utf-8")
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _index_entry_from_state(state: SkillState, path: Path, *, label: str, status: str) -> dict[str, Any]:
    sid = state.session_id or session_id_from_state_path(path) or path.parent.name
    return {
        "session_id": sid,
        "skill": state.skill_name,
        "label": label,
        "current_step": state.current_step,
        "last_completed_step": state.last_completed_step,
        "max_step": state.max_step,
        "status": status,
        "path": str(path.resolve()),
        "started_at": state.started_at,
        "last_touched_at": state.last_touched_at,
    }


def update_index_for_session(
    state: SkillState,
    path: Path,
    *,
    label: str | None = None,
    status: str | None = None,
    search_dir: Path | None = None,
) -> None:
    if not is_session_state_path(path):
        return
    sid = state.session_id or session_id_from_state_path(path) or path.parent.name
    data = load_index(search_dir)
    active = [e for e in data.get("active", []) if e.get("session_id") != sid]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    entry = _index_entry_from_state(
        state,
        path,
        label=label or raw.get("label") or _default_label(state.skill_name),
        status=status or raw.get("status") or "active",
    )
    if is_state_effectively_complete(state):
        entry["status"] = "completed"
        data["archived"] = [e for e in data.get("archived", []) if e.get("session_id") != sid]
        data["archived"].append({**entry, "archived_at": now_iso()})
    else:
        active.append(entry)
    data["active"] = active
    save_index(data, search_dir)


def remove_from_active_index(session_id: str, search_dir: Path | None = None) -> None:
    data = load_index(search_dir)
    data["active"] = [e for e in data.get("active", []) if e.get("session_id") != session_id]
    save_index(data, search_dir)


def _read_session_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def session_info_from_path(path: Path) -> SessionInfo | None:
    data = _read_session_file(path)
    if not data or "skill_name" not in data:
        return None
    sid = data.get("session_id") or session_id_from_state_path(path) or path.parent.name
    complete = is_state_effectively_complete(SkillState.from_dict(data))
    return SessionInfo(
        session_id=sid,
        skill=data["skill_name"],
        label=data.get("label") or _default_label(data["skill_name"]),
        current_step=int(data.get("current_step", 0)),
        last_completed_step=int(data.get("last_completed_step", 0)),
        max_step=int(data.get("max_step", 6)),
        status=data.get("status") or ("completed" if complete else "active"),
        path=path,
        started_at=data.get("started_at"),
        last_touched_at=data.get("last_touched_at"),
        is_complete=complete,
    )


def iter_session_json_paths(search_dir: Path | None = None, *, include_archive: bool = False) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for root in all_sessions_roots(search_dir):
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name in RESERVED_SESSION_DIRS:
                continue
            candidate = child / SESSION_JSON
            if candidate.is_file():
                key = str(candidate.resolve())
                if key not in seen:
                    seen.add(key)
                    paths.append(candidate)
        if include_archive:
            archive = root / ARCHIVE_DIRNAME
            if archive.is_dir():
                for child in sorted(archive.iterdir()):
                    if child.is_dir():
                        candidate = child / SESSION_JSON
                        if candidate.is_file():
                            key = str(candidate.resolve())
                            if key not in seen:
                                seen.add(key)
                                paths.append(candidate)
    return paths


def all_sessions_roots(search_dir: Path | None = None) -> list[Path]:
    """Return every ``sessions/`` directory that may hold workflow state."""
    from scripts.shared.runtime_layout import runtime_root_candidates

    roots: list[Path] = []
    seen: set[str] = set()
    for runtime in runtime_root_candidates(search_dir):
        candidate = runtime / SESSIONS_DIRNAME
        try:
            key = str(candidate.resolve())
        except OSError:
            key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        roots.append(candidate)
    return roots


def list_active_sessions(search_dir: Path | None = None) -> list[SessionInfo]:
    """Active, non-stale sessions under ``sessions/`` (not ``_archive/``)."""
    from scripts.shared.runtime_layout import runtime_root

    repo = search_dir or detect_repo_root()
    active_root = runtime_root(repo)
    sessions: list[SessionInfo] = []
    for path in iter_session_json_paths(search_dir, include_archive=False):
        info = session_info_from_path(path)
        if info is None or info.is_complete:
            continue
        try:
            state = SkillState.from_dict(_read_session_file(path) or {})
        except Exception:
            continue
        if is_state_stale(state, path):
            continue
        sessions.append(info)

    by_key: dict[tuple[str, str], SessionInfo] = {}
    for info in sessions:
        key = (info.skill, info.path.parent.name)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = info
            continue
        try:
            under_active = info.path.resolve().is_relative_to(active_root.resolve())
        except (ValueError, OSError):
            under_active = str(active_root) in str(info.path)
        if under_active:
            by_key[key] = info

    sessions = list(by_key.values())
    sessions.sort(key=lambda s: s.last_touched_at or s.started_at or "", reverse=True)
    return sessions


def create_session(
    skill: str,
    *,
    label: str | None = None,
    max_step: int = 6,
    search_dir: Path | None = None,
) -> tuple[str, Path]:
    """Create a new session directory and empty ``session.json`` shell."""
    from scripts.shared.runtime_adaptation import adapt_runtime, writable_repo_root

    repo = writable_repo_root(search_dir)
    adapt_runtime(repo)
    migrate_legacy_state_files(repo)
    sid = _new_session_id(search_dir)
    session_label = label or _default_label(skill)
    session_dir = session_directory(sid, search_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    session_sidecars_dir(sid, search_dir).mkdir(exist_ok=True)
    path = session_dir / SESSION_JSON
    return sid, path


def enrich_state_dict_for_save(state: SkillState, path: Path, *, label: str | None = None) -> dict[str, Any]:
    """Merge SkillState with session index fields for ``session.json``."""
    payload = state.to_dict()
    if is_session_state_path(path):
        sid = state.session_id or session_id_from_state_path(path) or path.parent.name
        payload["v"] = SESSION_SCHEMA_VERSION
        payload["session_id"] = sid
        existing_label: str | None = None
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                existing_label = raw.get("label")
            except (OSError, json.JSONDecodeError):
                pass
        payload.setdefault(
            "label",
            label or existing_label or _default_label(state.skill_name),
        )
        if is_state_effectively_complete(state):
            payload["status"] = "completed"
        else:
            payload.setdefault("status", "active")
    return payload


def archive_session_dir(
    session_id: str,
    search_dir: Path | None = None,
    *,
    reason: str = "archived",
) -> Path | None:
    """Move ``sessions/{id}/`` to ``sessions/_archive/{id}/``."""
    src = session_directory(session_id, search_dir)
    if not src.is_dir():
        return None
    archive_root = sessions_archive_root(search_dir)
    archive_root.mkdir(parents=True, exist_ok=True)
    dest = archive_root / session_id
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    shutil.move(str(src), str(dest))
    remove_from_active_index(session_id, search_dir)
    return dest


def delete_archived_session(session_id: str, search_dir: Path | None = None) -> bool:
    dest = sessions_archive_root(search_dir) / session_id
    if not dest.is_dir():
        return False
    shutil.rmtree(dest, ignore_errors=True)
    data = load_index(search_dir)
    data["archived"] = [e for e in data.get("archived", []) if e.get("session_id") != session_id]
    save_index(data, search_dir)
    return True


def auto_clean_expired_sessions(
    *,
    search_dir: Path | None = None,
    max_age_days: float | None = None,
    dry_run: bool = False,
) -> list[tuple[str, str, str]]:
    """Archive active sessions older than max age; delete archived sessions past max age.

    Returns list of ``(session_id, skill, reason)`` for audit lines.
    """
    if skip_session_cleanup():
        return []

    max_days = max_age_days if max_age_days is not None else session_max_age_days()
    max_seconds = max_days * 86400.0
    cleaned: list[tuple[str, str, str]] = []
    cwd = search_dir or detect_repo_root()

    for path in iter_session_json_paths(cwd, include_archive=False):
        data = _read_session_file(path)
        if not data:
            continue
        age = _session_age_seconds(data, path)
        if age <= max_seconds:
            continue
        sid = data.get("session_id") or path.parent.name
        skill = data.get("skill_name", "?")
        label = data.get("label", "")
        reason = f'untouched {_format_age(age)} (> {int(max_days)}d limit)'
        if not dry_run:
            archive_session_dir(sid, cwd, reason=reason)
        cleaned.append((sid, skill, f'{label!r} — {reason}' if label else reason))

    archive_root = sessions_archive_root(cwd)
    if archive_root.is_dir():
        for child in sorted(archive_root.iterdir()):
            if not child.is_dir():
                continue
            json_path = child / SESSION_JSON
            data = _read_session_file(json_path) if json_path.is_file() else None
            skill = (data or {}).get("skill_name", "?")
            sid = child.name
            archived_at = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc)
            age = (datetime.now(timezone.utc) - archived_at).total_seconds()
            if age <= max_seconds:
                continue
            reason = f'archive age {_format_age(age)} (> {int(max_days)}d limit)'
            if not dry_run:
                delete_archived_session(sid, cwd)
            cleaned.append((sid, skill, reason))

    return cleaned


def print_auto_cleaned_audit(cleaned: list[tuple[str, str, str]]) -> None:
    for sid, skill, reason in cleaned:
        print(f'AUTO-CLEANED: {sid} ({skill}, {reason})', file=sys.stderr)


def run_session_cleanup(search_dir: Path | None = None, *, dry_run: bool = False) -> list[tuple[str, str, str]]:
    cleaned = auto_clean_expired_sessions(search_dir=search_dir, dry_run=dry_run)
    if not dry_run:
        print_auto_cleaned_audit(cleaned)
    return cleaned


def migrate_legacy_state_files(search_dir: Path | None = None) -> list[str]:
    """One-time migration of flat ``state/{skill}.json`` files into session dirs."""
    from scripts.shared.runtime_layout import (
        legacy_state_dir,
        load_state,
        runtime_state_dir,
        state_path_candidates,
    )

    cwd = search_dir or detect_repo_root()
    marker = sessions_root(cwd) / ".migrated-from-legacy"
    if marker.is_file():
        return []

    migrated: list[str] = []
    seen: set[Path] = set()
    skills = [
        "sketch", "develop", "plan", "implement", "code-review", "test", "diagnose", "takeover",
    ]

    root = sessions_root(cwd)
    root.mkdir(parents=True, exist_ok=True)

    for skill in skills:
        for candidate in state_path_candidates(skill, cwd):
            if candidate in seen or not candidate.exists():
                continue
            seen.add(candidate)
            if is_session_state_path(candidate):
                continue
            try:
                state = load_state(candidate)
            except Exception:
                continue
            sid = _new_session_id(cwd)
            label = candidate.stem if candidate.stem != skill else _default_label(skill)
            session_dir = root / sid
            session_dir.mkdir(parents=True, exist_ok=True)
            session_sidecars_dir(sid, cwd).mkdir(exist_ok=True)
            path = session_dir / SESSION_JSON
            state.session_id = sid
            payload = enrich_state_dict_for_save(state, path, label=label)
            path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
            update_index_for_session(state, path, label=label, search_dir=cwd)
            candidate.unlink(missing_ok=True)
            migrated.append(str(candidate))

    if migrated or root.is_dir():
        marker.write_text(now_iso() + "\n", encoding="utf-8")
    return migrated


def format_sessions_table(sessions: list[SessionInfo]) -> str:
    if not sessions:
        return "(none)"
    lines = [
        f"{'ID':<8} {'SKILL':<12} {'STEP':<8} {'LABEL':<22} {'AGE':<6}",
    ]
    now = datetime.now(timezone.utc)
    for s in sessions:
        ref = parse_iso_timestamp(s.last_touched_at) or parse_iso_timestamp(s.started_at)
        age = _format_age((now - ref).total_seconds()) if ref else "?"
        step = f"{s.current_step}/{s.max_step}"
        label = (s.label[:20] + "..") if len(s.label) > 22 else s.label
        lines.append(f"{s.session_id:<8} {s.skill:<12} {step:<8} {label:<22} {age:<6}")
    return "\n".join(lines)


def resolve_session_for_step(
    skill_name: str,
    step: int,
    *,
    session_id: str | None = None,
    state_file: str | None = None,
    search_dir: Path | None = None,
) -> Path:
    """Resolve ``session.json`` path for a skill step invocation."""
    repo_root = detect_repo_root(search_dir).resolve()

    if session_id:
        path = session_json_path(session_id, repo_root)
        if not path.is_file():
            sys.exit(f"ERROR: session not found: {session_id}")
        try:
            state = SkillState.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            sys.exit(f"ERROR: unreadable session {session_id}: {exc}")
        from scripts.shared.skill_aliases import skills_match

        if not skills_match(state.skill_name, skill_name):
            sys.exit(
                f"ERROR: session {session_id} is skill {state.skill_name!r}, "
                f"not {skill_name!r}"
            )
        return path

    if state_file:
        from scripts.shared.repo_paths import equivalent_path_in_repo, same_git_repo

        sp = equivalent_path_in_repo(Path(state_file), repo_root)
        try:
            sp.relative_to(repo_root)
        except ValueError:
            if not same_git_repo(sp, repo_root):
                sys.exit(f"ERROR: --state path is outside the repository: {state_file}")
            sp = equivalent_path_in_repo(sp, repo_root)
        if not sp.is_file():
            sys.exit(f"ERROR: state file not found: {state_file}")
        return sp

    if step == 1:
        sys.exit(
            "ERROR: step 1 must create a session via orchestrator resolve_step1_state_path"
        )

    from scripts.shared.skill_aliases import skills_match

    active = [s for s in list_active_sessions(repo_root) if skills_match(s.skill, skill_name)]
    if len(active) == 1:
        return active[0].path
    if len(active) > 1:
        print(format_sessions_table(active), file=sys.stderr)
        sys.exit(
            f"ERROR: {len(active)} active {skill_name} sessions — "
            f"use --session <id> (see table above)"
        )

    from scripts.shared.runtime_layout import find_state_file

    legacy = find_state_file(skill_name, repo_root)
    if legacy is not None:
        return legacy
    sys.exit(f"ERROR: no active session for {skill_name}; start with --step 1")
