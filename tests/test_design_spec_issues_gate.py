"""Tests for design spec → issues gate (.design-spec-issues.json)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.develop import spec_gate, spec_issues


def _write_spec_gate(sidecars: Path, spec_path: str) -> None:
    (sidecars / spec_gate.SPEC_GATE_FILE).write_text(
        json.dumps(
            {
                "spec_path": spec_path,
                "spec_written": True,
                "self_review_passed": True,
                "user_approved": True,
            }
        ),
        encoding="utf-8",
    )


def _valid_issues_payload(spec_path: str) -> dict:
    return {
        "spec_path": spec_path,
        "issues_written": True,
        "user_confirmed": True,
        "beads_mode": "degraded",
        "epic_id": "none",
        "issues": [
            {
                "id": "D-001",
                "title": "Add runtime layout module",
                "summary": "Introduce .forge/ as canonical runtime root.",
                "spec_sections": ["Chosen design"],
                "acceptance_criteria": ["Runtime writes only under .forge/"],
            }
        ],
    }


def test_validate_spec_issues_not_required() -> None:
    sp = Path("/tmp/state/session.json")
    ok, msg = spec_issues.validate_spec_issues_gate(sp, False)
    assert ok is True
    assert msg == ""


def test_validate_spec_issues_missing_sidecar(tmp_path: Path) -> None:
    sp = tmp_path / "session.json"
    sp.write_text("{}", encoding="utf-8")
    ok, msg = spec_issues.validate_spec_issues_gate(sp, True)
    assert ok is False
    assert ".design-spec-issues.json" in msg


def test_validate_spec_issues_happy_path(tmp_path: Path) -> None:
    sp = tmp_path / "session.json"
    sp.write_text("{}", encoding="utf-8")
    spec_path = "docs/forge/specs/2026-01-01-slug-design.md"
    _write_spec_gate(tmp_path, spec_path)
    side = spec_issues.gate_sidecar_path(sp)
    side.write_text(json.dumps(_valid_issues_payload(spec_path)), encoding="utf-8")

    ok, msg = spec_issues.validate_spec_issues_gate(sp, True)
    assert ok is True
    assert msg == ""


def test_validate_spec_issues_spec_path_mismatch(tmp_path: Path) -> None:
    sp = tmp_path / "session.json"
    sp.write_text("{}", encoding="utf-8")
    _write_spec_gate(tmp_path, "docs/forge/specs/a-design.md")
    side = spec_issues.gate_sidecar_path(sp)
    side.write_text(
        json.dumps(_valid_issues_payload("docs/forge/specs/b-design.md")),
        encoding="utf-8",
    )

    ok, msg = spec_issues.validate_spec_issues_gate(sp, True)
    assert ok is False
    assert "must match" in msg


def test_validate_spec_issues_override_requires_reason(tmp_path: Path) -> None:
    sp = tmp_path / "session.json"
    sp.write_text("{}", encoding="utf-8")

    ok, msg = spec_issues.validate_spec_issues_gate(
        sp,
        True,
        allow_incomplete=True,
        override_reason="",
        override_follow_up="track later",
    )
    assert ok is False
    assert "override" in msg.lower()

    ok, msg = spec_issues.validate_spec_issues_gate(
        sp,
        True,
        allow_incomplete=True,
        override_reason="user accepted risk",
        override_follow_up="split issues in plan step 1",
        override_timestamp="2026-01-01T00:00:00Z",
    )
    assert ok is True
    assert "overridden" in msg.lower()


def test_handoff_issues_summary() -> None:
    summary = spec_issues.handoff_issues_summary(_valid_issues_payload("x.md"))
    assert summary["Issue count"] == "1"
    assert summary["Beads mode"] == "degraded"
