"""Regression tests for the "skills friction" documentation + behavior fixes.

Covers: default handoff routing (test/evaluate/diagnose), design handoff step
resolution, same-step re-run continuation wording, build_next_command with
next_step == current step on the max step (plan skeleton-incomplete case),
cli_inspect recognizing "/forge:" continuation lines, and structural probe
scope resolution not leaking non-path tokens like "HEAD".
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def add_repo_to_path():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# 1. resolve_next_skill — test green/red, evaluate post, diagnose large
# ---------------------------------------------------------------------------

def test_resolve_next_skill_test_green_defaults_to_ship():
    from scripts.shared.handoff_menu import resolve_next_skill
    from scripts.shared.skill_state import SkillState

    state = SkillState(skill_name="test", max_step=6)
    state.custom["test_results"] = {"failed": 0, "passed": 10}
    state.custom["mode"] = "run"

    default, alts = resolve_next_skill("test", state)

    assert default == "ship"
    assert "diagnose" in alts


def test_resolve_next_skill_test_red_defaults_to_diagnose():
    from scripts.shared.handoff_menu import resolve_next_skill
    from scripts.shared.skill_state import SkillState

    state = SkillState(skill_name="test", max_step=6)
    state.custom["test_results"] = {"failed": 3, "passed": 7}
    state.custom["mode"] = "run"

    default, alts = resolve_next_skill("test", state)

    assert default == "diagnose"
    assert "ship" in alts


def test_resolve_next_skill_evaluate_post_defaults_to_code_review():
    from scripts.shared.handoff_menu import resolve_next_skill
    from scripts.shared.skill_state import SkillState

    state = SkillState(skill_name="evaluate", max_step=8)
    state.custom["mode"] = "post"

    default, alts = resolve_next_skill("evaluate", state)

    assert default == "code-review"
    assert "code-review" not in alts


def test_resolve_next_skill_evaluate_pre_defaults_to_implement():
    from scripts.shared.handoff_menu import resolve_next_skill
    from scripts.shared.skill_state import SkillState

    state = SkillState(skill_name="evaluate", max_step=7)
    state.custom["mode"] = "pre"

    default, alts = resolve_next_skill("evaluate", state)

    assert default == "implement"
    assert "implement" not in alts


def test_resolve_next_skill_diagnose_large_defaults_to_design_via_suggested_next():
    """diagnose_steps.suggested_next_for_complexity must agree with the
    resolve_next_skill override — both must say "design" (not "develop") for
    large fix_complexity.
    """
    from scripts.diagnose.diagnose_steps import suggested_next_for_complexity
    from scripts.shared.handoff_menu import resolve_next_skill
    from scripts.shared.skill_state import SkillState

    assert suggested_next_for_complexity("large") == "design"

    state = SkillState(skill_name="diagnose", max_step=7)
    state.custom["fix_complexity"] = "large"

    default, alts = resolve_next_skill("diagnose", state)

    assert default == "design"
    assert "develop" not in alts
    assert "design" not in alts


def test_resolve_next_skill_diagnose_complex_defaults_to_plan():
    from scripts.diagnose.diagnose_steps import suggested_next_for_complexity
    from scripts.shared.handoff_menu import resolve_next_skill
    from scripts.shared.skill_state import SkillState

    assert suggested_next_for_complexity("complex") == "plan"

    state = SkillState(skill_name="diagnose", max_step=7)
    state.custom["fix_complexity"] = "complex"

    default, alts = resolve_next_skill("diagnose", state)

    assert default == "plan"
    assert "plan" not in alts


# ---------------------------------------------------------------------------
# 2. step_for_phase — design "handoff" phase resolves to step 8
# ---------------------------------------------------------------------------

def test_step_for_phase_design_handoff_is_step_8():
    from scripts.shared.skill_phases import step_for_phase

    assert step_for_phase("design", "handoff") == 8


def test_step_for_phase_develop_alias_resolves_like_design():
    from scripts.shared.skill_phases import step_for_phase

    assert step_for_phase("develop", "handoff") == 8


# ---------------------------------------------------------------------------
# 3. format_same_skill_continuation — await_same_step re-run wording
# ---------------------------------------------------------------------------

def test_format_same_skill_continuation_await_same_step_says_rerun():
    from scripts.shared.orchestrator import format_same_skill_continuation

    text = format_same_skill_continuation(3, await_same_step=True)

    assert "Re-run this step" in text
    assert "Should I continue" not in text


def test_format_same_skill_continuation_require_confirmation_without_await():
    from scripts.shared.orchestrator import format_same_skill_continuation

    text = format_same_skill_continuation(3, require_confirmation=True)

    assert "Should I continue" in text
    assert "Re-run this step" not in text


# ---------------------------------------------------------------------------
# 4. build_next_command — next_step == current step on max step (plan
#    skeleton-incomplete re-run case)
# ---------------------------------------------------------------------------

def test_build_next_command_same_step_on_max_step_is_not_empty(monkeypatch, tmp_path):
    from scripts.shared.orchestrator import build_next_command

    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "slash")
    max_step = 7
    cmd = build_next_command(
        Path("scripts/plan/plan.py"),
        max_step,
        max_step,
        next_step=max_step,
        state=str(tmp_path / "session.json"),
    )

    assert cmd != ""
    assert "/forge:plan" in cmd
    assert "--phase" in cmd


def test_build_next_command_max_step_without_next_step_is_empty():
    from scripts.shared.orchestrator import build_next_command

    cmd = build_next_command(Path("scripts/plan/plan.py"), 7, 7)

    assert cmd == ""


# ---------------------------------------------------------------------------
# 5. cli_inspect recognizes "/forge:plan --step 2" continuation lines
# ---------------------------------------------------------------------------

def test_cli_inspect_recognizes_slash_forge_continuation_line():
    from forge_next.cli_inspect import summarize_orchestrator_output

    human_output = (
        "PLAN — Architecture Dispatch (Step 1 of 7)\n"
        "\n"
        "Some step body text.\n"
        "\n"
        "/forge:plan --step 2\n"
    )

    summary = summarize_orchestrator_output(Path("/repo"), "forge plan --step 1", human_output)

    assert summary["next_cmd"] == "/forge:plan --step 2"


def test_cli_inspect_still_recognizes_dollar_forge_continuation_line():
    from forge_next.cli_inspect import summarize_orchestrator_output

    human_output = "$forge:plan --step 2\n"

    summary = summarize_orchestrator_output(Path("/repo"), "forge plan --step 1", human_output)

    assert summary["next_cmd"] == "$forge:plan --step 2"


# ---------------------------------------------------------------------------
# 6. resolve_effective_scope_paths — does not keep "HEAD" as a path
# ---------------------------------------------------------------------------

def test_resolve_effective_scope_paths_does_not_return_head_token(tmp_path, monkeypatch):
    from scripts.shared.structural_probes import resolve_effective_scope_paths

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()

    paths, note = resolve_effective_scope_paths(
        tmp_path,
        ["HEAD"],
        skill_name="code-review",
        step=3,
    )

    assert "HEAD" not in paths


def test_resolve_effective_scope_paths_passthrough_for_unscoped_skill(tmp_path):
    from scripts.shared.structural_probes import resolve_effective_scope_paths

    paths, note = resolve_effective_scope_paths(
        tmp_path,
        ["HEAD"],
        skill_name="implement",
        step=4,
    )

    # Only code-review step 3 / evaluate post step 4 / evaluate review step 1
    # are scoped; other skill/step combos pass tokens through unchanged.
    assert paths == ["HEAD"]


# ---------------------------------------------------------------------------
# 7. CLI forwards --effort / --no-structural to code-review
# ---------------------------------------------------------------------------

def test_cli_passthrough_effort_and_no_structural():
    from forge_next.cli_dispatch import _passthrough_argv
    from tests.helpers.forge_test_fixtures import empty_passthrough_args

    argv = _passthrough_argv(
        empty_passthrough_args(effort="light", structural=False, step=3, mode="pr", target=["scripts/shared/skill_chain.py"])
    )
    assert "--effort" in argv
    assert "light" in argv
    assert "--no-structural" in argv


def test_cli_passthrough_structural_true():
    from forge_next.cli_dispatch import _passthrough_argv
    from tests.helpers.forge_test_fixtures import empty_passthrough_args

    argv = _passthrough_argv(empty_passthrough_args(effort="thorough", structural=True))
    assert "--structural" in argv
    assert "--no-structural" not in argv


# ---------------------------------------------------------------------------
# 8. takeover router sorts sessions with None started_at
# ---------------------------------------------------------------------------

def test_takeover_router_sorts_sessions_with_none_started_at(tmp_path):
    from scripts.takeover.router import build_route_plan

    sessions = [
        {"skill": "plan", "path": str(tmp_path / "a"), "session_id": "aaaa", "started_at": None},
        {
            "skill": "implement",
            "path": str(tmp_path / "b"),
            "session_id": "bbbb",
            "started_at": "2026-07-18T12:00:00Z",
        },
    ]

    # Patch detect_active_sessions via monkeypatch in the caller's style
    import scripts.takeover.router as router

    original = router.detect_active_sessions
    router.detect_active_sessions = lambda _root: sessions
    try:
        plan, _inf = build_route_plan(repo_root=tmp_path, goal="ship-ready")
        assert plan.entry_skill == "implement"
        assert plan.active_session_id == "bbbb"
    finally:
        router.detect_active_sessions = original


# ---------------------------------------------------------------------------
# 9. highlight_regression is not high severity ("high" substring trap)
# ---------------------------------------------------------------------------

def test_is_high_severity_does_not_match_highlight_regression_substring():
    from scripts.diagnose.technique_coverage_policy import is_high_severity

    assert is_high_severity({"severity": "high"}) is True
    assert is_high_severity({"severity": "highlight_regression"}) is False
    assert is_high_severity({"incident_profile": "highlight_regression"}) is False
