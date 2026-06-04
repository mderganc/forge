"""Cross-session detection, auto-close, and leak hints for Forge workflows."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.shared.pipeline import PIPELINE_FLOW, PIPELINE_SKILL_INDEX
from scripts.shared.runtime_layout import (
    EVALUATE_STATE_FILENAME,
    clear_state_file,
    detect_repo_root,
    legacy_memory_dir,
    legacy_runtime_root,
    load_state,
    runtime_memory_dir,
    runtime_root,
    runtime_state_dir,
    state_path_candidates,
)
from scripts.shared.skill_state import SkillState
from scripts.shared.state_lifecycle import (
    is_evaluate_state_stale,
    is_state_effectively_complete,
    is_state_stale,
    parse_iso_timestamp,
)

KNOWN_SKILLS = [
    "develop",
    "plan",
    "implement",
    "code-review",
    "test",
    "diagnose",
    "evaluate",
    "iterate",
]

PIPELINE_SKILLS = {
    "develop",
    "plan",
    "implement",
    "code-review",
    "test",
    "diagnose",
}


def _scan_evaluate_sessions(cwd: Path) -> list[dict]:
    """Find active evaluate sessions."""
    sessions: list[dict] = []

    candidates: list[Path] = []
    for dir_path in (cwd, runtime_root(cwd), legacy_runtime_root(cwd)):
        if not dir_path.exists():
            continue
        for candidate in [
            dir_path / EVALUATE_STATE_FILENAME,
            *dir_path.glob(".evaluate-state-*.json"),
        ]:
            if candidate.exists():
                candidates.append(candidate)

    docs_dir = cwd / "docs"
    if docs_dir.is_dir():
        candidates.extend(docs_dir.rglob(".evaluate-state.json"))
        candidates.extend(docs_dir.rglob(".evaluate-state-*.json"))

    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)

        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if is_evaluate_state_stale(data, path):
            continue

        mode = data.get("mode") or "pre"
        if mode == "review":
            max_step = 5
        elif mode == "post":
            max_step = 8
        else:
            max_step = 7
        sessions.append({
            "skill": "evaluate",
            "path": path,
            "current_step": data.get("current_step", 1),
            "last_completed_step": data.get("last_completed_step", 0),
            "max_step": max_step,
            "started_at": None,
            "completed_at": None,
            "is_complete": False,
        })
    return sessions


def detect_active_sessions(search_dir: Path | None = None) -> list[dict]:
    """Scan for all active skill state files (session dirs + legacy json)."""
    cwd = search_dir or detect_repo_root()
    sessions: list[dict] = []
    seen_paths: set[Path] = set()

    from scripts.shared.session_store import list_active_sessions as list_session_store

    for info in list_session_store(cwd):
        resolved = info.path.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        sessions.append({
            "skill": info.skill,
            "path": info.path,
            "session_id": info.session_id,
            "label": info.label,
            "current_step": info.current_step,
            "last_completed_step": info.last_completed_step,
            "max_step": info.max_step,
            "started_at": info.started_at,
            "completed_at": None,
            "is_complete": False,
        })

    for skill in KNOWN_SKILLS:
        if skill == "evaluate":
            continue

        for candidate in state_path_candidates(skill, cwd):
            if not candidate.exists() or candidate in seen_paths:
                continue
            seen_paths.add(candidate)

            try:
                state = load_state(candidate)
            except Exception:
                continue

            if state.skill_name != skill:
                continue
            if is_state_effectively_complete(state):
                continue
            if is_state_stale(state, candidate):
                continue

            from scripts.shared.session_store import session_id_from_state_path

            sessions.append({
                "skill": state.skill_name,
                "path": candidate,
                "session_id": state.session_id or session_id_from_state_path(candidate),
                "label": None,
                "current_step": state.current_step,
                "last_completed_step": state.last_completed_step,
                "max_step": state.max_step,
                "started_at": state.started_at,
                "completed_at": state.completed_at,
                "is_complete": False,
            })

    sessions.extend(_scan_evaluate_sessions(cwd))
    return sessions


def skip_forge_auto_close() -> bool:
    v = os.environ.get("FORGE_SKIP_AUTO_CLOSE", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def step1_abandon_threshold_seconds() -> float:
    raw = os.environ.get("FORGE_STEP1_ABANDON_HOURS", "1").strip()
    try:
        hours = float(raw)
    except ValueError:
        hours = 1.0
    if hours <= 0:
        hours = 1.0
    return hours * 3600.0


def has_matching_handoff(skill: str, search_dir: Path | None = None) -> bool:
    """True if handoff-{skill}.md exists in runtime or legacy memory."""
    for memory_dir in (runtime_memory_dir(search_dir), legacy_memory_dir(search_dir)):
        if (memory_dir / f"handoff-{skill}.md").exists():
            return True
    return False


def is_step1_abandoned(state: SkillState, path: Path) -> bool:
    if state.current_step > 1 or state.last_completed_step > 1:
        return False
    touched = (
        parse_iso_timestamp(state.last_touched_at)
        or parse_iso_timestamp(state.started_at)
        or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    )
    age_seconds = (datetime.now(timezone.utc) - touched).total_seconds()
    return age_seconds > step1_abandon_threshold_seconds()


def _auto_close_reason(
    starting_skill: str,
    session_skill: str,
    state: SkillState,
    path: Path,
    search_dir: Path | None,
) -> str | None:
    from scripts.shared.session_store import (
        is_session_state_path,
        session_handoff_path,
        session_id_from_state_path,
    )

    if is_session_state_path(path):
        sid = state.session_id or session_id_from_state_path(path)
        if sid and session_handoff_path(sid, search_dir).is_file():
            return f"sessions/{sid}/handoff.md exists"
    elif has_matching_handoff(session_skill, search_dir):
        return f"handoff-{session_skill}.md exists"

    start_idx = PIPELINE_SKILL_INDEX.get(starting_skill)
    session_idx = PIPELINE_SKILL_INDEX.get(session_skill)
    if (
        start_idx is not None
        and session_idx is not None
        and session_idx < start_idx
    ):
        return f"upstream of {starting_skill} in pipeline"

    if is_step1_abandoned(state, path):
        return "step-1-only session abandoned past threshold"

    return None


def _iter_skill_state_paths(search_dir: Path | None = None) -> list[Path]:
    cwd = search_dir or detect_repo_root()
    paths: list[Path] = []
    seen: set[Path] = set()
    from scripts.shared.session_store import iter_session_json_paths

    for candidate in iter_session_json_paths(cwd, include_archive=False):
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            paths.append(candidate)
    for skill in KNOWN_SKILLS:
        if skill in ("evaluate", "iterate"):
            continue
        for candidate in state_path_candidates(skill, cwd):
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(candidate)
    return paths


def auto_close_superseded_sessions(
    starting_skill: str,
    *,
    search_dir: Path | None = None,
    preserve_paths: set[Path] | None = None,
    dry_run: bool = False,
) -> list[tuple[Path, str]]:
    """Close leaked sessions when starting a pipeline skill at step 1."""
    if skip_forge_auto_close():
        return []

    preserve = {p.resolve() for p in (preserve_paths or set())}
    closed: list[tuple[Path, str]] = []

    for path in _iter_skill_state_paths(search_dir):
        resolved = path.resolve()
        if resolved in preserve:
            continue
        if not path.exists():
            continue
        try:
            state = load_state(path)
        except Exception:
            continue
        if is_state_effectively_complete(state):
            continue
        if is_state_stale(state, path):
            continue

        session_skill = state.skill_name
        if session_skill == starting_skill and resolved in preserve:
            continue

        reason = _auto_close_reason(starting_skill, session_skill, state, path, search_dir)
        if reason is None:
            continue

        if not dry_run:
            clear_state_file(path)
        closed.append((path, reason))

    return closed


def print_auto_closed_audit(closed: list[tuple[Path, str]]) -> None:
    for path, reason in closed:
        print(f"AUTO-CLOSED: {path} — {reason}", file=sys.stderr)


def resume_invocation_hint(*, cleanup: bool = False, force: bool = False) -> str:
    if os.environ.get("FORGE_USE_LAUNCHER") == "1":
        cmd = "forge resume"
        if cleanup:
            cmd += " --cleanup"
            if force:
                cmd += " --force"
        return cmd
    cmd = "python3 scripts/shared/resume.py"
    if cleanup:
        cmd += " --cleanup"
        if force:
            cmd += " --force"
    return cmd


def hint_cleanup_if_still_active(search_dir: Path | None = None) -> None:
    if skip_forge_auto_close():
        return
    remaining = detect_active_sessions(search_dir)
    if not remaining:
        return
    cmd = resume_invocation_hint(cleanup=True)
    print(
        f"HINT: {len(remaining)} active session(s) remain. "
        f"Dry-run cleanup: `{cmd}` (add `--force` to delete).",
        file=sys.stderr,
    )


def run_step1_session_hygiene(
    starting_skill: str,
    target_state_path: Path | None,
    *,
    search_dir: Path | None = None,
) -> list[tuple[Path, str]]:
    from scripts.shared.session_store import run_session_cleanup

    run_session_cleanup(search_dir=search_dir)
    preserve: set[Path] = set()
    if target_state_path is not None:
        preserve.add(target_state_path.resolve())
    closed = auto_close_superseded_sessions(
        starting_skill,
        search_dir=search_dir,
        preserve_paths=preserve,
    )
    print_auto_closed_audit(closed)
    hint_cleanup_if_still_active(search_dir)
    return closed


def collect_session_leak_hints(search_dir: Path | None = None) -> list[str]:
    cwd = search_dir or detect_repo_root()
    hints: list[str] = []
    state_dir = runtime_state_dir(cwd).resolve()

    for session in detect_active_sessions(cwd):
        skill = session["skill"]
        path = Path(session["path"])
        from scripts.shared.session_store import is_session_state_path, session_id_from_state_path, session_handoff_path

        if is_session_state_path(path):
            sid = session.get("session_id") or session_id_from_state_path(path)
            if sid and session_handoff_path(sid, cwd).is_file():
                hints.append(
                    f"{skill}: active session with handoff present — {path} "
                    f"(run `forge session close {sid}` or `forge resume --cleanup --force`)"
                )
        elif has_matching_handoff(skill, cwd):
            hints.append(
                f"{skill}: active state with handoff present — {path} "
                f"(run `forge resume --cleanup --force`)"
            )
        if skill == "evaluate":
            try:
                path.resolve().relative_to(state_dir)
            except ValueError:
                hints.append(f"{skill}: state file outside runtime state dir — {path}")
            continue
        try:
            state = load_state(path)
        except Exception:
            hints.append(f"{skill}: active session state unreadable — {path}")
            continue
        if is_step1_abandoned(state, path):
            hints.append(f"{skill}: step-1-only session idle >1h — {path}")
        if not is_session_state_path(path):
            try:
                path.resolve().relative_to(state_dir)
            except ValueError:
                hints.append(f"{skill}: state file outside runtime state dir — {path}")

    return hints


def collect_unreadable_state_files(search_dir: Path | None = None) -> list[str]:
    cwd = search_dir or detect_repo_root()
    active_paths = {Path(s["path"]).resolve() for s in detect_active_sessions(cwd)}
    issues: list[str] = []

    for skill in KNOWN_SKILLS:
        if skill == "evaluate":
            continue
        for candidate in state_path_candidates(skill, cwd):
            if not candidate.exists():
                continue
            resolved = candidate.resolve()
            if resolved in active_paths:
                continue
            try:
                state = load_state(candidate)
            except Exception as exc:
                issues.append(f"{candidate}: {exc}")
                continue
            if state.skill_name != skill:
                issues.append(
                    f"{candidate}: skill_name={state.skill_name!r} (expected {skill!r})"
                )

    return issues


def format_active_session_warning(sessions: list[dict], starting_skill: str) -> str:
    if not sessions:
        return ""

    lines = [
        "",
        "━" * 60,
        "ACTIVE SESSION DETECTED",
        "━" * 60,
        "",
        f"You are starting `{starting_skill}` but other active sessions exist:",
        "",
    ]
    for s in sessions:
        label = s.get("label")
        sid = s.get("session_id")
        extra = ""
        if label:
            extra = f' "{label}"'
        elif sid:
            extra = f" [{sid}]"
        lines.append(
            f"  • {s['skill']}{extra} — step {s['current_step']}/{s['max_step']} "
            f"(last completed: {s['last_completed_step']}) — {s['path']}"
        )
    lines.extend([
        "",
        "Eligible sessions may have been **auto-closed** on this step-1 start "
        "(handoff present, upstream in pipeline, or step-1 abandoned). "
        "See `AUTO-CLOSED:` lines above.",
        "",
        "**PAUSE.** Ask the user a concise question before proceeding:",
        f'- Resume `{sessions[0]["skill"]}` and continue the in-progress session',
        f'- Start `{starting_skill}` fresh and leave the existing session alone',
        "- Cancel and let the user decide manually",
        "",
        "━" * 60,
        "",
    ])
    return "\n".join(lines)


def print_remaining_session_warning(starting_skill: str, search_dir: Path | None = None) -> None:
    conflicting = get_conflicting_sessions(
        starting_skill,
        sessions=detect_active_sessions(search_dir),
        search_dir=search_dir,
    )
    if conflicting:
        print(format_active_session_warning(conflicting, starting_skill), file=sys.stderr)


def get_conflicting_sessions(
    starting_skill: str,
    sessions: list[dict] | None = None,
    search_dir: Path | None = None,
) -> list[dict]:
    active = sessions if sessions is not None else detect_active_sessions(search_dir)

    if starting_skill == "evaluate":
        return []

    if starting_skill in PIPELINE_SKILLS:
        return [
            session
            for session in active
            if session["skill"] != starting_skill and session["skill"] in PIPELINE_SKILLS
        ]

    return [
        session
        for session in active
        if session["skill"] != starting_skill
    ]


def next_skill_command(current_skill: str) -> str | None:
    return PIPELINE_FLOW.get(current_skill)
