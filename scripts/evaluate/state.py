"""State management for evaluate skill.

Persists evaluation state to a JSON file between steps.
The state file is ephemeral — deleted when evaluation completes.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from scripts.shared.findings import FindingsTracker

STATE_FILENAME = ".evaluate-state.json"
DEFAULT_STATE_PATH = Path(STATE_FILENAME)


def state_path_for_plan(plan_path: str) -> Path:
    """Return state file path alongside the plan being evaluated."""
    return Path(plan_path).resolve().parent / STATE_FILENAME


@dataclass
class EvalState:
    """Evaluation session state."""
    plan_path: str
    plan_name: str
    mode: str | None = None
    current_step: int = 1
    last_completed_step: int = 0
    referenced_files: list[str] = field(default_factory=list)
    findings_tracker: FindingsTracker = field(default_factory=FindingsTracker)
    review_round: int = 0
    review_findings: list[dict] = field(default_factory=list)
    failure_count: int = 0

    def mark_step_complete(self, step: int) -> None:
        """Mark a step as completed and reset the retry-failure counter."""
        self.last_completed_step = step
        self.failure_count = 0

    @property
    def findings(self) -> list[dict]:
        """Backward-compatible findings list."""
        return self.findings_tracker.to_list()

    def add_finding(self, phase: str, severity: str, title: str, detail: str) -> dict:
        """Add a finding via the shared tracker."""
        f = self.findings_tracker.add(phase=phase, severity=severity, title=title, detail=detail)
        return f.to_dict()

    def to_dict(self) -> dict:
        return {
            "plan_path": self.plan_path,
            "plan_name": self.plan_name,
            "mode": self.mode,
            "current_step": self.current_step,
            "last_completed_step": self.last_completed_step,
            "referenced_files": self.referenced_files,
            "findings": self.findings_tracker.to_list(),
            "review_round": self.review_round,
            "review_findings": self.review_findings,
            "failure_count": self.failure_count,
        }


def save_state(state: EvalState, path: Path = DEFAULT_STATE_PATH) -> None:
    """Write state to JSON file atomically (write-to-temp-then-rename)."""
    content = json.dumps(state.to_dict(), indent=2)
    # Write to temp file in same directory, then rename for atomicity
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        import os
        os.close(fd)  # close the fd; we'll write via Path
        Path(tmp).write_text(content)
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    mode = state.mode or "pre"
    if mode == "review":
        max_step = 5
    elif mode == "post":
        max_step = 8
    else:
        max_step = 7

    # Continuity snapshot (evaluate uses variable max_step by mode).
    try:
        from scripts.shared import resume_context

        resume_context.write_evaluate_resume_snapshot(
            plan_path=state.plan_path,
            plan_name=state.plan_name,
            mode=state.mode,
            current_step=state.current_step,
            last_completed_step=state.last_completed_step,
            max_step=max_step,
            state_path=path,
            failure_count=int(state.failure_count or 0),
            search_dir=None,
        )
    except Exception:
        pass
    try:
        from scripts.shared import memory_synthesis

        memory_synthesis.write_memory_synthesis_evaluate(
            plan_name=state.plan_name,
            mode=state.mode,
            current_step=state.current_step,
            last_completed_step=state.last_completed_step,
            max_step=max_step,
            state_path=path,
            search_dir=None,
        )
    except Exception:
        pass


def load_state(path: Path = DEFAULT_STATE_PATH) -> EvalState:
    """Load state from JSON file.

    Raises:
        FileNotFoundError: If state file doesn't exist.
        json.JSONDecodeError: If state file is corrupted.
        KeyError: If required fields are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"No state file at {path}")
    data = json.loads(path.read_text())
    # Validate required fields
    for key in ("plan_path", "plan_name"):
        if key not in data:
            raise KeyError(f"State file missing required field: {key}")
    state = EvalState(
        plan_path=data["plan_path"],
        plan_name=data["plan_name"],
    )
    state.mode = data.get("mode")
    state.current_step = data.get("current_step", 1)
    state.last_completed_step = data.get("last_completed_step", 0)
    state.referenced_files = data.get("referenced_files", [])
    state.findings_tracker = FindingsTracker.from_list(data.get("findings", []))
    state.review_round = data.get("review_round", 0)
    state.review_findings = data.get("review_findings", [])
    state.failure_count = data.get("failure_count", 0)
    return state


def clear_state(path: Path = DEFAULT_STATE_PATH) -> None:
    """Remove state file if it exists."""
    if path.exists():
        path.unlink()
