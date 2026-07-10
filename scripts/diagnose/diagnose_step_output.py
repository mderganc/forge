"""Finalize and print diagnose steps 2–7 (keeps orchestrate.handle_step_n thin)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.diagnose import diagnose_gates
from scripts.diagnose.diagnose_steps import (
    complexity_run_summary,
    routing_label_for_complexity,
    suggested_next_for_complexity,
)


def apply_step_state_updates(
    state: Any,
    sp: Path,
    step: int,
    phase_name: str,
    gate_result: diagnose_gates.DiagnoseGateResult | None,
    is_last: bool,
) -> str:
    from scripts.shared.orchestrator import now_iso, save_state

    run_summary = f"Completed step {step} ({phase_name})."
    if is_last:
        state.mark_step_complete(step)
        state.completed_at = now_iso()
        save_state(state, sp)
        return "Completed diagnose workflow, wrote handoff, and closed session state."

    gate_blocked = gate_result is not None and not gate_result.passed
    if not gate_blocked:
        state.mark_step_complete(step)
    save_state(state, sp)
    return complexity_run_summary(step, state, run_summary)


def write_last_step_handoff(
    state: Any,
    sp: Path,
    *,
    skill_name: str,
) -> tuple[Path | None, str | None]:
    from scripts.shared.orchestrator import (
        build_skill_handoff_menu,
        clear_state_file,
        write_handoff,
    )

    complexity = state.custom.get("fix_complexity", "unknown")
    handoff_path = write_handoff(
        skill_name=skill_name,
        state=state,
        context={
            "Root cause": state.custom.get("root_cause", "see report"),
            "Fix complexity": complexity,
            "Routing": routing_label_for_complexity(complexity),
            "Autonomy mode": state.custom.get("autonomy_mode", "guided"),
            "Open findings": str(len(state.open_findings())),
        },
        suggested_next=suggested_next_for_complexity(complexity),
    )
    handoff_menu = build_skill_handoff_menu(skill_name, state, sp)
    clear_state_file(sp)
    return handoff_path, handoff_menu


def build_next_step_command(
    step: int,
    state: Any,
    gate_result: diagnose_gates.DiagnoseGateResult | None,
    *,
    script_dir: Path,
    max_step: int,
    is_last: bool,
    state_path: Path,
) -> tuple[str | None, bool]:
    from scripts.shared.orchestrator import build_next_command

    if is_last:
        return None, False

    extra: dict[str, str] = {}
    if state.custom.get("autonomy_mode"):
        extra["mode"] = state.custom["autonomy_mode"]
    extra["state"] = str(state_path)

    next_step_override = (
        gate_result.next_step_override
        if gate_result and not gate_result.passed
        else None
    )
    if next_step_override is not None:
        next_cmd = build_next_command(
            script_dir / "orchestrate.py",
            step,
            max_step,
            next_step=next_step_override,
            **extra,
        )
        return next_cmd, bool(gate_result.require_confirmation)

    return build_next_command(script_dir / "orchestrate.py", step, max_step, **extra), False


def print_diagnose_step(
    *,
    skill_name: str,
    step: int,
    max_step: int,
    phase_name: str,
    body: str,
    state: Any,
    sp: Path,
    gate_result: diagnose_gates.DiagnoseGateResult | None,
    mode: str | None,
    is_last: bool,
    script_dir: Path,
    phase_names: dict[int, str],
    phase_todos: dict[int, list],
) -> None:
    from scripts.shared.orchestrator import (
        append_skill_run_memory,
        format_step_output,
        render_dashboard,
        save_state,
    )

    state.current_step = step
    if mode:
        state.custom["autonomy_mode"] = mode
    save_state(state, sp)

    handoff_path: Path | None = None
    handoff_menu: str | None = None
    run_summary = apply_step_state_updates(
        state, sp, step, phase_name, gate_result, is_last
    )

    if is_last:
        handoff_path, handoff_menu = write_last_step_handoff(state, sp, skill_name=skill_name)

    next_cmd, gate_confirm = build_next_step_command(
        step,
        state,
        gate_result,
        script_dir=script_dir,
        max_step=max_step,
        is_last=is_last,
        state_path=sp,
    )

    output = format_step_output(
        skill_name,
        step,
        max_step,
        phase_name,
        body,
        next_cmd=next_cmd,
        phase_todos=phase_todos.get(step, []),
        cross_skill_next=None,
        handoff_menu=handoff_menu,
        all_phase_names=phase_names,
        all_phase_todos=phase_todos,
        require_confirmation=gate_confirm if gate_confirm else None,
    )
    if is_last:
        output += "\n\n" + render_dashboard(state)

    append_skill_run_memory(
        skill_name,
        step,
        phase_name,
        run_summary,
        state=state,
        state_path=sp,
        handoff_path=handoff_path,
    )
    print(output)
