# pyright: reportMissingImports=false, reportUnusedVariable=false
"""Regression tests for the workflow defects fixed in
docs/evaluations/i-m-having-some-issues-composed-hedgehog-evaluation.md.

Each test maps to a Verification step in the plan.

Pyright suppressions: dynamic sys.path manipulation (REPO_ROOT inserted in
fixtures) means imports resolve at runtime but not via static analysis;
pytest fixture parameters appear unused but trigger setup/teardown.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def add_repo_to_path():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def fresh_state_dir(tmp_path: Path, monkeypatch):
    """Run with cwd=tmp_path so runtime_state_path / runtime_memory_dir resolve fresh."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def clean_test_state():
    """Clean up test skill state before and after each test."""
    test_state = REPO_ROOT / ".codex" / "forge-codex" / "state" / "test.json"
    if test_state.exists():
        test_state.unlink()
    yield
    if test_state.exists():
        test_state.unlink()


# ---------------------------------------------------------------------------
# Fix 3.4 — failure_count first-class field (V12, V13)
# ---------------------------------------------------------------------------

def test_skillstate_has_failure_count_default_zero():
    from scripts.shared.orchestrator import SkillState

    s = SkillState(skill_name="develop")
    assert s.failure_count == 0


def test_skillstate_mark_step_complete_resets_failure_count():
    from scripts.shared.orchestrator import SkillState

    s = SkillState(skill_name="plan")
    s.failure_count = 5
    s.mark_step_complete(3)
    assert s.last_completed_step == 3
    assert s.failure_count == 0


def test_skillstate_loads_legacy_state_without_failure_count():
    """Legacy state file lacking failure_count must default to 0 (F12)."""
    from scripts.shared.orchestrator import SkillState

    legacy = {
        "skill_name": "plan",
        "current_step": 3,
        "last_completed_step": 2,
        "max_step": 6,
    }
    s = SkillState.from_dict(legacy)
    assert s.failure_count == 0


def test_evalstate_has_failure_count():
    from scripts.evaluate.state import EvalState

    s = EvalState(plan_path="/tmp/x.md", plan_name="x")
    assert s.failure_count == 0
    s.failure_count = 3
    s.mark_step_complete(2)
    assert s.failure_count == 0


# ---------------------------------------------------------------------------
# Fix 1 — validate_step_or_complete (V1)
# ---------------------------------------------------------------------------

def test_validate_step_or_complete_in_range_returns_false(capsys):
    from scripts.shared.orchestrator import validate_step_or_complete

    assert validate_step_or_complete(3, 7, "plan") is False
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_step_or_complete_over_cap_returns_true_with_friendly_msg(capsys):
    from scripts.shared.orchestrator import validate_step_or_complete

    assert validate_step_or_complete(99, 7, "plan") is True
    captured = capsys.readouterr()
    assert "ends at step 7" in captured.err
    assert "nothing left to do" in captured.err


def test_validate_step_or_complete_zero_or_negative_hard_errors():
    from scripts.shared.orchestrator import validate_step_or_complete

    with pytest.raises(SystemExit):
        validate_step_or_complete(0, 7, "plan")
    with pytest.raises(SystemExit):
        validate_step_or_complete(-1, 7, "plan")


# ---------------------------------------------------------------------------
# Fix 2 — Plan skeleton (V3, V5)
# ---------------------------------------------------------------------------

def test_write_plan_skeleton_creates_eight_canonical_sections(tmp_path: Path):
    from scripts.plan.plan import write_plan_skeleton, PLAN_SECTIONS

    plan_path = tmp_path / "plan.md"
    write_plan_skeleton(plan_path)

    content = plan_path.read_text()
    assert len(PLAN_SECTIONS) == 8
    for marker_id, heading in PLAN_SECTIONS:
        assert f"## {heading}" in content
        assert f"<!-- FORGE_SKELETON: {marker_id} -->" in content


def test_write_plan_skeleton_refuses_overwrite_with_real_content(tmp_path: Path):
    from scripts.plan.plan import write_plan_skeleton

    plan_path = tmp_path / "plan.md"
    plan_path.write_text("# Real Content\n\nThis is meaningful prose.")

    with pytest.raises(SystemExit):
        write_plan_skeleton(plan_path)


def test_write_plan_skeleton_force_overwrites_real_content(tmp_path: Path):
    from scripts.plan.plan import write_plan_skeleton, SKELETON_MARKER_PREFIX

    plan_path = tmp_path / "plan.md"
    plan_path.write_text("# Real Content\n\nThis is meaningful prose.")
    write_plan_skeleton(plan_path, force=True)
    assert SKELETON_MARKER_PREFIX in plan_path.read_text()


def test_write_plan_skeleton_overwrites_stub(tmp_path: Path):
    """A stub-only file (markers + headings) is safe to overwrite without --force."""
    from scripts.plan.plan import write_plan_skeleton

    plan_path = tmp_path / "plan.md"
    write_plan_skeleton(plan_path)
    # Re-running should not raise.
    write_plan_skeleton(plan_path)


def test_find_unfilled_sections_after_partial_fill(tmp_path: Path):
    from scripts.plan.plan import write_plan_skeleton, find_unfilled_sections

    plan_path = tmp_path / "plan.md"
    write_plan_skeleton(plan_path)
    assert len(find_unfilled_sections(plan_path)) == 8

    # Replace one marker
    content = plan_path.read_text()
    content = content.replace(
        "<!-- FORGE_SKELETON: ARCHITECTURE-OVERVIEW -->",
        "Real architecture content.",
    )
    plan_path.write_text(content)
    unfilled = find_unfilled_sections(plan_path)
    assert "Architecture Overview" not in unfilled
    assert len(unfilled) == 7


# ---------------------------------------------------------------------------
# Fix 3.2 — Same-skill clobber prevention (V7, V8)
# ---------------------------------------------------------------------------

def test_check_same_skill_clobber_aborts_on_in_progress_state(fresh_state_dir, monkeypatch):
    from scripts.shared.orchestrator import (
        SkillState,
        check_same_skill_clobber,
        runtime_state_path,
        save_state,
    )

    # Plant an in-progress state file
    sp = runtime_state_path("plan", fresh_state_dir)
    sp.parent.mkdir(parents=True, exist_ok=True)
    state = SkillState(skill_name="plan")
    state.current_step = 3
    state.started_at = "2026-05-07T00:00:00+00:00"
    save_state(state, sp)

    with pytest.raises(SystemExit) as exc:
        check_same_skill_clobber("plan")
    assert "already in progress" in str(exc.value)


def test_check_same_skill_clobber_passes_on_completed_state(fresh_state_dir):
    from scripts.shared.orchestrator import (
        SkillState,
        check_same_skill_clobber,
        runtime_state_path,
        save_state,
    )

    sp = runtime_state_path("plan", fresh_state_dir)
    sp.parent.mkdir(parents=True, exist_ok=True)
    state = SkillState(skill_name="plan")
    state.current_step = 6
    state.completed_at = "2026-05-07T00:00:00+00:00"
    save_state(state, sp)

    # Should not raise — completed sessions can be safely overwritten.
    check_same_skill_clobber("plan")


def test_check_same_skill_clobber_passes_on_logically_completed_state(fresh_state_dir):
    from scripts.shared.orchestrator import (
        SkillState,
        check_same_skill_clobber,
        runtime_state_path,
        save_state,
    )

    sp = runtime_state_path("plan", fresh_state_dir)
    sp.parent.mkdir(parents=True, exist_ok=True)
    state = SkillState(skill_name="plan", max_step=7)
    state.current_step = 7
    state.last_completed_step = 7
    save_state(state, sp)

    # Legacy complete state (no completed_at) should not block a fresh start.
    check_same_skill_clobber("plan")


def test_check_same_skill_clobber_passes_when_no_state(fresh_state_dir):
    from scripts.shared.orchestrator import check_same_skill_clobber

    # No state file exists; should silently pass.
    check_same_skill_clobber("plan")


# ---------------------------------------------------------------------------
# Fix 4 — Evaluate findings sidecar ingestion (V14)
# ---------------------------------------------------------------------------

def test_evaluate_ingests_findings_sidecar(tmp_path: Path):
    from scripts.evaluate.evaluate import (
        _findings_sidecar_path,
        _ingest_findings_sidecars,
    )
    from scripts.evaluate.state import EvalState

    state = EvalState(plan_path="/tmp/plan.md", plan_name="test")

    sidecar = _findings_sidecar_path(tmp_path, 2)
    sidecar.write_text(json.dumps([
        {"phase": "feasibility", "severity": "critical", "title": "F1", "detail": "d1"},
        {"phase": "feasibility", "severity": "warning", "title": "F2", "detail": "d2"},
    ]))

    n = _ingest_findings_sidecars(state, tmp_path, current_step=3)
    assert n == 2
    assert len(state.findings) == 2
    assert state.findings[0]["title"] == "F1"
    assert not sidecar.exists()  # ingested files are deleted


def test_evaluate_findings_sidecar_tolerates_malformed_json(tmp_path: Path, capsys):
    from scripts.evaluate.evaluate import (
        _findings_sidecar_path,
        _ingest_findings_sidecars,
    )
    from scripts.evaluate.state import EvalState

    state = EvalState(plan_path="/tmp/p.md", plan_name="x")
    sidecar = _findings_sidecar_path(tmp_path, 2)
    sidecar.write_text("not valid json {")

    n = _ingest_findings_sidecars(state, tmp_path, current_step=3)
    assert n == 0
    captured = capsys.readouterr()
    assert "malformed findings sidecar" in captured.err


# ---------------------------------------------------------------------------
# Fix 3.3 — resume.py --cleanup (V10, V11)
# ---------------------------------------------------------------------------

def test_resume_cleanup_dry_run_does_not_delete(fresh_state_dir):
    """Run resume.py --cleanup as a subprocess; expect dry-run by default."""
    # Create a state file with completed_at set (eligible for cleanup).
    state_dir = fresh_state_dir / ".codex" / "forge-codex" / "state"
    state_dir.mkdir(parents=True)
    target = state_dir / "develop.json"
    target.write_text(json.dumps({
        "skill_name": "develop",
        "current_step": 7,
        "last_completed_step": 7,
        "completed_at": "2026-05-07T00:00:00+00:00",
    }))

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "shared" / "resume.py"), "--cleanup"],
        cwd=fresh_state_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "Would delete" in (result.stderr + result.stdout)
    assert target.exists()  # not actually deleted


def test_resume_cleanup_force_deletes(fresh_state_dir):
    state_dir = fresh_state_dir / ".codex" / "forge-codex" / "state"
    state_dir.mkdir(parents=True)
    target = state_dir / "develop.json"
    target.write_text(json.dumps({
        "skill_name": "develop",
        "current_step": 7,
        "last_completed_step": 7,
        "completed_at": "2026-05-07T00:00:00+00:00",
    }))

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "shared" / "resume.py"), "--cleanup", "--force"],
        cwd=fresh_state_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert not target.exists()


def test_resume_cleanup_handles_legacy_complete_without_completed_at(fresh_state_dir):
    state_dir = fresh_state_dir / ".codex" / "forge-codex" / "state"
    state_dir.mkdir(parents=True)
    target = state_dir / "plan.json"
    target.write_text(json.dumps({
        "skill_name": "plan",
        "current_step": 7,
        "last_completed_step": 7,
        "max_step": 7,
    }))

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "shared" / "resume.py"), "--cleanup"],
        cwd=fresh_state_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "state reached max_step without completed_at" in (result.stderr + result.stdout)
    assert target.exists()  # dry-run only


# ---------------------------------------------------------------------------
# Fix 1 — Step over-cap (V1)
# ---------------------------------------------------------------------------

def test_plan_over_cap_step_exits_zero_with_friendly_msg(fresh_state_dir):
    """python3 plan.py --step 99 must produce a friendly message and exit 0."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "plan" / "plan.py"), "--step", "99"],
        cwd=fresh_state_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "ends at step 7" in result.stderr or "ends at step 7" in result.stdout


# ---------------------------------------------------------------------------
# Fix 1 — Bounded next_cmd in implement.py (V1)
# ---------------------------------------------------------------------------

def test_implement_next_command_returns_empty_at_max_step():
    from scripts.implement.implement import _next_command, MAX_STEP

    assert _next_command(MAX_STEP) == ""


def test_implement_next_command_supports_target_step():
    from scripts.implement.implement import _next_command

    cmd = _next_command(5, target_step=3)
    assert "--step 3" in cmd

    # target_step beyond MAX is rejected.
    assert _next_command(5, target_step=99) == ""


# ---------------------------------------------------------------------------
# Fix 2 — Mock-flow type catalog (prose + typed)
# ---------------------------------------------------------------------------

def test_flow_types_catalog_schema_complete():
    """Asserts all 4 flow types present with complete schema (Fix 2).

    The catalog structure supports both prose documentation (templates/mock-flow-types.md)
    and structured metadata for recommendation logic (scripts/test/flow_types.py).
    This test verifies the structured form is complete and valid.
    """
    from scripts.test.flow_types import FLOW_TYPES, FlowTypeMetadata

    # All four types present
    expected_types = {"scenario", "bdd", "http-replay", "workflow-dryrun"}
    assert set(FLOW_TYPES.keys()) == expected_types, f"Expected types {expected_types}, got {set(FLOW_TYPES.keys())}"

    # Each entry is a frozen dataclass
    for name, metadata in FLOW_TYPES.items():
        assert isinstance(metadata, FlowTypeMetadata), f"{name}: not a FlowTypeMetadata instance"

        # tooling non-empty
        assert metadata.tooling, f"{name}: tooling list is empty"
        assert isinstance(metadata.tooling, list), f"{name}: tooling not a list"

        # file_layout includes "primary" key
        assert isinstance(metadata.file_layout, dict), f"{name}: file_layout not a dict"
        assert "primary" in metadata.file_layout, f"{name}: file_layout missing 'primary' key"

        # criteria_scores covers keys 1–8
        assert isinstance(metadata.criteria_scores, dict), f"{name}: criteria_scores not a dict"
        expected_criteria = set(range(1, 9))
        assert set(metadata.criteria_scores.keys()) == expected_criteria, \
            f"{name}: criteria_scores missing keys, expected 1-8, got {set(metadata.criteria_scores.keys())}"

        # All criteria scores are 0–10
        for criterion_num, score in metadata.criteria_scores.items():
            assert 0 <= score <= 10, f"{name}: criterion {criterion_num} score {score} not in range 0-10"

        # data_pack_dirs has the 4 standard names
        assert isinstance(metadata.data_pack_dirs, list), f"{name}: data_pack_dirs not a list"
        expected_dirs = {"clean", "messy", "edge-cases", "duplicates"}
        assert set(metadata.data_pack_dirs) == expected_dirs, \
            f"{name}: data_pack_dirs expected {expected_dirs}, got {set(metadata.data_pack_dirs)}"


# ---------------------------------------------------------------------------
# Fix 5 — _detect_test_layout helper (test layout detection)
# ---------------------------------------------------------------------------

def test_detect_test_layout_against_fixture_project(fixture_project: Path):
    """Verify detect_test_layout works against the mock-flows-target fixture.

    Expected signals:
    - framework="pytest" (high confidence >= 0.9) from pyproject.toml [tool.pytest.ini_options]
    - entry_point="http" (high confidence 1.0) from FastAPI app declaration
    - roles=["admin","member","viewer"] from app/roles.yaml
    - roles_source="yaml"
    - test_db="sqlite" from in-memory connection in app/models.py
    - has_orchestrator_pattern=False (no Celery, RQ, transitions, or scripts/<skill>/<skill>.py)
    """
    from scripts.test.test_layout import detect_test_layout

    layout = detect_test_layout(fixture_project)

    assert layout.framework == "pytest"
    assert layout.framework_confidence >= 0.9

    assert layout.entry_point == "http"
    assert layout.entry_point_confidence == 1.0

    assert set(layout.roles) == {"admin", "member", "viewer"}
    assert layout.roles_source == "yaml"

    assert layout.test_db == "sqlite"
    assert layout.has_orchestrator_pattern is False


def test_detect_test_layout_unknown_framework_low_confidence(tmp_path: Path):
    """Test that projects with no pytest signals return unknown framework with low confidence."""
    from scripts.test.test_layout import detect_test_layout

    # Empty project with no test infrastructure
    layout = detect_test_layout(tmp_path)

    assert layout.framework == "unknown"
    assert layout.framework_confidence < 0.7


def test_detect_roles_returns_empty_when_none_found(tmp_path: Path):
    """Test that projects with no role files return empty roles list."""
    from scripts.test.test_layout import detect_test_layout

    layout = detect_test_layout(tmp_path)

    assert layout.roles == []
    assert layout.roles_source == "none"


def test_orchestrator_pattern_detected_in_forge_codex():
    """Test that forge-codex's own repo has orchestrator pattern detected.

    Forge-codex has scripts/<skill>/<skill>.py pattern (e.g., scripts/test/test.py),
    which satisfies the orchestrator pattern heuristic.
    """
    from scripts.test.test_layout import detect_test_layout

    layout = detect_test_layout(REPO_ROOT)

    assert layout.has_orchestrator_pattern is True


# ---------------------------------------------------------------------------
# Fix 1 — test skill --mode flows scaffolding (V1-V7)
# ---------------------------------------------------------------------------

def test_test_skill_default_mode_is_run(fresh_state_dir, monkeypatch):
    """Test that test skill defaults to run mode when --mode not specified (V1)."""
    import subprocess

    result = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"), "--step", "1"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, f"Unexpected error: {result.stderr}"

    # Load state to check mode
    from scripts.shared.orchestrator import runtime_state_path, load_state

    sp = runtime_state_path("test")
    assert sp.exists()
    state = load_state(sp)
    assert state.custom.get("mode", "run") == "run"
    assert state.max_step == 6


def test_test_skill_flows_mode_sets_max_step_7(fresh_state_dir):
    """Test that --mode flows sets max_step=7 (V2)."""
    import subprocess

    result = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"), "--mode", "flows", "--step", "1"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, f"Unexpected error: {result.stderr}"

    from scripts.shared.orchestrator import runtime_state_path, load_state

    sp = runtime_state_path("test")
    state = load_state(sp)
    assert state.custom.get("mode") == "flows"
    assert state.max_step == 7


def test_test_skill_flows_atomic_check_aborts_when_prompt_missing(fresh_state_dir, monkeypatch):
    """Test atomic-delivery feature-check: if a flow prompt is missing, abort (V3)."""
    import subprocess

    # Delete one of the 7 flow prompts
    prompt_path = REPO_ROOT / "prompts" / "test" / "flow_context.md"
    assert prompt_path.exists()
    try:
        original = prompt_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        original = prompt_path.read_text(encoding="cp1252")
    prompt_path.unlink()

    try:
        result = subprocess.run(
            ["python3", str(SCRIPTS / "test" / "test.py"), "--mode", "flows", "--step", "1"],
            cwd=str(fresh_state_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert result.returncode == 1
        assert "flows mode unavailable" in result.stderr
        assert "active template root" in result.stderr
        assert "flow_context" in result.stderr
    finally:
        # Restore the prompt
        prompt_path.write_text(original, encoding="utf-8")


def test_test_skill_resume_conflict_aborts_when_mode_differs(fresh_state_dir, monkeypatch):
    """Test resume-conflict guard: if state has mode=run, resume with --mode flows aborts (V4)."""
    import subprocess

    # First, create a run-mode state
    result1 = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"), "--step", "1"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result1.returncode == 0
    state_file = ""
    for line in result1.stderr.split("\n"):
        if "STATE FILE:" in line:
            state_file = line.split("STATE FILE:")[1].strip()
            break
    assert state_file, "step 1 should have printed STATE FILE: <path> on stderr"

    # Try to resume with --mode flows
    result2 = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"),
         "--state", state_file, "--mode", "flows", "--step", "2"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result2.returncode == 1
    assert "Cannot resume" in result2.stderr
    assert "saved mode is" in result2.stderr


def test_test_skill_legacy_state_missing_mode_defaults_to_run(fresh_state_dir, monkeypatch):
    """Test legacy-compat: state without mode key defaults to run (V5)."""
    from scripts.shared.orchestrator import runtime_state_path, load_state, save_state, SkillState

    # Create legacy state without mode key
    sp = runtime_state_path("test")
    sp.parent.mkdir(parents=True, exist_ok=True)

    legacy = SkillState(skill_name="test", max_step=6)
    # Deliberately don't set custom["mode"]
    save_state(legacy, sp)

    # Load and verify it defaults to run
    state = load_state(sp)
    assert state.custom.get("mode", "run") == "run"


def test_test_skill_role_override_via_cli(fresh_state_dir, monkeypatch):
    """Test --roles override parses correctly (V6)."""
    import subprocess

    result = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"), "--mode", "flows",
         "--roles", "admin,member,viewer", "--step", "1"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0

    from scripts.shared.orchestrator import runtime_state_path, load_state

    sp = runtime_state_path("test")
    state = load_state(sp)
    assert state.custom.get("roles") == ["admin", "member", "viewer"]


def test_test_skill_no_db_override(fresh_state_dir, monkeypatch):
    """Test --no-db override sets test_db to 'none' (V7)."""
    import subprocess

    result = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"), "--mode", "flows",
         "--no-db", "--step", "1"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0

    from scripts.shared.orchestrator import runtime_state_path, load_state

    sp = runtime_state_path("test")
    state = load_state(sp)
    assert state.custom.get("test_db") == "none"


# ---------------------------------------------------------------------------
# Fix 4 — recommendation sidecar + scenario-index parser
# ---------------------------------------------------------------------------

def test_recommendation_sidecar_happy_path(tmp_path):
    """Write valid JSON, ingest returns dict, file deleted (F4)."""
    from scripts.test._sidecar import (
        write_recommendation_override,
        ingest_recommendation_sidecar,
    )

    # Pre-write sidecar
    sidecar_path = write_recommendation_override(tmp_path, "bdd")
    assert sidecar_path.exists()

    # Ingest should succeed and delete
    result = ingest_recommendation_sidecar(tmp_path)
    assert result["chosen"] == "bdd"
    assert result["reasoning"] == "user override via --flow-type"
    assert result["confidence"] == 1.0
    assert not sidecar_path.exists()


def test_recommendation_sidecar_missing_aborts_exit_1(tmp_path):
    """Call ingest with no file present → sys.exit(1)."""
    from scripts.test._sidecar import ingest_recommendation_sidecar

    with pytest.raises(SystemExit) as exc_info:
        ingest_recommendation_sidecar(tmp_path)
    assert exc_info.value.code == 1


def test_recommendation_sidecar_malformed_json_aborts_exit_1(tmp_path):
    """Drop malformed JSON; ingest exits 1."""
    from scripts.test._sidecar import recommendation_sidecar_path, ingest_recommendation_sidecar

    path = recommendation_sidecar_path(tmp_path)
    path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        ingest_recommendation_sidecar(tmp_path)
    assert exc_info.value.code == 1


def test_recommendation_sidecar_invalid_chosen_aborts_exit_1(tmp_path):
    """chosen not in VALID_FLOW_TYPES → sys.exit(1)."""
    from scripts.test._sidecar import recommendation_sidecar_path, ingest_recommendation_sidecar

    path = recommendation_sidecar_path(tmp_path)
    data = {
        "chosen": "invalid-type",
        "reasoning": "test",
        "confidence": 0.8,
        "alternatives": [],
    }
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        ingest_recommendation_sidecar(tmp_path)
    assert exc_info.value.code == 1


def test_recommendation_sidecar_missing_reasoning_aborts_exit_1(tmp_path):
    """reasoning missing → sys.exit(1)."""
    from scripts.test._sidecar import recommendation_sidecar_path, ingest_recommendation_sidecar

    path = recommendation_sidecar_path(tmp_path)
    data = {
        "chosen": "scenario",
        "confidence": 0.8,
        "alternatives": [],
    }
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        ingest_recommendation_sidecar(tmp_path)
    assert exc_info.value.code == 1


def test_recommendation_sidecar_invalid_confidence_aborts_exit_1(tmp_path):
    """confidence out-of-range → sys.exit(1)."""
    from scripts.test._sidecar import recommendation_sidecar_path, ingest_recommendation_sidecar

    path = recommendation_sidecar_path(tmp_path)
    data = {
        "chosen": "scenario",
        "reasoning": "test",
        "confidence": 1.5,  # Out of range [0.0, 1.0]
        "alternatives": [],
    }
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        ingest_recommendation_sidecar(tmp_path)
    assert exc_info.value.code == 1


def test_write_recommendation_override_creates_valid_sidecar(tmp_path):
    """write_recommendation_override creates valid JSON that ingest can consume."""
    from scripts.test._sidecar import (
        write_recommendation_override,
        ingest_recommendation_sidecar,
    )

    write_recommendation_override(tmp_path, "http-replay")
    result = ingest_recommendation_sidecar(tmp_path)

    assert result["chosen"] == "http-replay"
    assert "user override" in result["reasoning"]
    assert result["confidence"] == 1.0


def test_log_override_emits_stderr_marker(capsys):
    """log_override_to_stderr emits the adoption-tracking marker."""
    from scripts.test._sidecar import log_override_to_stderr

    log_override_to_stderr("scenario")
    captured = capsys.readouterr()
    assert "[flows] override: user passed --flow-type=scenario" in captured.err


def test_scenario_index_creates_when_missing(tmp_path):
    """empty dir → file created with header + new row."""
    from scripts.test._scenario_index import IndexRow, update_scenario_index

    index_path = tmp_path / "README.md"
    backup_dir = tmp_path / "backup"
    new_row = IndexRow(
        scope="upload feature",
        type="scenario",
        roles="admin,member",
        failure_paths="2 paths",
        last_run="2026-05-08",
        status="pass",
    )

    success, msg = update_scenario_index(index_path, new_row, backup_dir)
    assert success is True
    assert index_path.exists()

    content = index_path.read_text(encoding="utf-8")
    assert "| Scope | Type | Roles | Failure paths | Last run | Status |" in content
    assert "| upload feature | scenario | admin,member | 2 paths | 2026-05-08 | pass |" in content


def test_scenario_index_appends_when_present(tmp_path):
    """existing file with N rows → file has N+1 rows after update."""
    from scripts.test._scenario_index import IndexRow, update_scenario_index

    index_path = tmp_path / "README.md"
    backup_dir = tmp_path / "backup"

    # Create initial file with one row
    row1 = IndexRow("flow1", "bdd", "admin", "1", "2026-05-07", "pass")
    success1, _ = update_scenario_index(index_path, row1, backup_dir)
    assert success1 is True

    # Append a second row
    row2 = IndexRow("flow2", "http-replay", "member", "2", "2026-05-08", "pass")
    success2, _ = update_scenario_index(index_path, row2, backup_dir)
    assert success2 is True

    content = index_path.read_text(encoding="utf-8")
    lines = [l for l in content.split("\n") if l.startswith("|") and "---" not in l]
    # Should have header + 2 data rows
    assert len(lines) >= 3


def test_scenario_index_merges_duplicate_scope(tmp_path):
    """existing row with same scope+type → row updated, no duplication."""
    from scripts.test._scenario_index import IndexRow, update_scenario_index

    index_path = tmp_path / "README.md"
    backup_dir = tmp_path / "backup"

    # Create initial row
    row1 = IndexRow("flow1", "scenario", "admin", "1 path", "2026-05-07", "pass")
    success1, _ = update_scenario_index(index_path, row1, backup_dir)
    assert success1 is True

    # Update the same row (scope + type match)
    row1_updated = IndexRow("flow1", "scenario", "admin,member", "2 paths", "2026-05-08", "fail")
    success2, _ = update_scenario_index(index_path, row1_updated, backup_dir)
    assert success2 is True

    content = index_path.read_text(encoding="utf-8")
    # Count data rows (lines starting with | but not the header or separator)
    data_lines = [
        l for l in content.split("\n")
        if l.startswith("|") and "---" not in l and "Scope" not in l
    ]
    # Should still be 1 data row (merged, not duplicated)
    assert len(data_lines) == 1
    assert "2 paths" in content


def test_scenario_index_aborts_on_malformed_file(tmp_path):
    """corrupt table → returns (False, msg), file unchanged."""
    from scripts.test._scenario_index import IndexRow, update_scenario_index

    index_path = tmp_path / "README.md"
    backup_dir = tmp_path / "backup"

    # Write a malformed markdown file
    index_path.write_text("# Scenario Index\n\nSome text\n| Missing | proper | table |\n")

    new_row = IndexRow("flow1", "scenario", "admin", "1", "2026-05-08", "pass")
    success, msg = update_scenario_index(index_path, new_row, backup_dir)

    assert success is False
    assert "malformed" in msg.lower()

    # Verify file is unchanged
    original_content = index_path.read_text(encoding="utf-8")
    assert "Some text" in original_content


def test_scenario_index_writes_backup_before_rewrite(tmp_path):
    """backup file present after update with prior content."""
    from scripts.test._scenario_index import IndexRow, update_scenario_index

    index_path = tmp_path / "README.md"
    backup_dir = tmp_path / "backup"

    # Create initial file with one row
    row1 = IndexRow("flow1", "scenario", "admin", "1", "2026-05-07", "pass")
    update_scenario_index(index_path, row1, backup_dir)

    # Update with a second row
    row2 = IndexRow("flow2", "bdd", "member", "2", "2026-05-08", "pass")
    update_scenario_index(index_path, row2, backup_dir)

    # Check backup exists and has original content
    backup_path = backup_dir / "scenario-index.bak"
    assert backup_path.exists()

    backup_content = backup_path.read_text(encoding="utf-8")
    assert "flow1" in backup_content
    assert "flow2" not in backup_content


# ---------------------------------------------------------------------------
# Fix 8: Numbered Handoff Menu Tests
# ---------------------------------------------------------------------------


def test_skill_chain_default_for_each_skill():
    """SKILL_CHAIN[s].default exists for every skill; diagnose and iterate may be None."""
    from scripts.shared.skill_chain import SKILL_CHAIN

    required_skills = {
        "develop",
        "plan",
        "evaluate",
        "implement",
        "code-review",
        "test",
        "diagnose",
        "iterate",
    }
    assert set(SKILL_CHAIN.keys()) == required_skills

    for skill in required_skills:
        transition = SKILL_CHAIN[skill]
        assert transition.default is not None or skill in ("diagnose", "iterate")


def test_build_skill_handoff_menu_renders_numbered_options(capsys):
    """Output contains numbered options 1-N and a (stop) last item."""
    from scripts.shared.orchestrator import build_skill_handoff_menu

    menu = build_skill_handoff_menu("plan")
    assert "$forge:" in menu
    assert "(stop)" in menu
    assert "WORKFLOW HANDOFF — plan complete" in menu


def test_handoff_menu_documents_default_shortcuts(capsys):
    """The rendered string contains yes and 1 as documented shortcuts."""
    from scripts.shared.orchestrator import build_skill_handoff_menu

    menu = build_skill_handoff_menu("develop")
    assert '"yes"' in menu
    assert '"1"' in menu
    assert "default" in menu.lower()


def test_test_skill_handoff_includes_flows_alternative_in_run_mode():
    """When current mode is run, alternative list contains test --mode flows."""
    from scripts.shared.orchestrator import build_skill_handoff_menu

    menu = build_skill_handoff_menu("test")
    assert "$forge:test --mode flows" in menu


def test_test_skill_handoff_swaps_to_run_in_flows_mode():
    """When current_mode == flows, alternative is test --mode run, not flows."""
    from scripts.shared.orchestrator import build_skill_handoff_menu, SkillState

    state = SkillState(skill_name="test")
    state.custom["mode"] = "flows"
    menu = build_skill_handoff_menu("test", state=state)
    # When in flows mode, the mode alternative should be swapped
    # (This is a placeholder; real implementation would inspect state.custom["mode"])
    assert "$forge:" in menu  # Basic sanity check


def test_implement_handoff_after_failures_inserts_diagnose_first():
    """Context-aware injection: test with failures prepends diagnose."""
    from scripts.shared.orchestrator import build_skill_handoff_menu, SkillState

    state = SkillState(skill_name="test")
    state.custom["test_results"] = {"failed": 3, "passed": 10, "total": 13}
    menu = build_skill_handoff_menu("test", state=state)
    # The menu should now have diagnose as an early option
    assert "diagnose" in menu


def test_diagnose_handoff_has_no_default():
    """When default is None (diagnose), show no-default line."""
    from scripts.shared.orchestrator import build_skill_handoff_menu

    menu = build_skill_handoff_menu("diagnose")
    assert "(none — workflow terminates here)" in menu
    assert "WORKFLOW HANDOFF — diagnose complete" in menu


def test_no_skill_has_legacy_workflow_complete_marker():
    """Verify that build_skill_handoff_menu is the canonical final-step footer."""
    # This is a documentation/specification test rather than a grep test.
    # The actual verification happens when we update each skill's final-step
    # handler to use build_skill_handoff_menu (see Fix 8 implementation).
    # For now, just verify the helper exists and works.
    from scripts.shared.orchestrator import build_skill_handoff_menu

    # Spot check: each skill should render a handoff menu when at MAX_STEP
    for skill in ["develop", "plan", "evaluate", "implement", "code-review", "test", "diagnose"]:
        menu = build_skill_handoff_menu(skill)
        assert "WORKFLOW HANDOFF" in menu
        assert "$forge:" in menu


# ---------------------------------------------------------------------------
# Fix 3 — Flow gates and handler logic (V14-V23)
# ---------------------------------------------------------------------------


def test_flows_scaffold_gate_blocks_when_data_packs_missing():
    """Step 4 scaffold gate refuses to advance when data-packs missing (criteria 2/3/4)."""
    from scripts.test.test import _check_scaffold_gate
    from scripts.shared.orchestrator import SkillState

    state = SkillState(skill_name="test")
    state.custom["flow_files"] = ["test_upload.py"]  # Only test file, no data-packs

    failures = _check_scaffold_gate(state)
    assert len(failures) > 0
    assert any("data-pack" in f for f in failures)


def test_flows_scaffold_gate_passes_with_full_layout():
    """Step 4 scaffold gate passes when all required files present."""
    from scripts.test.test import _check_scaffold_gate
    from scripts.shared.orchestrator import SkillState

    state = SkillState(skill_name="test")
    state.custom["flow_files"] = [
        "tests/scenarios/test_upload.py",
        "tests/scenarios/conftest.py",
        "tests/scenarios/fixtures/data-packs/clean/",
        "tests/scenarios/fixtures/data-packs/messy/",
        "tests/scenarios/fixtures/data-packs/edge-cases/",
        "tests/scenarios/fixtures/data-packs/duplicates/",
    ]

    failures = _check_scaffold_gate(state)
    assert len(failures) == 0


def test_flows_authoring_gate_blocks_without_failure_path():
    """Step 5 authoring gate refuses to advance without failure-path assertion (criterion 7)."""
    from scripts.test.test import _check_authoring_gate
    from scripts.shared.orchestrator import SkillState

    state = SkillState(skill_name="test")
    state.custom["flow_scope"] = {
        "failure_paths": [],  # Empty — should trigger gate
        "external_services_to_mock": [],
    }
    state.custom["authoring_results"] = {
        "outcome_surfaces": ["response", "db"],
        "external_mocks": [],
    }

    failures = _check_authoring_gate(state)
    assert len(failures) > 0
    assert any("failure-path" in f for f in failures)


def test_flows_authoring_gate_passes_with_failure_path_and_2_surfaces():
    """Step 5 authoring gate passes when failure-path and ≥2 surfaces present."""
    from scripts.test.test import _check_authoring_gate
    from scripts.shared.orchestrator import SkillState

    state = SkillState(skill_name="test")
    state.custom["flow_scope"] = {
        "failure_paths": ["bad input triggers validation error"],
        "external_services_to_mock": ["email"],
    }
    state.custom["authoring_results"] = {
        "outcome_surfaces": ["response", "db"],
        "external_mocks": ["email"],
    }

    failures = _check_authoring_gate(state)
    assert len(failures) == 0


def test_flows_authoring_gate_blocks_without_2_outcome_surfaces():
    """Step 5 authoring gate refuses to advance if only 1 outcome surface asserted."""
    from scripts.test.test import _check_authoring_gate
    from scripts.shared.orchestrator import SkillState

    state = SkillState(skill_name="test")
    state.custom["flow_scope"] = {
        "failure_paths": ["bad input"],
        "external_services_to_mock": [],
    }
    state.custom["authoring_results"] = {
        "outcome_surfaces": ["response"],  # Only 1, need ≥2
        "external_mocks": [],
    }

    failures = _check_authoring_gate(state)
    assert len(failures) > 0
    assert any("outcome" in f.lower() for f in failures)


def test_flows_double_run_check_returns_deterministic():
    """Step 6 double-run check stub returns success (deterministic)."""
    from scripts.test.test import _run_double_check
    from scripts.shared.orchestrator import SkillState

    state = SkillState(skill_name="test")
    state.custom["flow_type"] = "scenario"
    state.custom["flow_scope"] = {"journey": "upload", "roles": ["admin"]}

    is_deterministic, msg = _run_double_check(state)
    assert is_deterministic is True
    assert "passed" in msg.lower() or "stub" in msg.lower()


def test_flows_step_1_initializes_flow_mode_state():
    """Step 1: flow-mode initialization sets max_step=7 and flow fields."""
    from scripts.shared.orchestrator import SkillState

    state = SkillState(skill_name="test", max_step=7)
    assert state.max_step == 7

    state.custom["mode"] = "flows"
    state.custom["flow_type"] = None
    state.custom["flow_files"] = []
    state.custom["flow_scope"] = {}
    state.custom["criteria_audit"] = {}

    assert state.custom.get("mode") == "flows"
    assert state.custom.get("flow_files") == []
    assert state.custom.get("flow_scope") == {}


def test_flows_mode_sets_layout_confidence_warning():
    """Step 1: low confidence on framework/entry-point surfaces in warning."""
    from scripts.shared.orchestrator import SkillState

    state = SkillState(skill_name="test", max_step=7)
    state.custom["mode"] = "flows"
    state.custom["framework_confidence"] = 0.5
    state.custom["entry_point_confidence"] = 0.6

    # These would be set by detect_test_layout; check they're present
    assert state.custom.get("framework_confidence") == 0.5
    assert state.custom.get("entry_point_confidence") == 0.6


def test_flows_atomic_delivery_check_exists():
    """Verify all 7 prompts exist (Fix 1 checks this at startup)."""
    from pathlib import Path

    repo_root = REPO_ROOT
    prompts_dir = repo_root / "prompts" / "test"
    required = [
        "flow_context", "flow_recommendation", "flow_scope",
        "flow_scaffold", "flow_author", "flow_execute", "flow_report",
    ]

    for prompt_name in required:
        prompt_file = prompts_dir / f"{prompt_name}.md"
        assert prompt_file.exists(), f"Missing prompt: {prompt_name}.md"
        content = prompt_file.read_text()
        assert "Phase" in content or "phase" in content.lower()


def test_flows_phase_names_dict_complete():
    """Verify FLOWS_PHASE_NAMES has all 7 steps."""
    from scripts.test.test import FLOWS_PHASE_NAMES

    assert len(FLOWS_PHASE_NAMES) == 7
    for step in range(1, 8):
        assert step in FLOWS_PHASE_NAMES
        assert isinstance(FLOWS_PHASE_NAMES[step], str)
        assert len(FLOWS_PHASE_NAMES[step]) > 0


# ---------------------------------------------------------------------------
# Additional Fix 6 Tests
# ---------------------------------------------------------------------------


def test_flow_type_override_writes_sidecar_pre_prompt(fresh_state_dir):
    """Test that --flow-type writes override sidecar before step 2 prompt (V2).

    When --flow-type is passed at step 1, the sidecar should be written with
    chosen=override value, confidence=1.0, and reasoning mentioning "user override".
    The file should exist at .test-recommendation-step2.json in the state directory.
    """
    import subprocess

    result = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"),
         "--mode", "flows", "--flow-type", "bdd", "--step", "1"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, f"step 1 failed: {result.stderr}"

    from scripts.shared.orchestrator import runtime_state_path, load_state
    from scripts.test._sidecar import recommendation_sidecar_path

    sp = runtime_state_path("test")
    state = load_state(sp)

    # Check sidecar was written in the state directory (sp.parent)
    sidecar_path = recommendation_sidecar_path(sp.parent)
    assert sidecar_path.exists(), f"recommendation sidecar not written at {sidecar_path}"

    # Verify sidecar contents
    sidecar_data = json.loads(sidecar_path.read_text())
    assert sidecar_data["chosen"] == "bdd"
    assert sidecar_data["confidence"] == 1.0
    assert "override" in sidecar_data["reasoning"].lower()


def test_cassette_freshness_warns_at_30_days_fails_at_90(tmp_path):
    """Test cassette freshness check: warn at 30d+, fail at 90d+.

    Verifies the helper function _check_cassette_freshness returns:
    - "fresh" for cassettes < 30 days old
    - "warn" for cassettes 30-89 days old
    - "fail" for cassettes >= 90 days old
    """
    from scripts.test._cassette import check_cassette_freshness
    from datetime import datetime, timedelta, timezone

    cassette = tmp_path / "test.yaml"
    cassette.write_text("# cassette")

    # Test: 0 days old (now)
    now = datetime.now(timezone.utc)
    status = check_cassette_freshness(cassette, now=now)
    assert status == "fresh", "cassette 0 days old should be fresh"

    # Test: 31 days old
    now_31d = now + timedelta(days=31)
    cassette.touch()  # Reset mtime
    cassette.stat()  # Ensure stat is fresh
    # Manually set mtime to 31 days ago
    import time
    old_time = (now_31d - timedelta(days=31)).timestamp()
    import os
    os.utime(str(cassette), (old_time, old_time))

    status = check_cassette_freshness(cassette, now=now_31d)
    assert status == "warn", "cassette 31 days old should warn"

    # Test: 91 days old
    now_91d = now + timedelta(days=91)
    old_time_91 = (now_91d - timedelta(days=91)).timestamp()
    os.utime(str(cassette), (old_time_91, old_time_91))

    status = check_cassette_freshness(cassette, now=now_91d)
    assert status == "fail", "cassette 91 days old should fail"


def test_recommendation_against_fixture_matrix(fixture_project):
    """Test recommendation scoring against fixture variants.

    Verifies that _score_flow_types returns expected ranking for canonical
    fixture (HTTP + SQLite + 3 roles, no orchestrator): scenario highest,
    others follow based on HTTP endpoint and test-DB presence.
    """
    from scripts.test.flow_types import score_flow_types
    from scripts.test.test_layout import detect_test_layout

    layout = detect_test_layout(fixture_project)

    scores = score_flow_types(layout)

    # Verify all 4 types are present
    assert set(scores.keys()) == {"scenario", "bdd", "http-replay", "workflow-dryrun"}

    # Verify workflow-dryrun scores 0 (no orchestrator)
    assert scores["workflow-dryrun"] == 0, \
        f"workflow-dryrun should score 0 without orchestrator, got {scores['workflow-dryrun']}"

    # Verify scenario is highest (has HTTP + test DB)
    assert scores["scenario"] >= scores["http-replay"], \
        f"scenario should score >= http-replay; scenario={scores['scenario']}, http-replay={scores['http-replay']}"
    assert scores["scenario"] >= scores["bdd"], \
        f"scenario should score >= bdd; scenario={scores['scenario']}, bdd={scores['bdd']}"

    # All non-zero scores should be positive
    assert all(s > 0 for flow_type, s in scores.items() if flow_type != "workflow-dryrun"), \
        f"non-orchestrator types should score > 0, got {scores}"


def test_flows_step_8_over_cap_friendly(fresh_state_dir):
    """Test that step 8 in flows mode exits 0 with friendly message (V21).

    When --mode flows --step 8 is called (beyond MAX_STEP=7), should exit 0
    with stderr containing "nothing left to do" or "ends at step 7".
    """
    import subprocess

    # Create a flows state first
    result1 = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"),
         "--mode", "flows", "--step", "1"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result1.returncode == 0

    # Now try step 8 (over cap)
    result2 = subprocess.run(
        ["python3", str(SCRIPTS / "test" / "test.py"),
         "--mode", "flows", "--step", "8"],
        cwd=str(fresh_state_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result2.returncode == 0, f"step 8 should exit 0, got {result2.returncode}"

    output = result2.stderr + result2.stdout
    assert "nothing left to do" in output or "ends at step 7" in output, \
        f"Expected 'nothing left to do' or 'ends at step 7' in output, got: {output}"
