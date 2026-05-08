"""Shared findings tracking for evaluate and diagnose skills.

Provides a Finding dataclass and FindingsTracker for managing
evaluation/diagnostic findings with severity, dismissal, and escalation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Finding:
    """A single finding from an evaluation or diagnostic phase."""
    id: str
    phase: str
    severity: str  # "critical", "warning", "suggestion"
    title: str
    detail: str
    status: str = "open"  # "open", "dismissed"
    user_note: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Finding:
        return cls(**data)


class FindingsTracker:
    """Manages a collection of findings with add/dismiss/escalate operations."""

    def __init__(self) -> None:
        self._findings: list[Finding] = []
        self._counter: int = 0

    def add(self, phase: str, severity: str, title: str, detail: str) -> Finding:
        """Add a finding with auto-assigned sequential ID."""
        self._counter += 1
        finding = Finding(id=f"F{self._counter}", phase=phase, severity=severity, title=title, detail=detail)
        self._findings.append(finding)
        return finding

    def get(self, finding_id: str) -> Finding:
        """Get a finding by ID. Raises KeyError if not found."""
        for f in self._findings:
            if f.id == finding_id:
                return f
        raise KeyError(f"Finding {finding_id} not found")

    def dismiss(self, finding_id: str, reason: str) -> None:
        f = self.get(finding_id)
        f.status = "dismissed"
        f.user_note = reason

    def escalate(self, finding_id: str, new_severity: str) -> None:
        f = self.get(finding_id)
        f.severity = new_severity

    def filter_by_severity(self, severity: str) -> list[Finding]:
        return [f for f in self._findings if f.severity == severity]

    def open_findings(self) -> list[Finding]:
        return [f for f in self._findings if f.status != "dismissed"]

    def all(self) -> list[Finding]:
        return list(self._findings)

    def to_list(self) -> list[dict]:
        return [f.to_dict() for f in self._findings]

    @classmethod
    def from_list(cls, data: list[dict]) -> FindingsTracker:
        tracker = cls()
        for item in data:
            finding = Finding.from_dict(item)
            tracker._findings.append(finding)
            num = int(finding.id.lstrip("F"))
            if num > tracker._counter:
                tracker._counter = num
        return tracker
