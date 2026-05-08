#!/usr/bin/env python3
"""Resume meta-orchestrator for the forge-codex toolkit.

Detects all active skill sessions and outputs the appropriate resume command.
Handles three cases:
  0 active sessions: Check for handoff files and suggest the next skill in the pipeline
  1 active session:  Output the exact command to resume it
  2+ active sessions: Output a menu and tell Codex to ask the user directly

Usage:
    python3 resume.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Auto-detect repo root so this works from any working directory
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # scripts/shared/ -> scripts/ -> repo root

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.shared.orchestrator import (
    KNOWN_SKILLS,
    PIPELINE_FLOW,
    detect_active_sessions,
    legacy_memory_dir,
    legacy_state_dir,
    legacy_state_filename,
    load_state,
    runtime_memory_dir,
    runtime_state_dir,
    state_filename,
)

# Number of consecutive same-step retries after which we stop offering a
# resume command and ask the user to inspect logs / clear state.
MAX_RETRY_COUNT = 2


# Map skill name to script path for generating resume commands
def _script_for(skill: str) -> str:
    """Return the Python script path for a given skill name."""
    script_map = {
        "develop": "scripts/develop/develop.py",
        "plan": "scripts/plan/plan.py",
        "implement": "scripts/implement/implement.py",
        "code-review": "scripts/code_review/code_review.py",
        "test": "scripts/test/test.py",
        "diagnose": "scripts/diagnose/orchestrate.py",
        "evaluate": "scripts/evaluate/evaluate.py",
    }
    rel = script_map.get(skill)
    if rel:
        return str(REPO_ROOT / rel)
    return f"scripts/{skill}/{skill}.py"


def _resume_step(session: dict) -> int:
    """Determine which step to resume.

    Rules:
    - If current_step is 0 or unset, start at step 1.
    - If last_completed_step matches current_step AND there's a next step,
      advance to current_step + 1.
    - Otherwise re-execute the current step (idempotent retry).
    - Cap last_completed_step at current_step to defend against inconsistent
      state (e.g. wave loops that decrement current_step but leave last high).
    """
    current = session.get("current_step", 1)
    last_completed = session.get("last_completed_step", 0)
    max_step = session.get("max_step", 6)

    # Defensive: clamp last_completed to never exceed current_step
    last_completed = min(last_completed, current)

    # Fresh/uninitialized state
    if current <= 0:
        return 1

    # Workflow complete - nothing to advance to
    if current >= max_step and last_completed >= max_step:
        return max_step  # caller can detect "complete" via separate flag

    # Step completed - advance
    if last_completed == current and current < max_step:
        return current + 1

    # Retry current step
    return max(current, 1)


def _session_is_complete(session: dict) -> bool:
    """True if the session's workflow has finished."""
    current = session.get("current_step", 1)
    last_completed = session.get("last_completed_step", 0)
    max_step = session.get("max_step", 6)
    return current >= max_step and last_completed >= max_step


def _resume_command(session: dict) -> str:
    """Build the command to resume a session."""
    skill = session["skill"]
    script = _script_for(skill)
    step = _resume_step(session)
    state_path = session["path"]
    if os.environ.get("FORGE_USE_LAUNCHER") == "1":
        return f"forge {skill} --step {step} --state '{state_path}'"
    return f"python3 {script} --step {step} --state '{state_path}'"


def _is_retry(session: dict) -> bool:
    """True when resuming would re-execute the current step (not advance)."""
    current = session.get("current_step", 1)
    last = session.get("last_completed_step", 0)
    last = min(last, current)
    if current <= 0:
        return False
    return not (last == current and current < session.get("max_step", 6))


def _bump_failure_count(state_path: str) -> int:
    """Load JSON state, increment failure_count, save, return new value.

    Operates directly on JSON so it works for both SkillState and EvalState.
    Returns 0 on read/parse failure rather than raising.
    """
    p = Path(state_path)
    try:
        data = json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return 0
    new_count = int(data.get("failure_count", 0)) + 1
    data["failure_count"] = new_count
    try:
        p.write_text(json.dumps(data, indent=2))
    except OSError:
        return new_count
    return new_count


def _pipeline_successor_skill(completed_skills: set[str]) -> str | None:
    """Given the set of skills with handoff files, return the next skill to run."""
    # Walk the pipeline in order; return the first skill whose predecessor
    # has a handoff but which itself has no handoff.
    pipeline = ["develop", "plan", "implement", "code-review", "test", "diagnose"]
    for i, skill in enumerate(pipeline):
        if i == 0:
            continue
        predecessor = pipeline[i - 1]
        if predecessor in completed_skills and skill not in completed_skills:
            return skill
    return None


def _check_handoffs() -> list[str]:
    """List skill names that have written handoff files in runtime memory."""
    memory_dirs = [runtime_memory_dir(), legacy_memory_dir()]
    completed = []
    for skill in KNOWN_SKILLS:
        for memory_dir in memory_dirs:
            handoff = memory_dir / f"handoff-{skill}.md"
            if handoff.exists():
                completed.append(skill)
                break
    return completed


def render_no_sessions() -> str:
    """Output when no active sessions exist."""
    completed = _check_handoffs()

    lines = [
        "FORGE-CODEX RESUME",
        "=" * 60,
        "",
        "**No active sessions found.**",
        "",
    ]

    if not completed:
        lines.extend([
            "No handoff files exist either — no workflow is currently in progress.",
            "",
            "To start a new workflow, run one of these skills:",
            "  develop   - investigate and brainstorm solutions",
            "  plan      - create an implementation plan",
            "  diagnose  - deep root-cause analysis",
            "  evaluate  - critique an existing plan",
        ])
        return "\n".join(lines)

    lines.extend([
        f"**Handoff files found for:** {', '.join(completed)}",
        "",
    ])

    successor = _pipeline_successor_skill(set(completed))
    if successor:
        lines.extend([
            f"**Next skill in pipeline:** `{successor}`",
            "",
            "Ask the user directly whether to continue to that skill, run a different skill, or stay idle.",
        ])
    else:
        lines.extend([
            "**Workflow appears complete** — all pipeline skills have handoff files.",
            "",
            "Start a new workflow or view status with the `status` skill.",
        ])

    return "\n".join(lines)


def render_single_session(session: dict) -> str:
    """Output when exactly one active session exists."""
    skill = session["skill"]
    current = session.get("current_step", 1)
    last = session.get("last_completed_step", 0)
    max_step = session.get("max_step", 6)

    # If workflow is actually complete, don't produce a resume command
    if _session_is_complete(session):
        lines = [
            "FORGE-CODEX RESUME",
            "=" * 60,
            "",
            f"**Session `{skill}` is complete** ({current}/{max_step}).",
            f"**State file:** `{session['path']}`",
            "",
            "The final step has been executed. No resume command is needed.",
            "",
            "You may:",
            "  - Delete the state file to start fresh next time",
            "  - Run `resume` again to advance to the next pipeline skill",
            "  - Run `status` to see the overall workflow state",
        ]
        return "\n".join(lines)

    next_step = _resume_step(session)

    # Retry-loop guard: if this resume would re-execute the same step that
    # already failed too many times, stop offering a resume command and ask
    # the user to inspect logs / clear state.
    if _is_retry(session):
        new_count = _bump_failure_count(session["path"])
        if new_count >= MAX_RETRY_COUNT:
            return "\n".join([
                "FORGE-CODEX RESUME",
                "=" * 60,
                "",
                f"**Active session:** `{skill}` ({current}/{max_step})",
                f"**State file:** `{session['path']}`",
                "",
                f"**Step {current} has failed {new_count} times.**",
                "",
                "Inspect logs for the underlying error before retrying. If the failure",
                "is not recoverable, clear state with:",
                "",
                f"    forge resume --cleanup --force" if os.environ.get("FORGE_USE_LAUNCHER") == "1" else f"    python3 scripts/shared/resume.py --cleanup --force",
                "",
                "Then start the workflow over from step 1.",
            ])

    cmd = _resume_command(session)

    # Determine if resuming completed step vs retrying current
    if last == current and current < max_step:
        status = f"Step {current} completed, advancing to step {next_step}"
    else:
        status = f"Step {current} in progress, re-executing phase prompt"

    lines = [
        "FORGE-CODEX RESUME",
        "=" * 60,
        "",
        f"**Active session:** `{skill}` ({current}/{max_step})",
        f"**Status:** {status}",
        f"**State file:** `{session['path']}`",
        "",
        "━" * 60,
        "CONTINUATION — IMMEDIATE ACTION REQUIRED",
        "━" * 60,
        "Execute this command to resume:",
        "",
        f"    {cmd}",
        "",
        "DO NOT STOP. Execute the command now to continue the workflow.",
    ]
    return "\n".join(lines)


def render_multiple_sessions(sessions: list[dict]) -> str:
    """Output when 2+ active sessions exist - emit a menu."""
    options_lines = []
    for i, s in enumerate(sessions):
        skill = s["skill"]
        current = s.get("current_step", 1)
        max_step = s.get("max_step", 6)
        started = s.get("started_at", "unknown")
        comma = "," if i < len(sessions) - 1 or True else ""  # always comma, "None" follows
        options_lines.append(
            f'      {{"label": "{skill} ({current}/{max_step})", '
            f'"description": "Started {started}, resume from step {_resume_step(s)}"}}'
        )

    lines = [
        "FORGE-CODEX RESUME",
        "=" * 60,
        "",
        f"**{len(sessions)} active sessions found.**",
        "",
        "Ask the user directly which session to resume:",
    ]

    for i, opt_line in enumerate(options_lines):
        lines.append(opt_line.replace('      {"label": "', "- `").replace('", "description": "', "` — ").replace('"}', ""))
    lines.append("- `None` — do nothing and let the user decide")
    lines.extend(["", "After the user chooses, execute the corresponding resume command:"])
    lines.append("")
    for s in sessions:
        cmd = _resume_command(s)
        lines.append(f"  {s['skill']}: `{cmd}`")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cleanup mode
# ---------------------------------------------------------------------------

# State files older than this are considered stale.
STALE_THRESHOLD_DAYS = 7


def _state_file_age_days(path: Path) -> float:
    """Days since last modification of a state file."""
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return 0.0
    delta = datetime.now(timezone.utc) - datetime.fromtimestamp(mtime, tz=timezone.utc)
    return delta.total_seconds() / 86400.0


def _has_matching_handoff(skill: str) -> bool:
    """True if a handoff file for this skill exists in either memory dir."""
    for memory_dir in (runtime_memory_dir(), legacy_memory_dir()):
        if (memory_dir / f"handoff-{skill}.md").exists():
            return True
    return False


def _all_state_files(cwd: Path) -> list[tuple[Path, str]]:
    """Walk runtime+legacy state dirs and return (path, skill) for every state file.

    Unlike `detect_active_sessions`, this includes files where `completed_at`
    is set — those are exactly the leaked-but-finished files cleanup targets.
    """
    found: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    candidate_dirs = [runtime_state_dir(cwd), legacy_state_dir(cwd), cwd]
    for skill in KNOWN_SKILLS:
        if skill == "evaluate":
            continue
        for dir_path in candidate_dirs:
            for fname in (state_filename(skill), legacy_state_filename(skill)):
                p = dir_path / fname
                if p.exists() and p not in seen:
                    found.append((p, skill))
                    seen.add(p)
    return found


def _cleanup_candidates(all_stale: bool) -> list[tuple[dict, str]]:
    """Return (info, reason) pairs for state files eligible for cleanup."""
    candidates: list[tuple[dict, str]] = []
    cwd = Path.cwd()

    for path, skill in _all_state_files(cwd):
        info = {"path": str(path), "skill": skill}

        if all_stale:
            candidates.append((info, "marked stale via --all-stale"))
            continue

        try:
            state = load_state(path)
            if state.completed_at:
                candidates.append((info, "completed_at is set"))
                continue
        except Exception:
            # Corrupt state — also cleanup-eligible.
            candidates.append((info, "state file unparseable"))
            continue

        age = _state_file_age_days(path)
        if age > STALE_THRESHOLD_DAYS:
            candidates.append((info, f"file age {age:.1f}d > {STALE_THRESHOLD_DAYS}d"))
            continue

        if _has_matching_handoff(skill):
            candidates.append((info, f"handoff-{skill}.md exists"))
            continue

    return candidates


def run_cleanup(force: bool, all_stale: bool) -> None:
    """List or delete cleanup-eligible state files. Default = dry-run."""
    candidates = _cleanup_candidates(all_stale)

    if not candidates:
        print("No state files eligible for cleanup.")
        return

    action = "Deleting" if force else "Would delete (dry-run)"
    for session, reason in candidates:
        print(f"{action}: {session['path']}  ({session['skill']}: {reason})", file=sys.stderr)
        if force:
            try:
                Path(session["path"]).unlink()
            except OSError as e:
                print(f"  ! failed to delete: {e}", file=sys.stderr)

    summary_verb = "Deleted" if force else "Would delete"
    print(f"\n{summary_verb} {len(candidates)} state file(s).")
    if not force:
        print("Re-run with --force to actually delete.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resume forge-codex workflows or clean up stale state files."
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="List/delete state files eligible for cleanup. Defaults to dry-run.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="With --cleanup: actually delete files instead of dry-run.",
    )
    parser.add_argument(
        "--all-stale",
        action="store_true",
        help="With --cleanup: include every state file regardless of age "
             "(migration mode for users with pre-fix leaked state).",
    )
    args = parser.parse_args()

    if args.cleanup:
        run_cleanup(force=args.force, all_stale=args.all_stale)
        return

    sessions = detect_active_sessions()

    if not sessions:
        print(render_no_sessions())
    elif len(sessions) == 1:
        print(render_single_session(sessions[0]))
    else:
        # Sort by most recent first
        sessions_sorted = sorted(
            sessions,
            key=lambda s: s.get("started_at") or "",
            reverse=True,
        )
        print(render_multiple_sessions(sessions_sorted))


if __name__ == "__main__":
    main()
