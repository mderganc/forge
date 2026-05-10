#!/usr/bin/env python3
"""Test skill orchestrator.

Script-driven workflow that outputs formatted prompts for Codex to follow.
Each --step invocation loads state, selects the appropriate prompt template,
substitutes variables, and prints the prompt for Codex to execute.

Steps:
  1. Context Detection — read handoff files, identify test targets, initialize state
  2. Test Discovery — QA Reviewer identifies test suites and coverage targets
  3. Test Execution — run test suites, collect results, follow verification-protocol.md
  4. Failure Analysis — for each failure, Investigator performs root-cause
  5. Coverage Gap Analysis — QA Reviewer + Critic identify untested paths
  6. Report — write test report, handoff, dashboard
"""

from __future__ import annotations

import sys
from pathlib import Path

# Auto-detect repo root so this works from any working directory
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # scripts/test/ -> scripts/ -> repo root

# Add repo root to sys.path so imports resolve without PYTHONPATH
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.shared.orchestrator import (
    SkillState,
    append_skill_run_memory,
    build_base_parser,
    build_next_command,
    build_skill_handoff_menu,
    check_same_skill_clobber,
    clear_state_file,
    detect_active_sessions,
    find_state_file,
    format_active_session_warning,
    get_conflicting_sessions,
    format_step_output,
    load_state,
    now_iso,
    consume_handoff,
    read_memory_file,
    render_dashboard,
    runtime_state_path,
    save_state,
    validate_state_path,
    validate_step_or_complete,
    write_handoff,
)
from scripts.evaluate.template_engine import (
    default_prompts_root,
    load_template,
    render_template,
)
from scripts.test.test_layout import detect_test_layout  # pyright: ignore[reportMissingImports]

SKILL_NAME = "test"
MAX_STEP = 6

# Flow phase names — used when mode == "flows"
FLOWS_PHASE_NAMES = {
    1: "Flow Context Detection",
    2: "Flow-Type Recommendation",
    3: "Scope Definition",
    4: "Scaffolding",
    5: "Mock Authoring",
    6: "Execution + Iteration",
    7: "Report + Handoff",
}

# Max steps for flows mode
FLOWS_MAX_STEP = 7

PHASE_NAMES = {
    1: "Context Detection",
    2: "Test Discovery",
    3: "Test Execution",
    4: "Failure Analysis",
    5: "Coverage Gap Analysis",
    6: "Report",
}

PHASE_TODOS = {
    1: [
        {"content": "Read handoff-code-review.md and handoff-implement.md",
         "activeForm": "Reading handoffs"},
        {"content": "Initialize test state",
         "activeForm": "Initializing state"},
    ],
    2: [
        {"content": "Dispatch QA Reviewer to discover test suites",
         "activeForm": "Discovering test suites"},
        {"content": "Identify coverage targets",
         "activeForm": "Identifying coverage targets"},
    ],
    3: [
        {"content": "Run test suites via verification ladder",
         "activeForm": "Running test suites"},
        {"content": "Collect results and coverage data",
         "activeForm": "Collecting results"},
    ],
    4: [
        {"content": "Dispatch Investigator for failure root-cause analysis",
         "activeForm": "Investigating failures"},
    ],
    5: [
        {"content": "Dispatch QA + Critic for coverage gap analysis",
         "activeForm": "Analyzing coverage gaps"},
        {"content": "Run mutation audit on critical paths",
         "activeForm": "Running mutation audit"},
    ],
    6: [
        {"content": "Write test report",
         "activeForm": "Writing test report"},
        {"content": "Write handoff and render dashboard",
         "activeForm": "Writing handoff"},
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_path() -> Path:
    """Return the default state file path."""
    return runtime_state_path(SKILL_NAME)




def _build_variables(state: SkillState) -> dict[str, str]:
    """Build template variable dict from state."""
    mode = state.custom.get("mode", "run")
    target = state.custom.get("target", "")
    handoff_cr = state.custom.get("handoff_code_review", "")
    handoff_impl = state.custom.get("handoff_implement", "")

    # Build handoff section
    handoff_parts = []
    if handoff_cr:
        handoff_parts.append(
            "## Handoff from Code Review\n\n"
            "<handoff>\n"
            f"{handoff_cr}\n"
            "</handoff>"
        )
    if handoff_impl:
        handoff_parts.append(
            "## Handoff from Implement\n\n"
            "<handoff>\n"
            f"{handoff_impl}\n"
            "</handoff>"
        )
    if not handoff_parts:
        handoff_parts.append(
            "## No Handoff Found\n\n"
            "No handoff files found. Discovering test targets from the project."
        )
    handoff_section = "\n\n".join(handoff_parts)

    # Build test results summary
    test_results = state.custom.get("test_results", {})
    passed = test_results.get("passed", 0)
    failed = test_results.get("failed", 0)
    skipped = test_results.get("skipped", 0)
    total = test_results.get("total", 0)
    coverage = test_results.get("coverage_pct", "N/A")

    if total > 0:
        results_section = (
            f"**Total:** {total} | **Passed:** {passed} | "
            f"**Failed:** {failed} | **Skipped:** {skipped}\n"
            f"**Coverage:** {coverage}%"
        )
    else:
        results_section = "(Tests not yet executed)"

    # Build findings summary
    findings_text = ""
    if state.findings:
        for f in state.findings:
            status = f" [{f['status']}]" if f.get("status") != "open" else ""
            findings_text += (
                f"- **{f['id']}** ({f['severity']}): {f['title']}{status}\n"
                f"  {f['detail']}\n\n"
            )
    else:
        findings_text = "(No findings yet)"

    # Team assignments based on quick mode
    if state.quick_mode:
        team_section = (
            "**Quick mode active** -- abbreviated team:\n\n"
            "| Agent | Focus |\n"
            "|-------|-------|\n"
            "| QA Reviewer | Test execution and coverage analysis |\n"
            "| Investigator | Failure root-cause (if needed) |\n"
        )
    else:
        team_section = (
            "| Agent | Focus |\n"
            "|-------|-------|\n"
            "| QA Reviewer (lead) | Test discovery, execution, coverage analysis |\n"
            "| Investigator | Failure root-cause analysis |\n"
            "| Critic | Coverage gap identification, untested assumptions |\n"
            "| Doc-writer | Test report documentation |\n"
        )

    # Discovered test suites
    test_suites = state.custom.get("test_suites", [])
    if test_suites:
        suites_text = "\n".join(f"- {s}" for s in test_suites)
    else:
        suites_text = "(Not yet discovered)"

    # New flow-mode variables
    flow_type = state.custom.get("flow_type", "")
    flow_type_override = flow_type or ""
    framework = state.custom.get("framework", "")
    framework_confidence = state.custom.get("framework_confidence", 0.0)
    entry_point = state.custom.get("entry_point", "")
    entry_point_confidence = state.custom.get("entry_point_confidence", 0.0)
    test_db = state.custom.get("test_db", "")
    roles = state.custom.get("roles", [])
    layout_confidence_warning = state.custom.get("layout_confidence_warning", "")

    return {
        "TARGET": target or "(auto-detected from handoff or project)",
        "HANDOFF_CONTENT": handoff_section,
        "TEST_RESULTS": results_section,
        "TEST_SUITES": suites_text,
        "FINDINGS": findings_text.strip(),
        "TEAM_ASSIGNMENTS": team_section,
        "QUICK_MODE": "yes" if state.quick_mode else "no",
        "SKILL_NAME": SKILL_NAME,
        "PASSED": str(passed),
        "FAILED": str(failed),
        "SKIPPED": str(skipped),
        "TOTAL": str(total),
        "COVERAGE": str(coverage),
        # Flow-mode variables
        "MODE": mode,
        "FLOW_TYPE": flow_type,
        "FLOW_TYPE_OVERRIDE": flow_type_override,
        "FRAMEWORK": framework,
        "FRAMEWORK_CONFIDENCE": f"{framework_confidence:.0%}",
        "ENTRY_POINT": entry_point,
        "ENTRY_POINT_CONFIDENCE": f"{entry_point_confidence:.0%}",
        "TEST_DB": test_db,
        "ROLES": ", ".join(roles) if roles else "",
        "LAYOUT_CONFIDENCE_WARNING": layout_confidence_warning,
    }


def _next_command(step: int, state_path: str = "") -> str:
    """Build the command for the next step."""
    extra = {}
    if state_path:
        extra["state"] = state_path
    return build_next_command(SCRIPT_DIR / "test.py", step, MAX_STEP, **extra)


# ---------------------------------------------------------------------------
# Flow-mode step handlers (stubs for Fix 3)
# ---------------------------------------------------------------------------

def _check_scaffold_gate(state: SkillState) -> list[str]:
    """Check if scaffold is complete per criteria 2/3/4.

    Returns list of missing-item strings; empty list = gate passes.
    """
    flow_files = state.custom.get("flow_files", [])
    missing = []

    if not flow_files:
        missing.append("flow_files list is empty — scaffold not created")
        return missing

    # Check for data-pack directories
    has_data_packs = any("data-packs" in f for f in flow_files)
    if not has_data_packs:
        missing.append("data-pack directories (clean/, messy/, edge-cases/, duplicates/) missing")

    # Check for role harness (conftest.py or steps file)
    has_harness = any("conftest.py" in f or "steps" in f for f in flow_files)
    if not has_harness:
        missing.append("role-parameterization harness file (conftest.py or steps/) missing")

    # Check for entry-point invocation in primary test file
    has_entry_point_call = any(
        "test_" in f and (".py" in f)
        for f in flow_files
    )
    if not has_entry_point_call:
        missing.append("primary test file missing or entry-point invocation not found")

    return missing


def _check_authoring_gate(state: SkillState) -> list[str]:
    """Check if authoring is complete per criteria 5/6/7.

    Returns list of missing-item strings; empty list = gate passes.
    """
    flow_scope = state.custom.get("flow_scope", {})
    authoring_results = state.custom.get("authoring_results", {})

    missing = []

    # Check for failure paths
    failure_paths = flow_scope.get("failure_paths", [])
    if not failure_paths or len(failure_paths) == 0:
        missing.append("no failure-path assertions (criterion 7) — at least 1 required")

    # Check for outcome surfaces (criterion 5)
    outcome_surfaces = authoring_results.get("outcome_surfaces", [])
    if len(outcome_surfaces) < 2:
        missing.append(f"outcome validation touches only {len(outcome_surfaces)} surface(s) (criterion 5) — at least 2 required")

    # Check for external mocks (criterion 6)
    external_mocks = authoring_results.get("external_mocks", [])
    allowed_externals = flow_scope.get("external_services_to_mock", [])
    for mock in external_mocks:
        if mock not in allowed_externals:
            missing.append(f"mock '{mock}' not in allowed externals (criterion 6)")

    return missing


def _run_double_check(state: SkillState) -> tuple[bool, str]:
    """Run flow twice and check for determinism (criterion 8).

    Returns (is_deterministic, message).

    Stub: full implementation runs pytest twice against the scaffolded scope
    and diffs outputs. Currently passes through unconditionally; the gate is
    enforced by the LLM via the prompt's instructions until this is wired up.
    """
    return True, "Double-run determinism check passed (stub)"


def _handle_flow_step(step: int, state: SkillState, sp: Path) -> None:
    """Dispatcher for flow-mode steps 1-7 with progressive gating.

    Each step loads the corresponding flow_<phase>.md template,
    renders it with _build_variables, applies gates where applicable,
    and saves state.
    """
    flow_phase_map = {
        1: ("flow_context", "Flow Context Detection"),
        2: ("flow_recommendation", "Flow-Type Recommendation"),
        3: ("flow_scope", "Scope Definition"),
        4: ("flow_scaffold", "Scaffolding"),
        5: ("flow_author", "Mock Authoring"),
        6: ("flow_execute", "Execution + Iteration"),
        7: ("flow_report", "Report + Handoff"),
    }

    if step not in flow_phase_map:
        print(f"ERROR: Invalid flow step {step}", file=sys.stderr)
        sys.exit(1)

    template_base, phase_name = flow_phase_map[step]

    # Apply gates before rendering template
    gate_failures = []

    if step == 4:
        # Scaffold gate: check criteria 2/3/4
        gate_failures = _check_scaffold_gate(state)
        if gate_failures:
            # Re-prompt with gate failures
            state.custom.setdefault("scaffold_attempts", 0)
            state.custom["scaffold_attempts"] += 1
            state.custom["scaffold_gate_failures"] = gate_failures
            save_state(state, sp)

    elif step == 5:
        # Authoring gate: check criteria 5/6/7
        gate_failures = _check_authoring_gate(state)
        if gate_failures:
            # Re-prompt with gate failures
            state.custom.setdefault("authoring_attempts", 0)
            state.custom["authoring_attempts"] += 1
            state.custom["authoring_gate_failures"] = gate_failures
            save_state(state, sp)

    elif step == 6:
        # Execution gate: check criterion 8 (determinism)
        is_deterministic, msg = _run_double_check(state)
        if not is_deterministic:
            gate_failures = [msg]
            state.custom.setdefault("execution_attempts", 0)
            state.custom["execution_attempts"] += 1
            state.custom["execution_gate_failures"] = gate_failures
            save_state(state, sp)

    # Render template with current variables
    template = load_template(f"test/{template_base}")
    variables = _build_variables(state)

    # Populate gate failure variables
    if gate_failures:
        variables["SCAFFOLD_GATE_FAILURES"] = "\n".join(f"- {f}" for f in gate_failures) if step == 4 else ""
        variables["AUTHORING_GATE_FAILURES"] = "\n".join(f"- {f}" for f in gate_failures) if step == 5 else ""
        variables["EXECUTION_GATE_FAILURES"] = "\n".join(f"- {f}" for f in gate_failures) if step == 6 else ""

    body = render_template(template, variables)

    state.current_step = step
    save_state(state, sp)

    # Step 7: mark completion and write handoff
    handoff_menu = None
    handoff_path: Path | None = None
    run_summary = f"Completed flow-mode step {step} ({phase_name})."
    if step == FLOWS_MAX_STEP:
        state.mark_step_complete(step)
        state.completed_at = now_iso()
        save_state(state, sp)

        # Write handoff
        handoff_path = write_handoff(
            skill_name=SKILL_NAME,
            state=state,
            context={
                "Mode": "flows",
                "Flow type": state.custom.get("flow_type", ""),
                "Scope": state.custom.get("flow_scope", {}),
            },
            suggested_next="(end of flow)",
        )

        body += f"\n\nHandoff written to: {handoff_path}"
        clear_state_file(sp)
        handoff_menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
        run_summary = "Completed test (flows mode), wrote handoff, and closed session state."

    if step != FLOWS_MAX_STEP:
        state.mark_step_complete(step)
        save_state(state, sp)

    append_skill_run_memory(
        SKILL_NAME,
        step,
        phase_name,
        run_summary,
        state=state,
        state_path=sp,
        handoff_path=handoff_path,
    )

    next_cmd = _next_command(step, state_path=str(sp)) if step < FLOWS_MAX_STEP else None
    print(format_step_output(
        SKILL_NAME, step, FLOWS_MAX_STEP, phase_name, body,
        next_cmd=next_cmd,
        phase_todos=PHASE_TODOS.get(step, []),
        handoff_menu=handoff_menu,
        all_phase_names=FLOWS_PHASE_NAMES,
        all_phase_todos=PHASE_TODOS,
    ))


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------

def handle_step_1(args) -> None:
    """Step 1: Context Detection -- read handoffs, identify targets, init state."""
    # Same-skill abort: refuse to silently overwrite an in-progress session.
    check_same_skill_clobber(SKILL_NAME)

    # Cross-skill detection: warn only.
    conflicting_sessions = get_conflicting_sessions(
        SKILL_NAME,
        sessions=detect_active_sessions(),
    )
    if conflicting_sessions:
        print(format_active_session_warning(conflicting_sessions, SKILL_NAME), file=sys.stderr)

    # Read handoffs
    handoff_cr = consume_handoff("code-review")
    handoff_impl = consume_handoff("implement")
    project_md = read_memory_file("project.md")

    # Determine target
    target = getattr(args, "target", None) or ""

    # Determine mode and set max_step
    mode = getattr(args, "mode", "run")
    max_step = 7 if mode == "flows" else MAX_STEP

    state = SkillState(skill_name=SKILL_NAME, max_step=max_step)
    state.current_step = 1
    state.quick_mode = args.quick
    state.started_at = now_iso()
    state.custom["mode"] = mode
    state.custom["target"] = target
    state.custom["handoff_code_review"] = handoff_cr
    state.custom["handoff_implement"] = handoff_impl
    state.custom["project_context"] = project_md
    state.custom["test_results"] = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0,
        "coverage_pct": "N/A",
    }
    state.custom["test_suites"] = []

    # Flow-mode state initialization
    if mode == "flows":
        state.custom["flow_type"] = getattr(args, "flow_type", None)
        state.custom["flow_files"] = []
        state.custom["flow_scope"] = {}
        state.custom["criteria_audit"] = {}

        # Detect test layout and persist
        layout = detect_test_layout(REPO_ROOT)
        state.custom["framework"] = getattr(args, "framework", None) or layout.framework
        state.custom["framework_confidence"] = layout.framework_confidence
        state.custom["entry_point"] = getattr(args, "entry_point", None) or layout.entry_point
        state.custom["entry_point_confidence"] = layout.entry_point_confidence
        test_db_override = "none" if getattr(args, "no_db", False) else layout.test_db
        state.custom["test_db"] = test_db_override
        state.custom["has_orchestrator_pattern"] = layout.has_orchestrator_pattern
        roles_override = getattr(args, "roles", None)
        if roles_override:
            state.custom["roles"] = [r.strip() for r in roles_override.split(",")]
        else:
            state.custom["roles"] = layout.roles or ["anonymous"]

        # Compute confidence warning
        warnings = []
        if layout.framework_confidence < 0.7:
            warnings.append(f"framework detection confidence: {layout.framework_confidence:.1%}")
        if layout.entry_point_confidence < 0.7:
            warnings.append(f"entry-point detection confidence: {layout.entry_point_confidence:.1%}")
        if warnings:
            state.custom["layout_confidence_warning"] = (
                "⚠ Low confidence on: " + ", ".join(warnings) +
                " — override with --framework / --entry-point / --no-db / --roles"
            )
        else:
            state.custom["layout_confidence_warning"] = ""

    sp = _state_path()
    save_state(state, sp)

    # Print state path so Codex knows where it is
    print(f"STATE FILE: {sp}\n", file=sys.stderr)

    # For flows mode, dispatch to _handle_flow_step
    if mode == "flows":
        # If --flow-type was passed, write override sidecar now (before step 2 prompt)
        if getattr(args, "flow_type", None):
            from scripts.test._sidecar import write_recommendation_override, log_override_to_stderr
            write_recommendation_override(sp.parent, getattr(args, "flow_type"))
            log_override_to_stderr(getattr(args, "flow_type"))
        _handle_flow_step(1, state, sp)
    else:
        # Run mode: original flow
        template = load_template("test/context")
        variables = _build_variables(state)
        body = render_template(template, variables)

        state.mark_step_complete(1)
        save_state(state, sp)
        append_skill_run_memory(
            SKILL_NAME,
            1,
            PHASE_NAMES[1],
            "Initialized test session (run mode) and loaded handoff context.",
            state=state,
            state_path=sp,
        )

        phase_name = PHASE_NAMES[1]
        next_cmd = _next_command(1, state_path=str(sp))
        print(format_step_output(
            SKILL_NAME, 1, MAX_STEP, phase_name, body,
            next_cmd=next_cmd,
            phase_todos=PHASE_TODOS.get(1, []),
            all_phase_names=PHASE_NAMES,
            all_phase_todos=PHASE_TODOS,
        ))


def handle_step_n(step: int, state_file: str | None = None) -> None:
    """Steps 2-7: Load state, render template, output prompt."""
    sp = validate_state_path(state_file, SKILL_NAME) if state_file else None
    if sp is None:
        sp = find_state_file(SKILL_NAME)
        if sp is None:
            sp = _state_path()

    if not sp.exists():
        print("ERROR: No test session in progress. Run step 1 first.")
        print(f"Expected state file at: {_state_path()}")
        sys.exit(1)

    try:
        state = load_state(sp)
    except Exception as e:
        print(f"ERROR: Failed to load state: {e}")
        print("Delete the state file and re-run step 1.")
        sys.exit(1)

    # Dispatch based on mode
    mode = state.custom.get("mode", "run")
    if mode == "flows":
        _handle_flow_step(step, state, sp)
        return

    # Run-mode path (unchanged)
    # Map steps to template names
    template_map = {
        2: "test/discovery",
        3: "test/execution",
        4: "test/failure_analysis",
        5: "test/coverage_gaps",
        6: "test/report",
    }

    template_name = template_map.get(step)
    if not template_name:
        print(f"ERROR: Invalid step {step}")
        sys.exit(1)

    # Load template before mutating state — a missing template must not leave
    # state half-written.
    template = load_template(template_name)
    variables = _build_variables(state)
    body = render_template(template, variables)

    state.current_step = step
    save_state(state, sp)

    # Step 6: mark completion and write handoff
    handoff_menu = None
    handoff_path: Path | None = None
    run_summary = f"Completed step {step} ({PHASE_NAMES.get(step, f'Step {step}')})."
    if step == MAX_STEP:
        state.mark_step_complete(step)
        state.completed_at = now_iso()
        save_state(state, sp)

        test_results = state.custom.get("test_results", {})
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        total = test_results.get("total", 0)
        coverage = test_results.get("coverage_pct", "N/A")

        # Suggest diagnose if there are failures, otherwise end of flow
        suggested_next = "diagnose" if failed > 0 else "(end of flow)"

        handoff_path = write_handoff(
            skill_name=SKILL_NAME,
            state=state,
            context={
                "Test results": f"{passed}/{total} passed, {failed} failed",
                "Coverage": f"{coverage}%",
                "Failures": str(failed),
                "Open findings": str(len(state.open_findings())),
                "Suggested action": "diagnose failures" if failed > 0 else "all tests passing",
            },
            suggested_next=suggested_next,
        )

        dashboard = render_dashboard(state)
        body += f"\n\n---\n\n{dashboard}"
        body += f"\n\nHandoff written to: {handoff_path}"
        clear_state_file(sp)
        handoff_menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
        run_summary = "Completed test workflow (run mode), wrote handoff, and closed session state."

    if step != MAX_STEP:
        state.mark_step_complete(step)
        save_state(state, sp)

    append_skill_run_memory(
        SKILL_NAME,
        step,
        PHASE_NAMES.get(step, f"Step {step}"),
        run_summary,
        state=state,
        state_path=sp,
        handoff_path=handoff_path,
    )

    phase_name = PHASE_NAMES.get(step, f"Step {step}")
    next_cmd = _next_command(step, state_path=str(sp)) if step < MAX_STEP else None
    print(format_step_output(
        SKILL_NAME, step, MAX_STEP, phase_name, body,
        next_cmd=next_cmd,
        phase_todos=PHASE_TODOS.get(step, []),
        handoff_menu=handoff_menu,
        all_phase_names=PHASE_NAMES,
        all_phase_todos=PHASE_TODOS,
    ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = build_base_parser(SKILL_NAME, MAX_STEP)
    parser.add_argument(
        "--target", type=str, default=None,
        help="Test command, path, or pattern to run"
    )
    # Flow-mode flags (Fix 1)
    parser.add_argument(
        "--mode", type=str, choices=["run", "flows"], default="run",
        help="Skill mode: run (default) or flows (author mock flows)"
    )
    parser.add_argument(
        "--flow-type", type=str,
        choices=["scenario", "bdd", "http-replay", "workflow-dryrun"],
        default=None,
        help="Override flow type recommendation"
    )
    parser.add_argument(
        "--re-record", action="store_true",
        help="Refresh HTTP-replay cassettes (flows mode only)"
    )
    parser.add_argument(
        "--framework", type=str, default=None,
        help="Manual override for test framework detection"
    )
    parser.add_argument(
        "--entry-point", type=str,
        choices=["ui", "http", "cli", "module", "none"],
        default=None,
        help="Manual override for test entry point"
    )
    parser.add_argument(
        "--no-db", action="store_true",
        help="Override test-DB detection as 'none'"
    )
    parser.add_argument(
        "--roles", type=str, default=None,
        help="Comma-separated role list override (e.g., 'admin,member,viewer')"
    )
    args = parser.parse_args()

    # Atomic-delivery feature-check: if flows mode, verify all 7 prompts exist
    if args.mode == "flows":
        required_prompts = [
            "flow_context", "flow_recommendation", "flow_scope",
            "flow_scaffold", "flow_author", "flow_execute", "flow_report",
        ]
        missing = []
        for p in required_prompts:
            try:
                load_template(f"test/{p}")
            except FileNotFoundError:
                missing.append(p)
        if missing:
            prompts_root = default_prompts_root()
            print(
                f"ERROR: flows mode unavailable — missing prompts in active template root ({prompts_root}): {missing}",
                file=sys.stderr
            )
            sys.exit(1)

    # Resume-conflict guard: if state exists and mode differs, abort
    if args.step > 1 and args.state:
        sp = validate_state_path(args.state, SKILL_NAME)
        if sp and sp.exists():
            try:
                saved_state = load_state(sp)
                saved_mode = saved_state.custom.get("mode", "run")
                # Only abort if --mode was explicitly passed (not default)
                if args.mode != "run" and saved_mode != args.mode:
                    print(
                        f"ERROR: Cannot resume — saved mode is '{saved_mode}' but --mode '{args.mode}' was passed.\n"
                        f"       Either re-run without --mode (resume preserves saved mode) or delete the state file.",
                        file=sys.stderr
                    )
                    sys.exit(1)
            except Exception:
                # If we can't load, let validate_step_or_complete handle it
                pass

    # Determine the max step based on mode (if step > 1, try to load state first to check)
    mode = getattr(args, "mode", "run")
    if args.step > 1 and args.state:
        sp = validate_state_path(args.state, SKILL_NAME)
        if sp and sp.exists():
            try:
                saved_state = load_state(sp)
                mode = saved_state.custom.get("mode", "run")
            except Exception:
                pass

    effective_max_step = 7 if mode == "flows" else MAX_STEP

    # Allow over-cap if not a step request
    if validate_step_or_complete(args.step, effective_max_step, SKILL_NAME):
        return

    if args.step == 1:
        handle_step_1(args)
    else:
        handle_step_n(args.step, state_file=args.state)


if __name__ == "__main__":
    main()
