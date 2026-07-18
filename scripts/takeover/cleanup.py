"""Legacy flat state file cleanup (migrated from resume)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.shared.orchestrator import is_state_effectively_complete, load_state

STALE_THRESHOLD_DAYS = 7


def _state_file_age_days(path: Path) -> float:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return 0.0
    delta = datetime.now(timezone.utc) - datetime.fromtimestamp(mtime, tz=timezone.utc)
    return delta.total_seconds() / 86400.0


def _has_matching_handoff(skill: str) -> bool:
    from scripts.shared.orchestrator import has_matching_handoff

    return has_matching_handoff(skill)


def _all_state_files(cwd: Path) -> list[tuple[Path, str]]:
    from scripts.shared.orchestrator import _iter_skill_state_paths

    found: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for path in _iter_skill_state_paths(cwd):
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        skill: str | None = None
        try:
            skill = load_state(path).skill_name
        except Exception:
            pass
        if not skill:
            stem = path.stem
            if stem.endswith("-state"):
                skill = stem[: -len("-state")].replace("_", "-")
            elif "-" in stem and not stem.endswith(".json"):
                skill = stem.split("-", 1)[0]
            else:
                skill = stem.replace("_", "-")
        found.append((path, skill))
    return found


def cleanup_candidates(all_stale: bool) -> list[tuple[dict, str]]:
    candidates: list[tuple[dict, str]] = []
    cwd = Path.cwd()

    for path, skill in _all_state_files(cwd):
        info = {"path": str(path), "skill": skill}

        if all_stale:
            candidates.append((info, "marked stale via --all-stale"))
            continue

        try:
            state = load_state(path)
            if is_state_effectively_complete(state):
                reason = (
                    "completed_at is set"
                    if state.completed_at
                    else "state reached max_step without completed_at"
                )
                candidates.append((info, reason))
                continue
        except Exception:
            candidates.append((info, "state file unparseable"))
            continue

        age = _state_file_age_days(path)
        if age > STALE_THRESHOLD_DAYS:
            candidates.append((info, f"file age {age:.1f}d > {STALE_THRESHOLD_DAYS}d"))
            continue

        if skill and _has_matching_handoff(skill):
            candidates.append((info, f"handoff-{skill}.md exists (parallel session superseded)"))
            continue

    return candidates


def run_cleanup(force: bool, all_stale: bool) -> None:
    candidates = cleanup_candidates(all_stale)

    if not candidates:
        print("No state files eligible for cleanup.")
        return

    from scripts.shared.orchestrator import clear_state_file

    action = "Deleting" if force else "Would delete (dry-run)"
    for session, reason in candidates:
        print(f"{action}: {session['path']}  ({session['skill']}: {reason})", file=sys.stderr)
        if force:
            try:
                # Archives session directories (sidecars/, handoff.md) instead of
                # leaving them orphaned when the path is a session-store session.json.
                clear_state_file(Path(session["path"]))
            except OSError as e:
                print(f"  ! failed to delete: {e}", file=sys.stderr)

    summary_verb = "Deleted" if force else "Would delete"
    print(f"\n{summary_verb} {len(candidates)} state file(s).")
    if not force:
        print("Re-run with --force to actually delete.")
