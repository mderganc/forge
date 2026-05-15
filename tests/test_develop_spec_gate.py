"""Tests for develop design-spec gate sidecar validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.develop import spec_gate


def test_validate_spec_gate_not_required() -> None:
    sp = Path("/tmp/fake/state/develop.json")
    ok, msg = spec_gate.validate_spec_gate(sp, False)
    assert ok is True
    assert msg == ""


def test_validate_spec_gate_missing_sidecar(tmp_path: Path) -> None:
    state_dir = tmp_path / ".codex" / "forge" / "state"
    state_dir.mkdir(parents=True)
    sp = state_dir / "develop.json"
    sp.write_text('{"skill_name":"develop"}', encoding="utf-8")
    ok, msg = spec_gate.validate_spec_gate(sp, True)
    assert ok is False
    assert "Missing" in msg or "invalid" in msg.lower()


def test_validate_spec_gate_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    docs = repo / "docs" / "forge" / "specs"
    docs.mkdir(parents=True)
    spec_file = docs / "2026-01-01-test-design.md"
    spec_file.write_text("# Design\n", encoding="utf-8")

    state_dir = repo / ".codex" / "forge" / "state"
    state_dir.mkdir(parents=True)
    sp = state_dir / "develop.json"

    side = spec_gate.gate_sidecar_path(sp)
    side.write_text(
        json.dumps(
            {
                "spec_path": "docs/forge/specs/2026-01-01-test-design.md",
                "spec_written": True,
                "self_review_passed": True,
                "user_approved": True,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(repo)
    ok, msg = spec_gate.validate_spec_gate(sp, True)
    assert ok is True
    assert msg == ""


def test_validate_spec_gate_override_requires_reason(tmp_path: Path) -> None:
    state_dir = tmp_path / ".codex" / "forge" / "state"
    state_dir.mkdir(parents=True)
    sp = state_dir / "develop.json"
    ok, msg = spec_gate.validate_spec_gate(
        sp,
        True,
        allow_incomplete=True,
        override_reason="",
        override_follow_up="do it later",
    )
    assert ok is False
