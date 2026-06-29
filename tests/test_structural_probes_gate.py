"""Tests for code-review structural probes gate (steps 4+)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.code_review.structural_probes_gate import (
    validate_structural_probes_gate,
)


def _write_sidecar(state_dir: Path, *, python: bool = True, node: bool = False) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    probes = []
    if python:
        probes.append(
            {
                "tool": "pyscn",
                "status": "pass",
                "command": ["pyscn", "analyze"],
                "summary": "ok",
                "findings": [],
            }
        )
    else:
        probes.append(
            {
                "tool": "pyscn",
                "status": "skip",
                "summary": "skipped",
                "findings": [],
            }
        )
    if node:
        probes.extend(
            [
                {
                    "tool": "knip",
                    "status": "pass",
                    "command": ["knip"],
                    "summary": "ok",
                    "findings": [],
                },
                {
                    "tool": "jscn",
                    "status": "pass",
                    "command": ["jscn", "analyze"],
                    "summary": "ok",
                    "findings": [],
                },
            ]
        )
    payload = {
        "stack": {"python": python, "node": node},
        "plan": {"stack_applicable": {"python": python, "node": node}},
        "probes": probes,
    }
    (state_dir / ".structural-probes.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def test_gate_fails_without_sidecar(tmp_path: Path) -> None:
    ok, msg = validate_structural_probes_gate(tmp_path, tmp_path)
    assert not ok
    assert "missing" in msg.lower()


def test_gate_passes_python_pyscn(tmp_path: Path) -> None:
    _write_sidecar(tmp_path, python=True, node=False)
    ok, msg = validate_structural_probes_gate(tmp_path, tmp_path)
    assert ok, msg


def test_gate_fails_when_pyscn_skipped(tmp_path: Path) -> None:
    state_dir = tmp_path / "session"
    _write_sidecar(state_dir, python=True, node=False)
    data = json.loads((state_dir / ".structural-probes.json").read_text(encoding="utf-8"))
    data["probes"][0]["status"] = "skip"
    (state_dir / ".structural-probes.json").write_text(json.dumps(data), encoding="utf-8")
    ok, msg = validate_structural_probes_gate(state_dir, tmp_path)
    assert not ok
    assert "pyscn" in msg


def test_gate_requires_knip_and_jscn_when_node(tmp_path: Path) -> None:
    state_dir = tmp_path / "session"
    _write_sidecar(state_dir, python=True, node=True)
    ok, msg = validate_structural_probes_gate(state_dir, tmp_path)
    assert ok, msg


def test_gate_fails_node_without_knip(tmp_path: Path) -> None:
    state_dir = tmp_path / "session"
    payload = {
        "stack": {"python": True, "node": True},
        "plan": {"stack_applicable": {"python": True, "node": True}},
        "probes": [
            {"tool": "pyscn", "status": "pass", "summary": "ok", "findings": []},
            {"tool": "knip", "status": "skip", "summary": "not installed", "findings": []},
            {"tool": "jscn", "status": "pass", "summary": "ok", "findings": []},
        ],
    }
    state_dir.mkdir(parents=True)
    (state_dir / ".structural-probes.json").write_text(json.dumps(payload), encoding="utf-8")
    ok, msg = validate_structural_probes_gate(state_dir, tmp_path)
    assert not ok
    assert "knip" in msg


def test_gate_fails_node_without_jscn(tmp_path: Path) -> None:
    state_dir = tmp_path / "session"
    payload = {
        "stack": {"python": True, "node": True},
        "plan": {"stack_applicable": {"python": True, "node": True}},
        "probes": [
            {"tool": "pyscn", "status": "pass", "summary": "ok", "findings": []},
            {"tool": "knip", "status": "pass", "summary": "ok", "findings": []},
            {"tool": "jscn", "status": "skip", "summary": "not installed", "findings": []},
        ],
    }
    state_dir.mkdir(parents=True)
    (state_dir / ".structural-probes.json").write_text(json.dumps(payload), encoding="utf-8")
    ok, msg = validate_structural_probes_gate(state_dir, tmp_path)
    assert not ok
    assert "jscn" in msg


def test_gate_override_requires_reason(tmp_path: Path) -> None:
    ok, msg = validate_structural_probes_gate(
        tmp_path,
        tmp_path,
        allow_incomplete=True,
        override_reason="",
        override_follow_up="will fix",
    )
    assert not ok


def test_code_review_step4_blocked_without_sidecar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.code_review.code_review as cr
    from scripts.shared.orchestrator import SkillState, save_state

    repo = tmp_path
    (repo / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    state_path = repo / ".codex" / "forge" / "sessions" / "abc" / "session.json"
    state_path.parent.mkdir(parents=True)
    st = SkillState(skill_name="code-review", max_step=6, current_step=3, last_completed_step=3)
    st.custom = {"mode": "pr", "target": "."}
    save_state(st, state_path)

    monkeypatch.chdir(repo)
    with pytest.raises(SystemExit) as exc:
        cr.handle_step_n(4, state_file=str(state_path))
    assert exc.value.code == 1
