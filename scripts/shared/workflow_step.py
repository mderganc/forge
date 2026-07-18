"""Common workflow step output formatting helpers."""

from __future__ import annotations

from scripts.shared.orchestrator import format_step_output


def run_workflow_step(
    skill_name: str,
    step: int,
    max_step: int,
    phase_name: str,
    body: str,
    next_cmd: str | None = None,
    *,
    phase_todos: list[dict] | None = None,
    cross_skill_next: str | None = None,
    all_phase_names: dict[int, str] | None = None,
    all_phase_todos: dict[int, list[dict]] | None = None,
    handoff_menu: str | None = None,
    require_confirmation: bool | None = None,
    await_same_step: bool = False,
    title: str | None = None,
) -> str:
    """Format a workflow step prompt for stdout (header, opt-in, todos, body, continuation)."""
    return format_step_output(
        skill_name,
        step,
        max_step,
        phase_name,
        body,
        next_cmd=next_cmd,
        phase_todos=phase_todos,
        cross_skill_next=cross_skill_next,
        all_phase_names=all_phase_names,
        all_phase_todos=all_phase_todos,
        handoff_menu=handoff_menu,
        require_confirmation=require_confirmation,
        await_same_step=await_same_step,
        title=title,
    )
