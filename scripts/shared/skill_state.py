"""Skill orchestrator state dataclasses (shared by all workflow skills)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ReviewLoopState:
    """Tracks review loop progress for a single stage gate."""

    round: int = 0
    self_review: str = "pending"
    cross_review: str = "pending"
    critic_review: str = "pending"
    pm_validation: str = "pending"
    findings: list[dict] = field(default_factory=list)

    # skylos: reserved — review round pass/fail aggregation per stage gate
    def is_clean(self) -> bool:
        return all(
            getattr(self, attr) == "pass"
            for attr in ("self_review", "cross_review", "critic_review", "pm_validation")
        )

    # skylos: reserved — advance review loop between rounds
    def reset_round(self) -> None:
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
    beads_available: bool = False
    epic_id: str | None = None
    issue_ids: dict[str, str] = field(default_factory=dict)
    review_loops: dict[str, ReviewLoopState] = field(default_factory=dict)
    dispatches: list[AgentDispatch] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    phase_todos: dict[str, list[dict]] = field(default_factory=dict)
    started_at: str | None = None
    completed_at: str | None = None
    last_touched_at: str | None = None
    session_id: str = ""
    failure_count: int = 0
    custom: dict[str, Any] = field(default_factory=dict)

    # skylos: reserved — stage-gate review-loop API (not dead code; see docs/skylos-triage.md)
    def get_review_loop(self, step: int) -> ReviewLoopState:
        key = str(step)
        if key not in self.review_loops:
            self.review_loops[key] = ReviewLoopState()
        loop = self.review_loops[key]
        if isinstance(loop, dict):
            loop = ReviewLoopState.from_dict(loop)
            self.review_loops[key] = loop
        return loop

    # skylos: reserved — agent dispatch tracking for future orchestration wiring
    def record_dispatch(self, agent: str, step: int) -> AgentDispatch:
        dispatch = AgentDispatch(agent=agent, step=step, dispatched=True)
        self.dispatches.append(dispatch)
        return dispatch

    def add_finding(self, phase: str, severity: str, title: str, detail: str) -> dict:
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
        self.last_completed_step = step
        self.failure_count = 0

    def to_dict(self) -> dict:
        return {
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
