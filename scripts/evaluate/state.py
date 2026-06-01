"""State management for evaluate skill.

Persists evaluation state via :class:`~scripts.shared.orchestrator.SkillState`
(``skill_name='evaluate'``). Legacy ``.evaluate-state.json`` files without
``skill_name`` are upgraded on load.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from scripts.shared.findings import FindingsTracker
from scripts.shared.orchestrator import (
    EVALUATE_STATE_FILENAME,
    SkillState,
    clear_state_file,
    load_state as load_skill_state,
    save_state as save_skill_state,
)

STATE_FILENAME = EVALUATE_STATE_FILENAME
DEFAULT_STATE_PATH = Path(STATE_FILENAME)


def state_path_for_plan(plan_path: str) -> Path:
    """Return state file path alongside the plan being evaluated."""
    return Path(plan_path).resolve().parent / STATE_FILENAME


def _max_step_for_mode(mode: str | None) -> int:
    if mode == "review":
        return 5
    if mode == "post":
        return 8
    return 7


def _legacy_dict_to_skill(data: dict) -> SkillState:
    """Convert pre-SkillState evaluate JSON to SkillState."""
    mode = data.get("mode")
    skill = SkillState(skill_name="evaluate", max_step=_max_step_for_mode(mode))
    skill.current_step = data.get("current_step", 1)
    skill.last_completed_step = data.get("last_completed_step", 0)
    skill.findings = list(data.get("findings", []))
    skill.failure_count = data.get("failure_count", 0)
    skill.last_touched_at = data.get("last_touched_at")
    skill.session_id = data.get("session_id") or str(uuid4())
    skill.custom = dict(data.get("custom") or {})
    skill.custom["plan_path"] = data["plan_path"]
    skill.custom["plan_name"] = data["plan_name"]
    skill.custom["mode"] = mode
    skill.custom["referenced_files"] = data.get("referenced_files", [])
    skill.custom["review_round"] = data.get("review_round", 0)
    skill.custom["review_findings"] = data.get("review_findings", [])
    return skill


def _skill_to_eval_state(skill: SkillState) -> EvalState:
    custom = skill.custom or {}
    state = EvalState(
        plan_path=str(custom.get("plan_path", "")),
        plan_name=str(custom.get("plan_name", "")),
    )
    state.mode = custom.get("mode")
    state.current_step = skill.current_step
    state.last_completed_step = skill.last_completed_step
    state.referenced_files = list(custom.get("referenced_files") or [])
    state.findings_tracker = FindingsTracker.from_list(skill.findings)
    state.review_round = int(custom.get("review_round") or 0)
    state.review_findings = list(custom.get("review_findings") or [])
    state.custom = {
        k: v
        for k, v in custom.items()
        if k
        not in (
            "plan_path",
            "plan_name",
            "mode",
            "referenced_files",
            "review_round",
            "review_findings",
        )
    }
    state.failure_count = skill.failure_count
    state.last_touched_at = skill.last_touched_at
    state.session_id = skill.session_id
    return state


def _eval_to_skill(state: EvalState) -> SkillState:
    mode = state.mode
    skill = SkillState(skill_name="evaluate", max_step=_max_step_for_mode(mode))
    skill.current_step = state.current_step
    skill.last_completed_step = state.last_completed_step
    skill.findings = state.findings_tracker.to_list()
    skill.failure_count = state.failure_count
    skill.last_touched_at = state.last_touched_at
    skill.session_id = state.session_id
    skill.custom = dict(state.custom)
    skill.custom["plan_path"] = state.plan_path
    skill.custom["plan_name"] = state.plan_name
    skill.custom["mode"] = mode
    skill.custom["referenced_files"] = state.referenced_files
    skill.custom["review_round"] = state.review_round
    skill.custom["review_findings"] = state.review_findings
    return skill


@dataclass
class EvalState:
    """Evaluation session state (facade over SkillState fields in ``custom``)."""

    plan_path: str
    plan_name: str
    mode: str | None = None
    current_step: int = 1
    last_completed_step: int = 0
    referenced_files: list[str] = field(default_factory=list)
    findings_tracker: FindingsTracker = field(default_factory=FindingsTracker)
    review_round: int = 0
    review_findings: list[dict] = field(default_factory=list)
    custom: dict = field(default_factory=dict)
    failure_count: int = 0
    last_touched_at: str | None = None
    session_id: str = field(default_factory=lambda: str(uuid4()))

    def mark_step_complete(self, step: int) -> None:
        self.last_completed_step = step
        self.failure_count = 0

    @property
    def findings(self) -> list[dict]:
        return self.findings_tracker.to_list()

    def add_finding(self, phase: str, severity: str, title: str, detail: str) -> dict:
        f = self.findings_tracker.add(phase=phase, severity=severity, title=title, detail=detail)
        return f.to_dict()

    def to_dict(self) -> dict:
        """Legacy-shaped dict (tests); persisted files use SkillState.to_dict()."""
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
            "custom": self.custom,
            "failure_count": self.failure_count,
            "last_touched_at": self.last_touched_at,
            "session_id": self.session_id,
        }


def save_state(state: EvalState, path: Path = DEFAULT_STATE_PATH) -> None:
    """Write SkillState JSON atomically and refresh resume/memory sidecars."""
    skill = _eval_to_skill(state)
    save_skill_state(skill, path)


def load_state(path: Path = DEFAULT_STATE_PATH) -> EvalState:
    """Load evaluate state; upgrades legacy JSON without ``skill_name``."""
    if not path.exists():
        raise FileNotFoundError(f"No state file at {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise KeyError("State file is not a JSON object")
    if raw.get("skill_name") == "evaluate":
        skill = SkillState.from_dict(raw)
    else:
        for key in ("plan_path", "plan_name"):
            if key not in raw:
                raise KeyError(f"State file missing required field: {key}")
        skill = _legacy_dict_to_skill(raw)
    return _skill_to_eval_state(skill)


def clear_state(path: Path = DEFAULT_STATE_PATH) -> None:
    """Remove state file if it exists (orchestrator helper)."""
    clear_state_file(path)
