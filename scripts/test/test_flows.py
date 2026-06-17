#!/usr/bin/env python3
"""Flows-mode orchestration for the test skill.

Extracted from test.py so run mode stays the primary entry; test.py delegates
here when ``--mode flows`` or when resumed state has ``mode == "flows"``.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

from scripts.evaluate.template_engine import load_template, render_template
from scripts.shared.orchestrator import (
    SkillState,
    append_skill_run_memory,
    build_next_command,
    build_skill_handoff_menu,
    clear_state_file,
    format_step_output,
    now_iso,
    save_state,
    write_handoff,
)
from scripts.test.test_layout import detect_test_layout  # pyright: ignore[reportMissingImports]

SKILL_NAME = "test"

FLOWS_PHASE_NAMES = {
    1: "Flow Context Detection",
    2: "Flow-Type Recommendation",
    3: "Scope Definition",
    4: "Scaffolding",
    5: "Mock Authoring",
    6: "Execution + Iteration",
    7: "Report + Handoff",
}

FLOWS_MAX_STEP = 7

FLOWS_PHASE_TODOS: dict[int, list[dict[str, str]]] = {}


def initialize_flow_custom(state: SkillState, args) -> None:
    """Populate flow-mode fields on ``state.custom`` (step 1)."""
    state.custom["flow_type"] = getattr(args, "flow_type", None)
    state.custom["flow_files"] = []
    state.custom["flow_scope"] = {}
    state.custom["criteria_audit"] = {}

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

    warnings = []
    if layout.framework_confidence < 0.7:
        warnings.append(f"framework detection confidence: {layout.framework_confidence:.1%}")
    if layout.entry_point_confidence < 0.7:
        warnings.append(f"entry-point detection confidence: {layout.entry_point_confidence:.1%}")
    if warnings:
        state.custom["layout_confidence_warning"] = (
            "⚠ Low confidence on: "
            + ", ".join(warnings)
            + " — override with --framework / --entry-point / --no-db / --roles"
        )
    else:
        state.custom["layout_confidence_warning"] = ""


def _build_variables(state: SkillState, state_path: Path | None = None, *, prompts_style: str = "brief"):
    from scripts.test.test import _build_variables

    return _build_variables(state, state_path, prompts_style=prompts_style)


def _next_command(step: int, state_path: str = "", mode: str | None = None) -> str:
    extra = {}
    if state_path:
        extra["state"] = state_path
    if mode and mode != "run":
        extra["mode"] = mode
    variant = mode if mode in ("run", "flows") else "run"
    max_s = FLOWS_MAX_STEP if variant == "flows" else 6
    return build_next_command(
        SCRIPT_DIR / "test.py",
        step,
        max_s,
        phase_variant=variant,
        **extra,
    )


def _check_scaffold_gate(state: SkillState) -> list[str]:
    """Check if scaffold is complete per criteria 2/3/4."""
    flow_files = state.custom.get("flow_files", [])
    missing = []

    if not flow_files:
        missing.append("flow_files list is empty — scaffold not created")
        return missing

    has_data_packs = any("data-packs" in f for f in flow_files)
    if not has_data_packs:
        missing.append("data-pack directories (clean/, messy/, edge-cases/, duplicates/) missing")

    has_harness = any("conftest.py" in f or "steps" in f for f in flow_files)
    if not has_harness:
        missing.append("role-parameterization harness file (conftest.py or steps/) missing")

    has_entry_point_call = any("test_" in f and ".py" in f for f in flow_files)
    if not has_entry_point_call:
        missing.append("primary test file missing or entry-point invocation not found")

    return missing


def _check_authoring_gate(state: SkillState) -> list[str]:
    """Check if authoring is complete per criteria 5/6/7."""
    flow_scope = state.custom.get("flow_scope", {})
    authoring_results = state.custom.get("authoring_results", {})

    missing = []

    failure_paths = flow_scope.get("failure_paths", [])
    if not failure_paths:
        missing.append("no failure-path assertions (criterion 7) — at least 1 required")

    outcome_surfaces = authoring_results.get("outcome_surfaces", [])
    if len(outcome_surfaces) < 2:
        missing.append(
            f"outcome validation touches only {len(outcome_surfaces)} surface(s) "
            "(criterion 5) — at least 2 required"
        )

    external_mocks = authoring_results.get("external_mocks", [])
    allowed_externals = flow_scope.get("external_services_to_mock", [])
    for mock in external_mocks:
        if mock not in allowed_externals:
            missing.append(f"mock '{mock}' not in allowed externals (criterion 6)")

    return missing


def handle_flow_step(step: int, state: SkillState, sp: Path) -> None:
    """Dispatcher for flow-mode steps 1-7 with progressive gating."""
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
    gate_failures: list[str] = []

    if step == 4:
        gate_failures = _check_scaffold_gate(state)
        if gate_failures:
            state.custom.setdefault("scaffold_attempts", 0)
            state.custom["scaffold_attempts"] += 1
            state.custom["scaffold_gate_failures"] = gate_failures
            save_state(state, sp)

    elif step == 5:
        gate_failures = _check_authoring_gate(state)
        if gate_failures:
            state.custom.setdefault("authoring_attempts", 0)
            state.custom["authoring_attempts"] += 1
            state.custom["authoring_gate_failures"] = gate_failures
            save_state(state, sp)

    template = load_template(f"test/{template_base}")
    variables = _build_variables(state)
    variables["SCAFFOLD_GATE_FAILURES"] = (
        "\n".join(f"- {f}" for f in gate_failures) if step == 4 and gate_failures else ""
    )
    variables["AUTHORING_GATE_FAILURES"] = (
        "\n".join(f"- {f}" for f in gate_failures) if step == 5 and gate_failures else ""
    )

    body = render_template(template, variables)

    state.current_step = step
    save_state(state, sp)

    handoff_menu = None
    handoff_path: Path | None = None
    run_summary = f"Completed flow-mode step {step} ({phase_name})."
    if step == FLOWS_MAX_STEP:
        state.mark_step_complete(step)
        state.completed_at = now_iso()
        save_state(state, sp)

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

    next_cmd = _next_command(step, state_path=str(sp), mode="flows") if step < FLOWS_MAX_STEP else None
    print(
        format_step_output(
            SKILL_NAME,
            step,
            FLOWS_MAX_STEP,
            phase_name,
            body,
            next_cmd=next_cmd,
            phase_todos=FLOWS_PHASE_TODOS.get(step, []),
            handoff_menu=handoff_menu,
            all_phase_names=FLOWS_PHASE_NAMES,
            all_phase_todos=FLOWS_PHASE_TODOS,
        )
    )


def prepare_flow_step_1(state_path: Path, flow_type: str | None) -> None:
    """Write recommendation override sidecar when ``--flow-type`` is passed."""
    if not flow_type:
        return
    from scripts.test._sidecar import log_override_to_stderr, write_recommendation_override

    write_recommendation_override(state_path.parent, flow_type)
    log_override_to_stderr(flow_type)


def required_flow_prompts() -> list[str]:
    return [
        "flow_context",
        "flow_recommendation",
        "flow_scope",
        "flow_scaffold",
        "flow_author",
        "flow_execute",
        "flow_report",
    ]
