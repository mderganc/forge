"""Tests for scripts.shared.structural_probes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.shared import structural_probes as sp


def test_should_run_probes_matrix() -> None:
    assert sp.should_run_probes("code-review", 3)
    assert not sp.should_run_probes("code-review", 2)
    assert sp.should_run_probes("evaluate", 4, mode="post")
    assert sp.should_run_probes("evaluate", 1, mode="review")
    assert not sp.should_run_probes("evaluate", 4, mode="pre")


def test_detect_stack_python_only(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("x=1\n", encoding="utf-8")
    stack = sp.detect_stack(tmp_path)
    assert stack["python"] is True
    assert stack["node"] is False


def test_run_probes_skip_without_node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "mod.py").write_text("def f():\n    pass\n", encoding="utf-8")
    state_dir = tmp_path / "state"
    monkeypatch.setattr(
        "forge_next.structural_tools.resolve_pyscn_command",
        lambda: None,
    )
    monkeypatch.setattr(
        "forge_next.structural_tools.resolve_knip_command",
        lambda: None,
    )
    monkeypatch.setattr(
        "forge_next.structural_tools.resolve_madge_command",
        lambda: None,
    )
    payload = sp.run_probes(tmp_path, state_dir=state_dir)
    knip = next(p for p in payload["probes"] if p["tool"] == "knip")
    assert knip["status"] == "skip"
    sidecar = state_dir / sp.SIDECAR_NAME
    assert sidecar.is_file()
    loaded = json.loads(sidecar.read_text(encoding="utf-8"))
    assert loaded["stack"]["node"] is False


def test_inject_appends_banner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    fake = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "stack": {"python": True, "node": False},
        "probes": [],
    }

    def fake_run(*_a, **_k):
        sp._write_sidecar(state_dir, fake)
        return fake

    monkeypatch.setattr(sp, "run_probes", fake_run)
    body, sidecar, payload = sp.inject_structural_probes_section(
        "body",
        skill_name="code-review",
        step=3,
        repo_root=tmp_path,
        state_dir=state_dir,
    )
    assert "STRUCTURAL PROBES" in body
    assert sidecar is not None
    assert payload is not None


def test_code_review_step3_mentions_sidecar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke: step 3 output includes structural-probes when injection runs."""
    import subprocess
    import sys

    from scripts.shared.orchestrator import SkillState, save_state

    repo = Path(__file__).resolve().parents[1]
    state = repo / ".codex" / "forge" / "state" / "code-review-structural-smoke.json"
    st = SkillState(skill_name="code-review", max_step=6, current_step=2)
    st.custom = {"mode": "pr", "target": ".", "target_tokens": ["."]}
    save_state(st, state)
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "code_review" / "code_review.py"),
            "--step",
            "3",
            "--state",
            str(state),
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    try:
        state.unlink(missing_ok=True)
    except OSError:
        pass
    assert proc.returncode == 0, proc.stderr
    assert "structural-probes" in proc.stdout.lower() or "STRUCTURAL PROBES" in proc.stdout
