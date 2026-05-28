"""Prompt parity and orchestrator smoke tests for structural quality probes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

STRUCTURAL_PROMPT_RELS = [
    "code-review/mode_selection.md",
    "code-review/diff_analysis.md",
    "code-review/architecture_check.md",
    "code-review/deep_dive.md",
    "post/code_quality.md",
    "review/team_dispatch.md",
    "pre/risk_dependencies.md",
]

STRUCTURAL_MARKER = "structural-quality-probes.md"


@pytest.fixture(autouse=True)
def _repo_path():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


@pytest.mark.parametrize("rel", STRUCTURAL_PROMPT_RELS)
def test_structural_prompts_reference_template(rel: str) -> None:
    text = (REPO_ROOT / "prompts" / rel).read_text(encoding="utf-8")
    assert STRUCTURAL_MARKER in text or ".structural-probes.json" in text


@pytest.mark.parametrize("rel", STRUCTURAL_PROMPT_RELS)
def test_packaged_structural_prompts_match_repo(rel: str) -> None:
    src = REPO_ROOT / "prompts" / rel
    packaged = REPO_ROOT / "forge_next" / "assets" / "prompts" / rel
    assert packaged.is_file(), f"missing packaged prompt: {rel}"
    assert src.read_text(encoding="utf-8") == packaged.read_text(encoding="utf-8")


def test_packaged_structural_quality_template_matches_repo() -> None:
    src = REPO_ROOT / "templates" / "structural-quality-probes.md"
    packaged = REPO_ROOT / "forge_next" / "assets" / "templates" / "structural-quality-probes.md"
    assert src.is_file()
    assert packaged.is_file()
    assert src.read_text(encoding="utf-8") == packaged.read_text(encoding="utf-8")


def test_eval_state_custom_roundtrip(tmp_path: Path) -> None:
    from scripts.evaluate.state import EvalState, load_state, save_state

    sp = tmp_path / ".evaluate-state.json"
    state = EvalState(plan_path="/tmp/plan.md", plan_name="plan")
    state.custom["structural_probes_sidecar"] = "/tmp/.structural-probes.json"
    save_state(state, sp)
    loaded = load_state(sp)
    assert loaded.custom.get("structural_probes_sidecar") == "/tmp/.structural-probes.json"


def test_evaluate_post_step4_injects_structural_banner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orchestrator step 4 (post) must append STRUCTURAL PROBES when probes run."""
    from scripts.evaluate.state import EvalState, save_state
    from scripts.shared import structural_probes as sp

    state_dir = REPO_ROOT / ".codex" / "forge" / "state" / "evaluate-post-step4-smoke"
    state_dir.mkdir(parents=True, exist_ok=True)
    plan = state_dir / "plan.md"
    plan.write_text("# Plan\n\n## Task 1\n\nDo thing.\n", encoding="utf-8")
    sp_file = state_dir / ".evaluate-state.json"
    st = EvalState(plan_path=str(plan), plan_name="plan", mode="post")
    st.current_step = 3
    st.last_completed_step = 3
    save_state(st, sp_file)

    fake = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "stack": {"python": True, "node": False},
        "probes": [],
    }
    monkeypatch.setattr(sp, "run_probes", lambda *_a, **_k: fake)

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "evaluate" / "evaluate.py"),
            "--step",
            "4",
            "--mode",
            "post",
            "--state",
            str(sp_file),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert "STRUCTURAL PROBES" in proc.stdout
    reloaded = json.loads(sp_file.read_text(encoding="utf-8"))
    assert "custom" in reloaded
    assert "structural_probes_sidecar" in reloaded.get("custom", {})
    try:
        sp_file.unlink(missing_ok=True)
        plan.unlink(missing_ok=True)
        state_dir.rmdir()
    except OSError:
        pass
