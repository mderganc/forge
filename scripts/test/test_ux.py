#!/usr/bin/env python3
"""UX-mode orchestration for the test skill.

Real-user browser QA: understand the app, plan goal-based journeys, exercise
them in a live browser, record issues, and report coverage. Invoked when
``--mode ux`` or when resumed state has ``mode == "ux"``.
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

UX_MAX_STEP = 6

UX_PHASE_NAMES = {
    1: "App Understanding",
    2: "Goal-Based Test Plan",
    3: "Browser Journey Execution",
    4: "Edge Cases & Persistence",
    5: "Issue Documentation",
    6: "Report + Handoff",
}

UX_PHASE_TODOS: dict[int, list[dict[str, str]]] = {
    1: [
        {"content": "Map purpose, features, roles, and critical workflows",
         "activeForm": "Mapping the application"},
        {"content": "Confirm base URL and entry surfaces",
         "activeForm": "Confirming entry surfaces"},
    ],
    2: [
        {"content": "Write goal-based scenarios covering happy and failure paths",
         "activeForm": "Writing the UX test plan"},
    ],
    3: [
        {"content": "Drive real-browser journeys for core user goals",
         "activeForm": "Executing browser journeys"},
    ],
    4: [
        {"content": "Exercise empty, invalid, cancel, retry, and recovery paths",
         "activeForm": "Running edge and recovery passes"},
        {"content": "Verify data after navigation and refresh",
         "activeForm": "Checking persistence"},
    ],
    5: [
        {"content": "Record every issue with repro, severity, and evidence",
         "activeForm": "Documenting issues"},
    ],
    6: [
        {"content": "Summarize coverage, risks, and prioritized recommendations",
         "activeForm": "Writing UX report"},
    ],
}


def initialize_ux_custom(state: SkillState, args) -> None:
    """Populate UX-mode fields on ``state.custom`` (step 1)."""
    base_url = getattr(args, "base_url", None) or ""
    state.custom["base_url"] = base_url
    state.custom["app_map"] = {}
    state.custom["ux_plan"] = {}
    state.custom["ux_results"] = {
        "passed": 0,
        "failed": 0,
        "blocked": 0,
        "total": 0,
        "scenarios": [],
    }
    state.custom["ux_issues"] = []
    state.custom["ux_coverage"] = {
        "covered": [],
        "untested": [],
        "risks": [],
        "recommendations": [],
    }

    layout = detect_test_layout(REPO_ROOT)
    roles_override = getattr(args, "roles", None)
    if roles_override:
        state.custom["roles"] = [r.strip() for r in roles_override.split(",") if r.strip()]
    else:
        state.custom["roles"] = layout.roles or ["anonymous"]
    state.custom["entry_point"] = getattr(args, "entry_point", None) or layout.entry_point or "ui"
    state.custom["framework"] = getattr(args, "framework", None) or layout.framework


def _build_variables(state: SkillState, state_path: Path | None = None, *, prompts_style: str = "brief"):
    from scripts.test.test import _build_variables

    return _build_variables(state, state_path, prompts_style=prompts_style)


def _next_command(step: int, state_path: str = "", mode: str | None = None) -> str:
    extra = {}
    if state_path:
        extra["state"] = state_path
    if mode and mode != "run":
        extra["mode"] = mode
    return build_next_command(
        SCRIPT_DIR / "test.py",
        step,
        UX_MAX_STEP,
        phase_variant="ux",
        **extra,
    )


def _check_plan_gate(state: SkillState) -> list[str]:
    """Require a usable goal-based plan before browser execution."""
    plan = state.custom.get("ux_plan") or {}
    missing: list[str] = []
    scenarios = plan.get("scenarios") or []
    if not scenarios:
        missing.append("ux_plan.scenarios is empty — write goal-based scenarios before executing")
    goals = plan.get("user_goals") or []
    if not goals and scenarios:
        # Accept scenarios that each carry a goal
        if not any(isinstance(s, dict) and s.get("goal") for s in scenarios):
            missing.append("ux_plan needs user_goals or per-scenario goal fields")
    return missing


def _check_issues_gate(state: SkillState) -> list[str]:
    """Issues may be empty (clean run); require structured shape when present."""
    issues = state.custom.get("ux_issues") or []
    missing: list[str] = []
    required = ("title", "severity", "steps", "expected", "actual")
    for i, issue in enumerate(issues):
        if not isinstance(issue, dict):
            missing.append(f"ux_issues[{i}] must be an object")
            continue
        for key in required:
            if not issue.get(key):
                missing.append(f"ux_issues[{i}] missing '{key}'")
    results = state.custom.get("ux_results") or {}
    if results.get("failed", 0) > 0 and not issues:
        missing.append(
            "ux_results reports failures but ux_issues is empty — document each failure"
        )
    return missing


def handle_ux_step(step: int, state: SkillState, sp: Path) -> None:
    """Dispatcher for UX-mode steps 1–6."""
    phase_map = {
        1: ("ux_context", UX_PHASE_NAMES[1]),
        2: ("ux_plan", UX_PHASE_NAMES[2]),
        3: ("ux_execute", UX_PHASE_NAMES[3]),
        4: ("ux_adversarial", UX_PHASE_NAMES[4]),
        5: ("ux_issues", UX_PHASE_NAMES[5]),
        6: ("ux_report", UX_PHASE_NAMES[6]),
    }

    if step not in phase_map:
        print(f"ERROR: Invalid UX step {step}", file=sys.stderr)
        sys.exit(1)

    template_base, phase_name = phase_map[step]
    gate_failures: list[str] = []

    if step == 3:
        gate_failures = _check_plan_gate(state)
        if gate_failures:
            state.custom.setdefault("ux_plan_attempts", 0)
            state.custom["ux_plan_attempts"] += 1
            state.custom["ux_plan_gate_failures"] = gate_failures
            save_state(state, sp)

    elif step == 6:
        gate_failures = _check_issues_gate(state)
        if gate_failures:
            state.custom.setdefault("ux_issues_attempts", 0)
            state.custom["ux_issues_attempts"] += 1
            state.custom["ux_issues_gate_failures"] = gate_failures
            save_state(state, sp)

    template = load_template(f"test/{template_base}")
    variables = _build_variables(state, state_path=sp, prompts_style="full" if step == UX_MAX_STEP else "brief")
    variables["UX_PLAN_GATE_FAILURES"] = (
        "\n".join(f"- {f}" for f in gate_failures) if step == 3 and gate_failures else ""
    )
    variables["UX_ISSUES_GATE_FAILURES"] = (
        "\n".join(f"- {f}" for f in gate_failures) if step == 6 and gate_failures else ""
    )

    body = render_template(template, variables)

    if step == 3 and gate_failures:
        body = (
            "## PLAN GATE — incomplete\n\n"
            "Fix the plan (step 2) before browser execution:\n\n"
            + variables["UX_PLAN_GATE_FAILURES"]
            + "\n\n---\n\n"
            + body
        )
        state.current_step = step
        save_state(state, sp)
        append_skill_run_memory(
            SKILL_NAME,
            step,
            phase_name,
            "UX execute blocked by plan gate.",
            state=state,
            state_path=sp,
        )
        next_cmd = _next_command(2, state_path=str(sp), mode="ux")
        print(
            format_step_output(
                SKILL_NAME,
                step,
                UX_MAX_STEP,
                phase_name,
                body,
                next_cmd=next_cmd,
                phase_todos=UX_PHASE_TODOS.get(step, []),
                all_phase_names=UX_PHASE_NAMES,
                all_phase_todos=UX_PHASE_TODOS,
            )
        )
        return

    if step == 6 and gate_failures:
        body = (
            "## ISSUES GATE — incomplete\n\n"
            "Complete issue documentation before handoff:\n\n"
            + variables["UX_ISSUES_GATE_FAILURES"]
            + "\n\n---\n\n"
            + body
        )
        # Do not clear state / write handoff while gate fails
        state.current_step = step
        save_state(state, sp)
        append_skill_run_memory(
            SKILL_NAME,
            step,
            phase_name,
            "UX report blocked by issues gate.",
            state=state,
            state_path=sp,
        )
        next_cmd = _next_command(5, state_path=str(sp), mode="ux")
        print(
            format_step_output(
                SKILL_NAME,
                step,
                UX_MAX_STEP,
                phase_name,
                body,
                next_cmd=next_cmd,
                phase_todos=UX_PHASE_TODOS.get(step, []),
                all_phase_names=UX_PHASE_NAMES,
                all_phase_todos=UX_PHASE_TODOS,
            )
        )
        return

    state.current_step = step
    save_state(state, sp)

    handoff_menu = None
    handoff_path: Path | None = None
    run_summary = f"Completed UX-mode step {step} ({phase_name})."
    if step == UX_MAX_STEP:
        state.mark_step_complete(step)
        state.completed_at = now_iso()
        save_state(state, sp)

        results = state.custom.get("ux_results") or {}
        issues = state.custom.get("ux_issues") or []
        failed = int(results.get("failed", 0) or 0) + len(
            [i for i in issues if str(i.get("severity", "")).lower() in ("critical", "high")]
        )
        suggested_next = "diagnose" if failed > 0 or results.get("failed", 0) else "(end of flow)"

        handoff_path = write_handoff(
            skill_name=SKILL_NAME,
            state=state,
            context={
                "Mode": "ux",
                "Base URL": state.custom.get("base_url", ""),
                "Scenarios": f"{results.get('passed', 0)}/{results.get('total', 0)} passed",
                "Issues": str(len(issues)),
                "Suggested action": (
                    "diagnose high-severity UX issues" if failed > 0 else "UX pass clean"
                ),
            },
            suggested_next=suggested_next,
        )

        body += f"\n\nHandoff written to: {handoff_path}"
        clear_state_file(sp)
        handoff_menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
        run_summary = "Completed test (UX mode), wrote handoff, and closed session state."

    if step != UX_MAX_STEP:
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

    next_cmd = _next_command(step, state_path=str(sp), mode="ux") if step < UX_MAX_STEP else None
    print(
        format_step_output(
            SKILL_NAME,
            step,
            UX_MAX_STEP,
            phase_name,
            body,
            next_cmd=next_cmd,
            phase_todos=UX_PHASE_TODOS.get(step, []),
            handoff_menu=handoff_menu,
            all_phase_names=UX_PHASE_NAMES,
            all_phase_todos=UX_PHASE_TODOS,
        )
    )


def required_ux_prompts() -> list[str]:
    return [
        "ux_context",
        "ux_plan",
        "ux_execute",
        "ux_adversarial",
        "ux_issues",
        "ux_report",
    ]
