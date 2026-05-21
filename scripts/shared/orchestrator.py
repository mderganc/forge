"""Shared orchestrator base for all Forge skill scripts.

Provides common patterns for state management, step progression,
review loop enforcement, agent dispatch tracking, beads state,
session resume, and handoff file generation.

All skill orchestrators inherit from SkillOrchestrator.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

def _detect_repo_root(start: Path | None = None) -> Path:
    """Detect the target repo root from the current working directory.

    This module is used both from a repo checkout and from an installed package
    (e.g. via `pipx`). In installed mode, `__file__` points into site-packages,
    so we must anchor runtime state to the *target repo*, not the package.
    """
    cur = (start or Path.cwd()).resolve()
    readme_candidate: Path | None = None
    for p in (cur, *cur.parents):
        if (p / ".git").is_dir():
            return p
        if readme_candidate is None and (p / "README.md").is_file():
            readme_candidate = p
    return readme_candidate or cur


# Runtime defaults are anchored to the detected target repo root (cwd-based).
REPO_ROOT = _detect_repo_root()

# Ensure Unicode prompt output works on Windows terminals when running scripts
# directly (not via the `forge` launcher).
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
# Canonical on-disk layout under the target repo (matches the `forge` CLI / forge-next package).
CANONICAL_RUNTIME_PARTS = (".codex", "forge")
# Older checkouts used this name; still honored if present and canonical is absent.
LEGACY_FORGE_CODEX_RUNTIME_PARTS = (".codex", "forge-codex")
LEGACY_RUNTIME_DIRNAME = ".forge"
EVALUATE_STATE_FILENAME = ".evaluate-state.json"
RUN_HISTORY_MAX_ENTRIES = 30


def _blocked_runtime_anchor(base_dir: Path) -> bool:
    """True when the canonical `.codex` anchor exists but is not a directory."""
    anchor = base_dir / CANONICAL_RUNTIME_PARTS[0]
    return anchor.exists() and not anchor.is_dir()


def runtime_root(search_dir: Path | None = None) -> Path:
    """Return the runtime root for Forge artifacts under the target repo.

    Resolution order:
    1) If `.codex` exists but is not a directory, use legacy `.forge/` (single-dir layout).
    2) Else if `.codex/forge-codex/` exists as a directory and `.codex/forge/` does not,
       use the old path (backward compatibility).
    3) Else use canonical `.codex/forge/`.
    """
    base_dir = search_dir or _detect_repo_root()
    if _blocked_runtime_anchor(base_dir):
        return base_dir / LEGACY_RUNTIME_DIRNAME
    canonical = base_dir.joinpath(*CANONICAL_RUNTIME_PARTS)
    legacy_fc = base_dir.joinpath(*LEGACY_FORGE_CODEX_RUNTIME_PARTS)
    if legacy_fc.is_dir() and not canonical.exists():
        return legacy_fc
    return canonical


def legacy_runtime_root(search_dir: Path | None = None) -> Path:
    """Return the legacy runtime root used by the original copied workflow."""
    base_dir = search_dir or _detect_repo_root()
    return base_dir / LEGACY_RUNTIME_DIRNAME


def runtime_memory_dir(search_dir: Path | None = None) -> Path:
    """Return the canonical memory directory."""
    return runtime_root(search_dir) / "memory"


def legacy_memory_dir(search_dir: Path | None = None) -> Path:
    """Return the legacy memory directory."""
    return legacy_runtime_root(search_dir) / "memory"


def runtime_state_dir(search_dir: Path | None = None) -> Path:
    """Return the canonical state directory."""
    return runtime_root(search_dir) / "state"


def legacy_state_dir(search_dir: Path | None = None) -> Path:
    """Return the legacy state directory."""
    return legacy_runtime_root(search_dir)


def runtime_adr_dir(search_dir: Path | None = None) -> Path:
    """Return the canonical ADR directory."""
    return runtime_root(search_dir) / "adr"


def runtime_backlog_path(search_dir: Path | None = None) -> Path:
    """Return the canonical backlog path."""
    return runtime_root(search_dir) / "backlog.md"


def ensure_runtime_dirs(search_dir: Path | None = None) -> None:
    """Create the canonical runtime directory structure if missing."""
    runtime_state_dir(search_dir).mkdir(parents=True, exist_ok=True)
    runtime_memory_dir(search_dir).mkdir(parents=True, exist_ok=True)
    runtime_adr_dir(search_dir).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ReviewLoopState:
    """Tracks review loop progress for a single stage gate."""
    round: int = 0
    self_review: str = "pending"       # pending / pass / fail
    cross_review: str = "pending"
    critic_review: str = "pending"
    pm_validation: str = "pending"
    findings: list[dict] = field(default_factory=list)

    def is_clean(self) -> bool:
        """True if all four checks passed in the current round."""
        return all(
            getattr(self, attr) == "pass"
            for attr in ("self_review", "cross_review", "critic_review", "pm_validation")
        )

    def reset_round(self) -> None:
        """Start a new review round."""
        self.round += 1
        self.self_review = "pending"
        self.cross_review = "pending"
        self.critic_review = "pending"
        self.pm_validation = "pending"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ReviewLoopState:
        return cls(**data)


@dataclass
class AgentDispatch:
    """Tracks dispatch and completion of a single agent in a step."""
    agent: str
    step: int
    dispatched: bool = False
    completed: bool = False
    review_passed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AgentDispatch:
        return cls(**data)


@dataclass
class SkillState:
    """Base state for all skill orchestrators."""
    skill_name: str
    current_step: int = 0
    last_completed_step: int = 0
    max_step: int = 6
    quick_mode: bool = False
    autonomy_level: int = 1

    # Beads tracking
    beads_available: bool = False
    epic_id: str | None = None
    issue_ids: dict[str, str] = field(default_factory=dict)

    # Review loop state (per-step, keyed by step number)
    review_loops: dict[str, ReviewLoopState] = field(default_factory=dict)

    # Agent dispatch tracking
    dispatches: list[AgentDispatch] = field(default_factory=list)

    # Findings
    findings: list[dict] = field(default_factory=list)

    # Phase todos (per-step, keyed by step number)
    phase_todos: dict[str, list[dict]] = field(default_factory=dict)

    # Timestamps
    started_at: str | None = None
    completed_at: str | None = None
    last_touched_at: str | None = None
    session_id: str = field(default_factory=lambda: str(uuid4()))

    # Retry guard: counts consecutive failures of the same step. Reset on
    # successful step completion. resume.py emits an "inspect logs" hint
    # instead of a third retry once this hits 2.
    failure_count: int = 0

    # Custom state for specific skills
    custom: dict[str, Any] = field(default_factory=dict)

    def get_review_loop(self, step: int) -> ReviewLoopState:
        """Get or create review loop state for a step."""
        key = str(step)
        if key not in self.review_loops:
            self.review_loops[key] = ReviewLoopState()
        loop = self.review_loops[key]
        if isinstance(loop, dict):
            loop = ReviewLoopState.from_dict(loop)
            self.review_loops[key] = loop
        return loop

    def record_dispatch(self, agent: str, step: int) -> AgentDispatch:
        """Record that an agent was dispatched for a step."""
        dispatch = AgentDispatch(agent=agent, step=step, dispatched=True)
        self.dispatches.append(dispatch)
        return dispatch

    def add_finding(self, phase: str, severity: str, title: str, detail: str) -> dict:
        """Add a finding."""
        fid = f"F{len(self.findings) + 1}"
        finding = {
            "id": fid,
            "phase": phase,
            "severity": severity,
            "title": title,
            "detail": detail,
            "status": "open",
        }
        self.findings.append(finding)
        return finding

    def open_findings(self) -> list[dict]:
        return [f for f in self.findings if f.get("status") != "dismissed"]

    def mark_step_complete(self, step: int) -> None:
        """Mark a step as completed and reset the retry-failure counter."""
        self.last_completed_step = step
        self.failure_count = 0

    def to_dict(self) -> dict:
        data = {
            "skill_name": self.skill_name,
            "current_step": self.current_step,
            "last_completed_step": self.last_completed_step,
            "max_step": self.max_step,
            "quick_mode": self.quick_mode,
            "autonomy_level": self.autonomy_level,
            "beads_available": self.beads_available,
            "epic_id": self.epic_id,
            "issue_ids": self.issue_ids,
            "review_loops": {
                k: v.to_dict() if isinstance(v, ReviewLoopState) else v
                for k, v in self.review_loops.items()
            },
            "dispatches": [
                d.to_dict() if isinstance(d, AgentDispatch) else d
                for d in self.dispatches
            ],
            "findings": self.findings,
            "phase_todos": self.phase_todos,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "last_touched_at": self.last_touched_at,
            "session_id": self.session_id,
            "failure_count": self.failure_count,
            "custom": self.custom,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> SkillState:
        state = cls(skill_name=data["skill_name"])
        state.current_step = data.get("current_step", 0)
        state.last_completed_step = data.get("last_completed_step", 0)
        state.max_step = data.get("max_step", 6)
        state.quick_mode = data.get("quick_mode", False)
        state.autonomy_level = data.get("autonomy_level", 1)
        state.beads_available = data.get("beads_available", False)
        state.epic_id = data.get("epic_id")
        state.issue_ids = data.get("issue_ids", {})
        state.review_loops = {
            k: ReviewLoopState.from_dict(v) if isinstance(v, dict) else v
            for k, v in data.get("review_loops", {}).items()
        }
        state.dispatches = [
            AgentDispatch.from_dict(d) if isinstance(d, dict) else d
            for d in data.get("dispatches", [])
        ]
        state.findings = data.get("findings", [])
        state.phase_todos = data.get("phase_todos", {})
        state.started_at = data.get("started_at")
        state.completed_at = data.get("completed_at")
        state.last_touched_at = data.get("last_touched_at")
        state.session_id = data.get("session_id", state.session_id)
        state.failure_count = data.get("failure_count", 0)
        state.custom = data.get("custom", {})
        return state


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def state_filename(skill_name: str) -> str:
    """Return the state filename for a skill."""
    return f"{skill_name}.json"


def legacy_state_filename(skill_name: str) -> str:
    """Return the legacy pre-refactor state filename for a skill."""
    return f".forge-{skill_name}-state.json"


def runtime_state_path(skill_name: str, search_dir: Path | None = None) -> Path:
    """Return the canonical state path for a skill."""
    return runtime_state_dir(search_dir) / state_filename(skill_name)


def _is_skill_state_filename(name: str, skill_name: str) -> bool:
    """True when ``name`` is a valid state filename for ``skill_name``."""
    if skill_name == "evaluate":
        return name == EVALUATE_STATE_FILENAME or (
            name.startswith(".evaluate-state-") and name.endswith(".json")
        )
    if name in {state_filename(skill_name), legacy_state_filename(skill_name)}:
        return True
    # Support parallel sessions with suffixed names, e.g. plan-20260517-123000.json
    return name.startswith(f"{skill_name}-") and name.endswith(".json")


def _state_path_candidates(skill_name: str, search_dir: Path | None = None) -> list[Path]:
    """Return deduplicated candidate paths for a skill's state files."""
    cwd = search_dir or Path.cwd()
    dirs = [
        runtime_state_dir(cwd),
        legacy_state_dir(cwd),
        cwd,
    ]
    candidates: list[Path] = []
    seen: set[Path] = set()

    # Fixed canonical + legacy names first.
    for path in (
        runtime_state_path(skill_name, cwd),
        cwd / state_filename(skill_name),
        legacy_state_dir(cwd) / legacy_state_filename(skill_name),
        cwd / legacy_state_filename(skill_name),
    ):
        if path not in seen:
            candidates.append(path)
            seen.add(path)

    # Parallel-session variants (skill-*.json) in the same directories.
    for dir_path in dirs:
        if not dir_path.exists():
            continue
        for path in sorted(dir_path.glob(f"{skill_name}-*.json")):
            if path not in seen:
                candidates.append(path)
                seen.add(path)

    return candidates


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
    # Continuity snapshot for `forge resume` (never break state saves).
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
    """Find the best state file for a skill.

    Selection policy:
      1) Prefer active (not effectively complete) states.
      2) Within that set, choose most recently modified.
      3) Optionally include completed states as fallback.
    """
    active_fresh: list[Path] = []
    active_stale: list[Path] = []
    complete: list[Path] = []

    for candidate in _state_path_candidates(skill_name, search_dir):
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


# ---------------------------------------------------------------------------
# Cross-session detection & pipeline flow
# ---------------------------------------------------------------------------

# Known skills that produce state files (used by detect_active_sessions)
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

# Explicit pipeline order (PIPELINE_SKILLS is a set — never iterate it for ordering).
PIPELINE_SKILL_ORDER = (
    "develop",
    "plan",
    "implement",
    "code-review",
    "test",
    "diagnose",
)
PIPELINE_SKILL_INDEX = {name: idx for idx, name in enumerate(PIPELINE_SKILL_ORDER)}

# Pipeline flow: which skill comes next after each skill completes
PIPELINE_FLOW = {
    "develop": "plan",
    "plan": "implement",
    "implement": "code-review",
    "code-review": "test",
    "test": "diagnose",
    "diagnose": None,  # end of pipeline
    "evaluate": None,  # standalone skill
}


def _scan_evaluate_sessions(cwd: Path) -> list[dict]:
    """Find active evaluate sessions.

    Evaluate is special: it uses `.evaluate-state.json` and places state files
    alongside the plan being evaluated instead of the runtime state directory.
    """
    import json

    sessions: list[dict] = []

    # Candidate locations: cwd, runtime roots, and anywhere under docs/
    candidates: list[Path] = []
    for dir_path in (cwd, runtime_root(cwd), legacy_runtime_root(cwd)):
        if not dir_path.exists():
            continue
        # Canonical evaluate state filename plus parallel-session variants.
        for candidate in [dir_path / EVALUATE_STATE_FILENAME, *dir_path.glob(".evaluate-state-*.json")]:
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

        # Evaluate state has no completed_at field (it's ephemeral - deleted on
        # completion). If the file exists, it's active.
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
    """Scan for all active skill state files.

    Returns a list of dicts, one per active session:
        {
            "skill": str,
            "path": Path,
            "current_step": int,
            "last_completed_step": int,
            "max_step": int,
            "started_at": str | None,
            "completed_at": str | None,
            "is_complete": bool,
        }

    Only returns sessions that are NOT completed (completed_at is None).
    """
    cwd = search_dir or _detect_repo_root()
    sessions: list[dict] = []
    seen_paths: set[Path] = set()
    for skill in KNOWN_SKILLS:
        # Evaluate uses a different state system - handle separately below
        if skill == "evaluate":
            continue

        for candidate in _state_path_candidates(skill, cwd):
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

            sessions.append({
                "skill": state.skill_name,
                "path": candidate,
                "current_step": state.current_step,
                "last_completed_step": state.last_completed_step,
                "max_step": state.max_step,
                "started_at": state.started_at,
                "completed_at": state.completed_at,
                "is_complete": False,
            })

    # Handle evaluate separately (different state format + location)
    sessions.extend(_scan_evaluate_sessions(cwd))

    return sessions


def skip_forge_auto_close() -> bool:
    """Return True when step-1 auto-close of superseded sessions is suppressed."""
    v = os.environ.get("FORGE_SKIP_AUTO_CLOSE", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def step1_abandon_threshold_seconds() -> float:
    """Inactivity threshold for step-1-only abandoned sessions."""
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
    """True when a session never left step 1 and has been idle past the threshold."""
    if state.current_step > 1 or state.last_completed_step > 1:
        return False
    touched = (
        _parse_iso_timestamp(state.last_touched_at)
        or _parse_iso_timestamp(state.started_at)
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
    """Return a close reason string, or None if the session should stay active."""
    if has_matching_handoff(session_skill, search_dir):
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
    """All plausible on-disk skill state paths (canonical + parallel variants)."""
    cwd = search_dir or _detect_repo_root()
    paths: list[Path] = []
    seen: set[Path] = set()
    for skill in KNOWN_SKILLS:
        if skill in ("evaluate", "iterate"):
            continue
        for candidate in _state_path_candidates(skill, cwd):
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
    """Close leaked sessions when starting a pipeline skill at step 1.

    Applies handoff-backed, upstream-pipeline, and step-1-abandoned rules.
    Never closes paths in ``preserve_paths`` (typically the new step-1 target).
    """
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
    """Emit stderr lines for sessions removed by auto-close."""
    for path, reason in closed:
        print(f"AUTO-CLOSED: {path} — {reason}", file=sys.stderr)


def hint_cleanup_if_still_active(search_dir: Path | None = None) -> None:
    """Suggest manual cleanup when active sessions remain after auto-close."""
    if skip_forge_auto_close():
        return
    remaining = detect_active_sessions(search_dir)
    if not remaining:
        return
    cmd = "forge resume --cleanup" if os.environ.get("FORGE_USE_LAUNCHER") == "1" else (
        "python3 scripts/shared/resume.py --cleanup"
    )
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
    """Auto-close superseded sessions, audit to stderr, hint if leaks remain."""
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
    """Human-readable warnings for leaked or misplaced workflow state."""
    cwd = search_dir or _detect_repo_root()
    hints: list[str] = []
    state_dir = runtime_state_dir(cwd).resolve()

    for session in detect_active_sessions(cwd):
        skill = session["skill"]
        path = Path(session["path"])
        if has_matching_handoff(skill, cwd):
            hints.append(
                f"{skill}: active state with handoff present — {path} "
                f"(run `forge resume --cleanup --force`)"
            )
        if is_step1_abandoned(load_state(path), path):
            hints.append(f"{skill}: step-1-only session idle >1h — {path}")
        try:
            path.resolve().relative_to(state_dir)
        except ValueError:
            hints.append(f"{skill}: state file outside runtime state dir — {path}")

    return hints


def print_remaining_session_warning(starting_skill: str, search_dir: Path | None = None) -> None:
    """Warn about active sessions that auto-close did not remove."""
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
    """Return only sessions that should block a fresh step-1 start."""
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
    """Return the next skill name in the pipeline, or None."""
    return PIPELINE_FLOW.get(current_skill)


def skip_forge_session_opt_in() -> bool:
    """Return True when step-1 session opt-in banner should be suppressed."""
    v = os.environ.get("FORGE_SKIP_SESSION_OPTIN", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def forge_graphify_context_block(skill_name: str, step: int) -> str:
    """Per-step Graphify reminder when the repo has an index (see graphify_contract)."""
    from scripts.shared.graphify_contract import forge_graphify_banner

    return forge_graphify_banner(skill_name, step, REPO_ROOT)


def forge_session_opt_in_banner(skill_name: str, step: int) -> str:
    """Prompt agents to offer structured Forge workflows vs ad-hoc help (step 1 only).

    Shown at the start of any skill when ``step == 1``, unless
    ``FORGE_SKIP_SESSION_OPTIN`` is set (automation / CI).
    """
    if step != 1 or skip_forge_session_opt_in():
        return ""
    bar = ("=" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("━" * 60)
    slug = skill_name.strip().lower()
    return (
        f"{bar}\n"
        "SESSION OPT-IN — Forge structured workflows\n"
        f"{bar}\n\n"
        "**Before mirroring or acting on the “Create Phase Todos” block below,** complete "
        "this opt-in with the user (unless they already confirmed earlier in this chat).\n\n"
        f"You are on **step 1** of **`{slug}`** — a multi-step Forge skill (printed "
        "prompts, gates, handoff menus).\n\n"
        "**Pause and ask the user once** (unless they already answered in this chat):\n\n"
        "- **Opt in:** They want Forge for this session — follow each step, run suggested "
        "`/forge:…`, `$forge:…`, or `forge …` lines, and honor handoffs.\n"
        "- **Ad hoc:** Informal help only — do not drive the full workflow or touch Forge "
        "state unless they ask.\n\n"
        "If they already opted in earlier in this conversation, skip repeating the "
        "question; add a line under `## Forge session` in `project.md`: "
        "`forge_skills: opted_in` (optional short note).\n\n"
        "_To hide this block (e.g. CI): set `FORGE_SKIP_SESSION_OPTIN=1`._\n\n"
    )


def format_active_session_warning(sessions: list[dict], starting_skill: str) -> str:
    """Render a Codex-friendly cross-session conflict prompt.

    Used when a skill's step 1 detects other active sessions.
    """
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
        lines.append(
            f"  • {s['skill']} — step {s['current_step']}/{s['max_step']} "
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


def validate_state_path(state_file: str, skill_name: str) -> Path | None:
    """Validate and resolve a --state CLI argument.

    Returns the resolved Path if valid, or None if the argument should be
    ignored (doesn't exist, outside project).
    """
    sp = Path(state_file).resolve()
    repo_root = _detect_repo_root().resolve()

    # Reject paths outside the repository directory
    try:
        sp.relative_to(repo_root)
    except ValueError:
        print(f"WARNING: --state path is outside the repository, ignoring: {state_file}",
              file=sys.stderr)
        return None

    # Reject paths that don't look like state files for this skill.
    looks_like_state = _is_skill_state_filename(sp.name, skill_name)
    if not looks_like_state:
        print(f"WARNING: --state path doesn't look like a state file, ignoring: {state_file}",
              file=sys.stderr)
        return None

    if not sp.exists():
        return None

    return sp


def resolve_step1_state_path(
    skill_name: str,
    state_file: str | None = None,
    *,
    parallel: bool = False,
    search_dir: Path | None = None,
) -> Path:
    """Resolve where a step-1 invocation should write state.

    - ``--state <path>``: use that path if it is inside the repo and filename
      matches the skill.
    - ``--parallel``: auto-allocate a suffixed file in runtime state dir.
    - default: canonical ``<skill>.json`` in runtime state dir.
    """
    repo_root = _detect_repo_root(search_dir).resolve()

    if state_file:
        sp = Path(state_file).resolve()
        try:
            sp.relative_to(repo_root)
        except ValueError:
            sys.exit(f"ERROR: --state path is outside the repository: {state_file}")
        if not _is_skill_state_filename(sp.name, skill_name):
            sys.exit(
                f"ERROR: --state must look like `{skill_name}.json` or "
                f"`{skill_name}-<id>.json` (got `{sp.name}`)"
            )
        return sp

    if parallel:
        return _next_parallel_state_path(skill_name, repo_root)

    # Fresh active same-skill session exists: auto-fan-out to parallel unless disabled.
    if find_state_file(skill_name, repo_root) is not None and auto_parallel_on_conflict_enabled():
        return _next_parallel_state_path(skill_name, repo_root)

    return runtime_state_path(skill_name, repo_root)


def _next_parallel_state_path(skill_name: str, repo_root: Path) -> Path:
    state_dir = runtime_state_dir(repo_root)
    state_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    candidate = state_dir / f"{skill_name}-{stamp}.json"
    idx = 2
    while candidate.exists():
        candidate = state_dir / f"{skill_name}-{stamp}-{idx}.json"
        idx += 1
    return candidate


def auto_parallel_on_conflict_enabled() -> bool:
    """Whether step-1 should auto-allocate parallel state on same-skill conflicts."""
    v = os.environ.get("FORGE_AUTO_PARALLEL_ON_CONFLICT", "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _handoff_paths(name: str, search_dir: Path | None = None) -> tuple[Path, Path]:
    """Return canonical and legacy handoff paths for a skill name."""
    return (
        runtime_memory_dir(search_dir) / f"handoff-{name}.md",
        legacy_memory_dir(search_dir) / f"handoff-{name}.md",
    )


def read_handoff(name: str, search_dir: Path | None = None) -> str:
    """Read a handoff file from the runtime memory directory if it exists.

    Args:
        name: The skill name (e.g. "develop", "implement", "code-review").
        search_dir: Optional repo root override (mainly for tests).

    Returns:
        File content as string, or empty string if not found.
    """
    for handoff in _handoff_paths(name, search_dir):
        if handoff.exists():
            return handoff.read_text(encoding="utf-8")
    return ""


def close_handoff(name: str, search_dir: Path | None = None) -> bool:
    """Delete canonical + legacy handoff files for a skill.

    Returns True when at least one file was deleted.
    """
    removed = False
    for handoff in _handoff_paths(name, search_dir):
        if handoff.exists():
            handoff.unlink()
            removed = True
    return removed


def consume_handoff(name: str, search_dir: Path | None = None) -> str:
    """Read and close a handoff so it does not leak across later sessions."""
    content = read_handoff(name, search_dir=search_dir)
    if content:
        close_handoff(name, search_dir=search_dir)
    return content


def is_state_effectively_complete(state: SkillState) -> bool:
    """Treat legacy max-step states as complete when completed_at is absent."""
    if state.completed_at:
        return True
    if state.max_step <= 0:
        return False
    return state.current_step >= state.max_step and state.last_completed_step >= state.max_step


def stale_session_threshold_seconds() -> float:
    """Session inactivity threshold used to classify stale in-progress states."""
    raw = os.environ.get("FORGE_STALE_SESSION_HOURS", "24").strip()
    try:
        hours = float(raw)
    except ValueError:
        hours = 24.0
    if hours <= 0:
        hours = 24.0
    return hours * 3600.0


def _parse_iso_timestamp(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_state_stale(state: SkillState, path: Path) -> bool:
    """True when an in-progress state has not been touched recently."""
    if is_state_effectively_complete(state):
        return False
    touched = (
        _parse_iso_timestamp(state.last_touched_at)
        or _parse_iso_timestamp(state.started_at)
        or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    )
    age_seconds = (datetime.now(timezone.utc) - touched).total_seconds()
    return age_seconds > stale_session_threshold_seconds()


def is_evaluate_state_stale(data: dict[str, Any], path: Path) -> bool:
    """Staleness check for raw evaluate-state JSON objects."""
    touched = (
        _parse_iso_timestamp(data.get("last_touched_at"))
        or _parse_iso_timestamp(data.get("started_at"))
        or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    )
    age_seconds = (datetime.now(timezone.utc) - touched).total_seconds()
    return age_seconds > stale_session_threshold_seconds()


def read_memory_file(name: str) -> str:
    """Read a file from the runtime memory directory if it exists.

    Args:
        name: The filename (e.g. "project.md").

    Returns:
        File content as string, or empty string if not found.
    """
    for path in (
        runtime_memory_dir() / name,
        legacy_memory_dir() / name,
    ):
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_phase_todos(phase_todos: list[dict]) -> str:
    """Render a Codex plan-tracking block for the current phase.

    Uses json.dumps() for proper escaping of quotes, backslashes, newlines,
    and other special characters in todo content.
    """
    if not phase_todos:
        return ""

    # Build a list of safe todo dicts (only the three expected keys)
    safe_todos = [
        {
            "content": todo.get("content", ""),
            "activeForm": todo.get("activeForm", ""),
            "status": todo.get("status", "pending"),
        }
        for todo in phase_todos
    ]

    # json.dumps handles all escaping correctly
    todos_json = json.dumps(safe_todos, indent=2)

    return "\n".join([
        "## Create Phase Todos",
        "",
        "**IMMEDIATELY mirror these todos in Codex progress tracking before any other work.**",
        "Prefer `update_plan` by translating each item into a plan step with the same status.",
        "When work changes, keep the plan updated and add new steps for important sub-tasks.",
        "",
        "```json",
        todos_json,
        "```",
        "",
    ])


def build_skill_todos(
    phase_names: dict[int, str],
    phase_todos: dict[int, list[dict]],
    current_step: int,
    last_completed_step: int = 0,
) -> list[dict]:
    """Build a complete skill-level todo list covering all phases.

    Completed phases are marked 'completed', the current phase is
    'in_progress', and future phases are 'pending'.  Sub-tasks for the
    current phase are appended as 'pending' items.
    """
    todos: list[dict] = []
    for step_num in sorted(phase_names.keys()):
        name = phase_names[step_num]
        if step_num <= last_completed_step:
            status = "completed"
        elif step_num == current_step:
            status = "in_progress"
        else:
            status = "pending"

        todos.append({
            "content": name,
            "activeForm": f"Running {name}",
            "status": status,
        })

        # Add sub-tasks for the current phase only
        if step_num == current_step:
            for sub_todo in phase_todos.get(step_num, []):
                todos.append({
                    "content": f"  {sub_todo['content']}",
                    "activeForm": sub_todo["activeForm"],
                    "status": "pending",
                })

    return todos


def skill_token_from_script(script_path: Path) -> str:
    """Parent dir under scripts/ as a hyphenated CLI token (code_review → code-review)."""
    return script_path.parent.name.replace("_", "-")


def chain_command_to_agent_invocation(chain_cmd: str) -> str:
    """Map SKILL_CHAIN entries like 'evaluate --mode pre' to '$forge:evaluate --mode pre'."""
    chain_cmd = chain_cmd.strip()
    if not chain_cmd:
        return chain_cmd
    skill, sep, tail = chain_cmd.partition(" ")
    skill_h = skill.replace("_", "-")
    inv = f"$forge:{skill_h}"
    return f"{inv}{sep}{tail}" if sep else inv


def parse_continuation_command(cmd: str) -> tuple[int | None, str | None]:
    """Extract ``--step`` and ``--state`` from a line emitted by ``build_next_command``."""
    if not cmd.strip():
        return None, None
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return None, None
    next_step: int | None = None
    state_path: str | None = None
    i = 0
    while i < len(parts):
        if parts[i] == "--step" and i + 1 < len(parts):
            try:
                next_step = int(parts[i + 1])
            except ValueError:
                pass
            i += 2
            continue
        if parts[i] == "--state" and i + 1 < len(parts):
            state_path = parts[i + 1]
            i += 2
            continue
        i += 1
    return next_step, state_path


def format_same_skill_continuation(
    next_step: int,
    state_path: str | None = None,
    *,
    require_confirmation: bool = False,
) -> str:
    """Render same-skill continuation guidance.

    By default, deterministic next steps should auto-continue and avoid a
    confirmation prompt. Ask for confirmation only when the continuation target
    could not be parsed unambiguously.
    """
    bar = ("-" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("━" * 60)
    if require_confirmation:
        lines = [
            f"\n\n{bar}",
            "CONTINUATION",
            bar,
            "",
            f"This phase is complete. **Should I continue into step {next_step}?**",
            "",
            "Reply yes to move on, or say no / pause if you want to stop here.",
        ]
    else:
        lines = [
            f"\n\n{bar}",
            "CONTINUATION",
            bar,
            "",
            f"Next step is clear: continue directly to **step {next_step}**.",
            "",
            "Only pause if the user asked to stop or change direction.",
        ]
    if state_path:
        lines.extend(["", f"Resume context is saved at `{state_path}`."])
    return "\n".join(lines)


def format_workflow_transition(cross_skill_next: str) -> str:
    """Render a short cross-skill transition prompt.

    `cross_skill_next` is a skill name like "plan". Suggested invocation uses
    ``$forge:<skill>`` for IDE/agent routing.
    """
    bar = ("=" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("═" * 60)
    slug = cross_skill_next.strip().replace("_", "-")
    suggestion = f"$forge:{slug}"
    return (
        f"\n\n{bar}\n"
        f"WORKFLOW TRANSITION\n"
        f"{bar}\n"
        f"This skill is finished. **Suggested next:** `{suggestion}` (starts at step 1).\n"
        f"\n"
        f"Pause here unless the user asks to continue — confirm before switching skills.\n"
    )


def format_step_output(
    skill_name: str,
    step: int,
    max_step: int,
    phase_name: str,
    body: str,
    next_cmd: str | None = None,
    phase_todos: list[dict] | None = None,
    cross_skill_next: str | None = None,
    all_phase_names: dict[int, str] | None = None,
    all_phase_todos: dict[int, list[dict]] | None = None,
    handoff_menu: str | None = None,
    *,
    require_confirmation: bool | None = None,
) -> str:
    """Format step output with title, todos, body, and continuation directive.

    Args:
        skill_name: Name of the skill (e.g. "develop").
        step: Current step number.
        max_step: Maximum step number for this skill.
        phase_name: Human-readable phase name.
        body: The rendered prompt body.
        next_cmd: Command to run for the next step (None if final step).
        phase_todos: Optional list of todo dicts for current phase only (legacy).
        cross_skill_next: Optional next-skill command when at skill boundary.
        all_phase_names: Full dict of {step: phase_name} for the skill.
            When provided, a skill-level todo list is generated showing
            all phases with their completion status.
        all_phase_todos: Full dict of {step: [todo_dicts]} for the skill.
            Used alongside all_phase_names for sub-task detail.
        handoff_menu: Optional numbered handoff menu for final-step transitions.
        require_confirmation: When set, overrides auto-continue for same-skill
            continuation (e.g. workflow gates that must wait for user approval).
    """
    title = f"{skill_name.upper()} — {phase_name} (Step {step} of {max_step})"
    header = f"{title}\n{'=' * len(title)}\n\n"
    opt_in_section = forge_session_opt_in_banner(skill_name, step)
    graphify_section = forge_graphify_context_block(skill_name, step)

    # Step 1 may insert a session opt-in block, then phase todos (for Codex plan
    # mirroring), then body.
    if all_phase_names:
        # If caller provided a per-step phase_todos override (e.g. implement's
        # wave-scoped todos), use it for the current step's sub-tasks instead
        # of the generic all_phase_todos entry.
        effective_phase_todos = dict(all_phase_todos or {})
        if phase_todos is not None:
            effective_phase_todos[step] = phase_todos
        skill_todos = build_skill_todos(
            all_phase_names,
            effective_phase_todos,
            current_step=step,
            last_completed_step=step - 1,
        )
        todos_section = format_phase_todos(skill_todos)
    elif phase_todos:
        todos_section = format_phase_todos(phase_todos)
    else:
        todos_section = ""
    output = header + opt_in_section + graphify_section + todos_section + body

    if handoff_menu:
        output += "\n\n" + handoff_menu
    elif next_cmd:
        ns, sp_ = parse_continuation_command(next_cmd)
        confirm = require_confirmation if require_confirmation is not None else (ns is None)
        if ns is None:
            ns = step + 1
        output += format_same_skill_continuation(
            ns,
            sp_,
            require_confirmation=confirm,
        )
    elif cross_skill_next:
        output += "\n\nWORKFLOW COMPLETE — this skill has finished."
        output += format_workflow_transition(cross_skill_next)
    else:
        output += "\n\nWORKFLOW COMPLETE — return results to the user."

    return output


def build_next_command(
    script_path: Path,
    step: int,
    max_step: int,
    *,
    next_step: int | None = None,
    flags: tuple[str, ...] = (),
    **extra_args: str,
) -> str:
    """Build a compact continuation token line (``$forge:<skill> --step N …``).

    Shown to tooling parsers; same-step prompts use plain language via
    ``format_same_skill_continuation`` instead of echoing this string to users.
    """
    if step >= max_step:
        return ""
    target_step = next_step if next_step is not None else step + 1
    if target_step > max_step:
        return ""
    token = skill_token_from_script(script_path)
    parts: list[str] = [f"$forge:{token}", f"--step {target_step}"]
    for flag in flags:
        parts.append(f"--{flag}")
    for key, val in extra_args.items():
        parts.append(f"--{key} {shlex.quote(val)}")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Handoff file generation
# ---------------------------------------------------------------------------

def write_handoff(
    skill_name: str,
    state: SkillState,
    context: dict[str, str],
    suggested_next: str,
    memory_dir: Path | None = None,
) -> Path:
    """Write a handoff file to the runtime memory directory.

    Args:
        skill_name: Name of the completing skill.
        state: Current skill state.
        context: Key-value pairs of context for the next skill.
        suggested_next: Suggested next command string.
        memory_dir: Override memory directory path.

    Returns:
        Path to the written handoff file.
    """
    if memory_dir is None:
        memory_dir = runtime_memory_dir()
    memory_dir.mkdir(parents=True, exist_ok=True)

    handoff_path = memory_dir / f"handoff-{skill_name}.md"
    now = datetime.now(timezone.utc).isoformat()

    lines = [
        f"# Handoff: {skill_name} → {suggested_next.split()[0] if suggested_next else 'next'}",
        "",
        "## Completed",
        f"- **Skill:** {skill_name}",
        f"- **Timestamp:** {now}",
        f"- **Status:** complete",
        f"- **Quick mode:** {state.quick_mode}",
        "",
        "## Context for Next Skill",
    ]

    for key, val in context.items():
        lines.append(f"- **{key}:** {val}")

    lines.extend([
        "",
        "## Beads State",
        f"- **Epic:** {state.epic_id or 'N/A'}",
        f"- **Open issues:** {', '.join(k for k, v in state.issue_ids.items()) or 'none'}",
        "",
        "## Suggested Next",
        f"`{suggested_next}`" if suggested_next else "(end of flow)",
        "",
    ])

    handoff_path.write_text("\n".join(lines), encoding="utf-8")
    return handoff_path


def skill_run_memory_path(
    skill_name: str,
    search_dir: Path | None = None,
    memory_dir: Path | None = None,
) -> Path:
    """Path to per-skill run-memory jsonl file."""
    md = memory_dir or runtime_memory_dir(search_dir)
    return md / f"{skill_name}-runs.jsonl"


def append_skill_run_memory(
    skill_name: str,
    step: int,
    phase: str,
    summary: str,
    *,
    state: Any | None = None,
    state_path: Path | None = None,
    handoff_path: Path | None = None,
    max_entries: int = RUN_HISTORY_MAX_ENTRIES,
    search_dir: Path | None = None,
    memory_dir: Path | None = None,
) -> Path:
    """Append an auditable run entry and cap history to the most recent entries."""
    md = memory_dir or runtime_memory_dir(search_dir)
    md.mkdir(parents=True, exist_ok=True)
    history_path = skill_run_memory_path(skill_name, search_dir=search_dir, memory_dir=md)
    timestamp = now_iso()

    state_path_str = str(state_path.resolve()) if isinstance(state_path, Path) else (
        str(Path(state_path).resolve()) if state_path else ""
    )
    handoff_path_str = str(handoff_path.resolve()) if isinstance(handoff_path, Path) else (
        str(Path(handoff_path).resolve()) if handoff_path else ""
    )

    started_at = getattr(state, "started_at", None) if state is not None else None
    session_ref = f"{skill_name}:{state_path_str or '(no-state)'}:{started_at or '(unknown-start)'}"
    handoff_ref = handoff_path_str or "(none)"

    entry: dict[str, Any] = {
        "timestamp": timestamp,
        "skill": skill_name,
        "step": int(step),
        "phase": phase,
        "summary": summary.strip(),
        "session_ref": session_ref,
        "state_path": state_path_str,
        "session_started_at": started_at,
        "handoff_ref": handoff_ref,
        "handoff_path": handoff_path_str,
    }
    if state is not None:
        entry["current_step"] = getattr(state, "current_step", None)
        entry["last_completed_step"] = getattr(state, "last_completed_step", None)
        entry["max_step"] = getattr(state, "max_step", None)
        entry["completed_at"] = getattr(state, "completed_at", None)
        entry["quick_mode"] = bool(getattr(state, "quick_mode", False))

    records: list[dict[str, Any]] = []
    if history_path.exists():
        for line in history_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                records.append(obj)

    records.append(entry)
    keep = max(1, int(max_entries))
    records = records[-keep:]

    history_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=True, separators=(",", ":")) for r in records) + "\n",
        encoding="utf-8",
    )
    return history_path


def build_skill_handoff_menu(
    skill_name: str,
    state: SkillState | None = None,
    state_path: Path | None = None,
) -> str:
    """Build a numbered handoff menu for skill-chain transitions.

    Renders an interactive menu at the final step showing:
    - Default next command (e.g. "plan" for develop)
    - Numbered alternatives (e.g. "evaluate --mode pre", "implement")
    - Stop option to exit without transitioning
    - State file location for resuming

    Args:
        skill_name: Current skill name (e.g. "develop", "plan")
        state: Optional SkillState for context-aware menu adjustments
        state_path: Optional Path to state file for display

    Returns:
        Formatted menu string ready for insertion into prompt output.
    """
    from scripts.shared.skill_chain import SKILL_CHAIN, COMMAND_DESCRIPTIONS

    transition = SKILL_CHAIN.get(skill_name)
    if not transition:
        # Fallback for undefined skills
        return f"\nWORKFLOW HANDOFF — {skill_name} complete\n\nNo configured next skill."

    default_cmd = transition.default
    alternatives = list(transition.alternatives) or []

    # Diagnose: large/systemic incidents default to develop → plan; localized complex defaults to plan
    if skill_name == "diagnose" and state is not None:
        fc = str(state.custom.get("fix_complexity", "unknown")).lower()
        base_alts = list(transition.alternatives) or []
        if fc == "large":
            default_cmd = "develop"
            alternatives = [command for command in base_alts if command != "develop"]
        elif fc == "complex":
            default_cmd = "plan"
            alternatives = [command for command in base_alts if command != "plan"]

    # Context-aware injection: test skill with failures prepends diagnose
    if skill_name == "test" and state:
        test_results = state.custom.get("test_results", {})
        failed = test_results.get("failed", 0)
        if failed > 0 and "diagnose" not in alternatives:
            alternatives.insert(0, "diagnose")

    # Test skill mode switching: swap test --mode flows with test --mode run
    if skill_name == "test" and state:
        mode = state.custom.get("mode", "run")
        if mode == "flows" and "test --mode flows" in alternatives:
            idx = alternatives.index("test --mode flows")
            alternatives[idx] = "test --mode run"
        elif mode == "run" and "test --mode run" in alternatives:
            idx = alternatives.index("test --mode run")
            alternatives[idx] = "test --mode flows"

    # Build the menu
    lines = [
        "",
        f"WORKFLOW HANDOFF — {skill_name} complete",
        "",
    ]

    option_num = 1
    if default_cmd:
        desc = COMMAND_DESCRIPTIONS.get(default_cmd, "")
        desc_text = f" ({desc})" if desc else ""
        inv = chain_command_to_agent_invocation(default_cmd)
        lines.append(f'**Default (reply "yes" or "1"):**')
        lines.append(f"1. `{inv}`{desc_text}")
        option_num = 2
    else:
        lines.append("**(none — workflow terminates here)**")

    if alternatives:
        lines.append("")
        lines.append("**Alternatives:**")
        for alt_cmd in alternatives:
            desc = COMMAND_DESCRIPTIONS.get(alt_cmd, "")
            desc_text = f" ({desc})" if desc else ""
            inv_a = chain_command_to_agent_invocation(alt_cmd)
            lines.append(f"{option_num}. `{inv_a}`{desc_text}")
            option_num += 1

    lines.append("")
    lines.append("**To stop without transitioning:**")
    lines.append("Reply 'stop' (stop) and the workflow will end here.")

    if state_path:
        lines.append("")
        lines.append(f"**State file:** `{state_path}`")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dashboard rendering
# ---------------------------------------------------------------------------

def render_dashboard(state: SkillState) -> str:
    """Render a skill completion dashboard."""
    open_count = len(state.open_findings())
    resolved_count = len(state.findings) - open_count
    agents = set()
    for d in state.dispatches:
        name = d.agent if isinstance(d, AgentDispatch) else d.get("agent", "unknown")
        agents.add(name)

    lines = [
        "## forge — Skill Summary",
        f"**Skill:** {state.skill_name}",
        f"**Status:** {'COMPLETE' if state.completed_at else 'IN_PROGRESS'}",
        f"**Started:** {state.started_at or 'N/A'}",
        f"**Completed:** {state.completed_at or 'N/A'}",
        f"**Agents dispatched:** {', '.join(sorted(agents)) or 'none'}",
        f"**Findings:** {open_count} open, {resolved_count} resolved",
        f"**Beads:** {state.epic_id or 'N/A'}",
        f"**Quick mode:** {state.quick_mode}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_base_parser(skill_name: str, max_step: int) -> argparse.ArgumentParser:
    """Build the base argument parser for a skill orchestrator."""
    parser = argparse.ArgumentParser(
        description=f"forge {skill_name} skill orchestrator"
    )
    parser.add_argument(
        "--step", type=int, required=True,
        help=f"Phase number (1-{max_step})"
    )
    parser.add_argument(
        "--state", type=str, default=None,
        help="Path to state file (auto-detected if omitted; step 1 supports custom paths)"
    )
    parser.add_argument(
        "--parallel", action="store_true",
        help=(
            "Start a parallel same-skill session by creating a suffixed state file "
            f"(`{skill_name}-<timestamp>.json`)."
        ),
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick mode: minimal review loops, lead agents only"
    )
    return parser


def validate_step(step: int, max_step: int) -> None:
    """Validate step number is in range."""
    if step < 1 or step > max_step:
        sys.exit(f"ERROR: --step must be 1-{max_step}")


def check_same_skill_clobber(
    skill_name: str,
    *,
    allow_parallel: bool = False,
    target_state_path: Path | None = None,
) -> None:
    """Abort if a same-skill state file exists with in-progress work.

    Call from a skill's `handle_step_1` (fresh-start path only). Subsequent
    steps explicitly pass `--state <path>` and must not be blocked by this
    check — they're the resume signal.

    Checks every plausible location: the canonical write target
    (`runtime_state_path` with default REPO_ROOT) AND any state file
    discoverable from the current cwd. The dual check matters because
    skills write to REPO_ROOT but a user could be invoking from elsewhere;
    the clobber needs to fire either way.

    Cross-skill conflicts remain warning-only via the existing
    `format_active_session_warning` flow; this function only handles the
    *same-skill* case where the user would otherwise silently overwrite
    in-progress state.
    """
    # Default behavior (single-session mode): block when any in-progress same-skill
    # session exists.
    candidates = [
        p
        for p in _state_path_candidates(skill_name, _detect_repo_root())
        if p.exists()
    ]
    if allow_parallel and target_state_path is not None:
        # Parallel mode still protects against overwriting the chosen file.
        candidates = [target_state_path] if target_state_path.exists() else []

    for path in candidates:
        if not path.exists():
            continue
        try:
            state = load_state(path)
        except Exception:
            # Corrupt state — leave it for the regular load path to surface.
            continue
        if is_state_stale(state, path):
            continue
        if not is_state_effectively_complete(state) and state.current_step > 0:
            sys.exit(
                f"ERROR: A `{skill_name}` session is already in progress "
                f"(step {state.current_step}/{state.max_step}, started "
                f"{state.started_at}, session_id {state.session_id}).\n"
                f"State file: {path}\n"
                f"Run `python3 scripts/shared/resume.py` to continue it, "
                f"or use `--parallel` / `--state {skill_name}-<id>.json` "
                f"to start another session."
            )


def validate_step_or_complete(step: int, max_step: int, skill_name: str) -> bool:
    """Soft step validator: tolerates over-cap steps as 'already complete'.

    Returns True when the requested step is past the skill's final step —
    caller should print a friendly 'workflow complete' message and exit 0
    without mutating state. Returns False for in-range steps. Hard-errors
    (sys.exit) for negative or zero steps.

    Use this at skill entry points where the LLM may overshoot after the
    final step; keep `validate_step` for code paths that depend on its
    sys.exit contract (e.g. existing tests).
    """
    if step < 1:
        sys.exit(f"ERROR: --step must be >= 1 (got {step})")
    if step > max_step:
        print(
            f"`{skill_name}` ends at step {max_step}; nothing left to do.\n"
            f"Run `python3 scripts/shared/resume.py` to continue the next pipeline skill, "
            f"or start a new workflow.",
            file=sys.stderr,
        )
        return True
    return False


def now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()
