#!/usr/bin/env python3
"""Implement skill orchestrator.

Script-driven workflow that outputs formatted prompts for Codex to follow.
Each --step invocation loads state, selects the appropriate prompt template,
substitutes variables, and prints the prompt for Codex to execute.

Steps 3-5 form a wave loop: dispatch -> review -> complete, repeating
for each wave in the parallelization map.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Auto-detect repo root so this works from any working directory
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # scripts/implement/ -> scripts/ -> repo root

# Add repo root to sys.path so imports resolve without PYTHONPATH
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.shared.orchestrator import (
    SkillState,
    build_base_parser,
    build_next_command,
    build_skill_handoff_menu,
    clear_state_file,
    detect_active_sessions,
    find_state_file,
    format_active_session_warning,
    format_step_output,
    get_conflicting_sessions,
    load_state,
    now_iso,
    render_dashboard,
    runtime_state_path,
    save_state,
    validate_state_path,
    validate_step,
    validate_step_or_complete,
    write_handoff,
)
from scripts.evaluate.template_engine import load_template, render_template

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_NAME = "implement"
MAX_STEP = 8
PROMPTS_DIR = REPO_ROOT / "prompts"

PHASE_NAMES = {
    1: "Plan Detection",
    2: "Branch Setup",
    3: "Wave Dispatch",
    4: "Wave Review",
    5: "Wave Completion",
    6: "Integration Verification",
    7: "Documentation",
    8: "Handoff",
}

TEMPLATE_NAMES = {
    1: "implement/plan_detect",
    2: "implement/branch_setup",
    3: "implement/wave_dispatch",
    4: "implement/wave_review",
    5: "implement/wave_complete",
    6: "implement/integration_check",
    7: "implement/documentation",
    8: "implement/handoff",
}

PHASE_TODOS = {
    1: [
        {"content": "Detect plan path from handoff or CLI",
         "activeForm": "Detecting plan path"},
        {"content": "Initialize implement state",
         "activeForm": "Initializing state"},
    ],
    2: [
        {"content": "Create feature branch",
         "activeForm": "Creating feature branch"},
        {"content": "Identify waves from parallelization map",
         "activeForm": "Identifying waves"},
    ],
    3: [
        {"content": "Dispatch developer agents for current wave",
         "activeForm": "Dispatching wave agents"},
        {"content": "Wait for wave task completion",
         "activeForm": "Waiting for wave completion"},
    ],
    4: [
        {"content": "Run per-task review loops (QA + Critic + Security)",
         "activeForm": "Running per-task reviews"},
        {"content": "Resolve findings from reviews",
         "activeForm": "Resolving findings"},
    ],
    5: [
        {"content": "Merge wave branches to feature branch",
         "activeForm": "Merging wave"},
        {"content": "Check for next wave or proceed to documentation",
         "activeForm": "Checking wave status"},
    ],
    6: [
        {"content": "Verify cross-wave integration (dependencies, interfaces, architecture)",
         "activeForm": "Verifying cross-wave integration"},
        {"content": "Run regression sweep and performance check",
         "activeForm": "Running regression sweep"},
    ],
    7: [
        {"content": "Dispatch doc-writer for documentation",
         "activeForm": "Dispatching doc-writer"},
        {"content": "Create or update ADRs for significant decisions",
         "activeForm": "Updating ADRs"},
    ],
    8: [
        {"content": "Write handoff file for code-review",
         "activeForm": "Writing handoff"},
        {"content": "Render dashboard and complete",
         "activeForm": "Rendering dashboard"},
    ],
}

# Team roles and when they activate
TEAM_ROLES = [
    ("Backend Dev", "Plan assigns backend tasks"),
    ("Frontend Dev", "Plan assigns frontend tasks"),
    ("QA Reviewer", "Always (per-task review)"),
    ("Critic", "Always (per-task challenge)"),
    ("Security Reviewer", "Plan involves auth, data, APIs, or security-sensitive code"),
    ("Doc-writer", "Documentation phase + capture"),
]


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _get_state_path() -> Path:
    """Return the canonical state file path in cwd."""
    return runtime_state_path(SKILL_NAME)


def _init_state(quick: bool = False) -> SkillState:
    """Create a fresh implement state."""
    state = SkillState(skill_name=SKILL_NAME)
    state.max_step = MAX_STEP
    state.quick_mode = quick
    state.started_at = now_iso()
    state.custom = {
        "plan_path": "",
        "feature_branch": "",
        "current_wave": 0,
        "total_waves": 0,
        "waves_completed": 0,
    }
    return state


def _load_or_init_state(state_file: str | None, quick: bool = False) -> tuple[SkillState, Path]:
    """Load existing state or initialize a new one.

    Returns (state, state_path).
    """
    # Try explicit path first
    if state_file:
        sp = Path(state_file)
        if sp.exists():
            return load_state(sp), sp

    # Search for existing state
    found = find_state_file(SKILL_NAME)
    if found:
        return load_state(found), found

    # Initialize fresh
    state = _init_state(quick=quick)
    sp = _get_state_path()
    return state, sp


# ---------------------------------------------------------------------------
# Variable builders
# ---------------------------------------------------------------------------

def _build_team_composition() -> str:
    """Build the team composition table for template substitution."""
    lines = []
    lines.append("| Role | When Activated |")
    lines.append("|------|---------------|")
    for role, condition in TEAM_ROLES:
        lines.append(f"| {role} | {condition} |")
    return "\n".join(lines)


def _build_step1_variables(state: SkillState) -> dict[str, str]:
    """Build template variables for step 1 (plan detection)."""
    return {
        "TEAM_COMPOSITION": _build_team_composition(),
    }


def _build_step2_variables(state: SkillState) -> dict[str, str]:
    """Build template variables for step 2 (branch setup)."""
    return {
        "PLAN_PATH": state.custom.get("plan_path", "(not yet detected)"),
    }


def _build_wave_variables(state: SkillState) -> dict[str, str]:
    """Build template variables for wave-related steps (3, 4, 5)."""
    current_wave = state.custom.get("current_wave", 1)
    total_waves = state.custom.get("total_waves", 0)
    waves_completed = state.custom.get("waves_completed", 0)

    # Placeholder text for wave tasks and agent list -- the PM fills these
    # from the plan when executing the prompt
    wave_tasks = (
        f"Read `.codex/forge-codex/memory/project.md` for the Wave {current_wave} task list.\n"
        f"Each task includes: title, assigned agent, file paths, acceptance criteria."
    )
    agent_list = (
        f"Read `.codex/forge-codex/memory/project.md` for the agent assignments for Wave {current_wave}.\n"
        f"Dispatch each agent per `templates/parallel-dispatch.md`."
    )

    # Quick mode note
    if state.quick_mode:
        quick_note = (
            "**QUICK MODE active.** Minimal reviews: self-review + PM validation only. "
            "Skip cross-review and critic challenge."
        )
    else:
        quick_note = "Standard mode: full four-step review loop for each task."

    # Next wave or proceed to documentation
    if waves_completed < total_waves - 1:
        next_wave_or_proceed = (
            f"More waves remain. After completing this wave, proceed to Wave {current_wave + 1}."
        )
    else:
        next_wave_or_proceed = (
            "This is the final wave. After completion, proceed to the Documentation phase."
        )

    return {
        "CURRENT_WAVE": str(current_wave),
        "TOTAL_WAVES": str(total_waves) if total_waves > 0 else "(to be determined)",
        "WAVE_TASKS": wave_tasks,
        "AGENT_LIST": agent_list,
        "WAVES_COMPLETED": str(waves_completed),
        "QUICK_MODE_NOTE": quick_note,
        "NEXT_WAVE_OR_PROCEED": next_wave_or_proceed,
    }


def _build_doc_variables(state: SkillState) -> dict[str, str]:
    """Build template variables for step 6 (documentation)."""
    if state.quick_mode:
        quick_note = (
            "**QUICK MODE active.** Produce minimal documentation: "
            "changelog entry and inline comments only. Skip full user/dev docs."
        )
    else:
        quick_note = "Standard mode: produce full documentation suite."
    return {
        "QUICK_MODE_NOTE": quick_note,
    }


def _build_handoff_variables(state: SkillState) -> dict[str, str]:
    """Build template variables for step 7 (handoff)."""
    return {
        "FEATURE_BRANCH": state.custom.get("feature_branch", "forge/[feature-name]"),
        "WAVES_COMPLETED": str(state.custom.get("waves_completed", 0)),
        "TOTAL_WAVES": str(state.custom.get("total_waves", 0)),
    }


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------

def _wave_scoped_todos(step: int, wave: int | None) -> list[dict]:
    """Return PHASE_TODOS[step] with wave context injected for wave-loop steps."""
    todos = [dict(t) for t in PHASE_TODOS.get(step, [])]
    if wave is not None and step in (3, 4, 5):
        for todo in todos:
            todo["content"] = f"Wave {wave}: {todo['content']}"
            todo["activeForm"] = f"Wave {wave}: {todo['activeForm']}"
    return todos


def _next_command(current_step: int, quick: bool = False, target_step: int | None = None) -> str:
    """Build the next-step command, bounded by MAX_STEP.

    Returns "" when the requested next step would exceed MAX_STEP. Use
    `target_step` to override the default `current_step + 1` (wave loops in
    step 5 jump back to step 3).
    """
    nxt = target_step if target_step is not None else current_step + 1
    if nxt > MAX_STEP:
        return ""
    cmd = f"python3 {SCRIPT_DIR / 'implement.py'} --step {nxt}"
    if quick:
        cmd += " --quick"
    return cmd


def _emit(step: int, body: str, next_cmd: str | None,
          cross_skill_next: str | None = None,
          handoff_menu: str | None = None,
          phase_label: str | None = None,
          wave: int | None = None) -> None:
    """Shared output helper that injects PHASE_TODOS and continuation blocks."""
    label = phase_label or PHASE_NAMES.get(step, f"Step {step}")
    print(format_step_output(
        SKILL_NAME, step, MAX_STEP, label, body,
        next_cmd=next_cmd,
        phase_todos=_wave_scoped_todos(step, wave),
        cross_skill_next=cross_skill_next,
        handoff_menu=handoff_menu,
        all_phase_names=PHASE_NAMES,
        all_phase_todos=PHASE_TODOS,
    ))


def handle_step_1(args) -> None:
    """Step 1: Plan detection and state initialization."""
    # Cross-session detection (only for a fresh start)
    if not args.state:
        conflicting_sessions = get_conflicting_sessions(
            SKILL_NAME,
            sessions=detect_active_sessions(),
        )
        if conflicting_sessions:
            print(format_active_session_warning(conflicting_sessions, SKILL_NAME), file=sys.stderr)

    state, sp = _load_or_init_state(args.state, quick=args.quick)

    # Load template before mutating state — a missing template must not leave
    # state half-written.
    template = load_template(TEMPLATE_NAMES[1])
    variables = _build_step1_variables(state)
    body = render_template(template, variables)

    state.current_step = 1

    # Record plan path if provided via CLI
    if args.plan:
        state.custom["plan_path"] = args.plan

    save_state(state, sp)
    print(f"STATE FILE: {sp}\n", file=sys.stderr)

    # Add plan path hint if provided
    if args.plan:
        body += f"\n\n---\n\n**Plan argument provided:** `{args.plan}`\n"
        body += "Use this path directly (skip detection order steps 2-4).\n"

    # Mark step complete
    state.mark_step_complete(1)
    save_state(state, sp)

    _emit(1, body, _next_command(1, quick=args.quick))


def handle_step_2(state: SkillState, sp: Path) -> None:
    """Step 2: Branch setup and wave identification."""
    template = load_template(TEMPLATE_NAMES[2])
    variables = _build_step2_variables(state)
    body = render_template(template, variables)

    state.current_step = 2
    save_state(state, sp)

    state.mark_step_complete(2)
    save_state(state, sp)

    _emit(2, body, _next_command(2, quick=state.quick_mode))


def handle_step_3(state: SkillState, sp: Path) -> None:
    """Step 3: Wave dispatch -- send agents for current wave."""
    template = load_template(TEMPLATE_NAMES[3])

    current_wave = state.custom.get("current_wave", 0)
    if current_wave == 0:
        state.custom["current_wave"] = 1
        current_wave = 1

    # 0-wave plans (no parallel work): jump straight to integration verification
    # without ever entering the wave-review loop.
    total_waves = state.custom.get("total_waves", 0)
    if total_waves == 0:
        state.current_step = 3
        save_state(state, sp)
        state.mark_step_complete(3)
        save_state(state, sp)
        body = (
            "**No waves defined for this plan.** Skipping wave dispatch and review; "
            "proceeding directly to integration verification (step 6)."
        )
        _emit(3, body, _next_command(3, quick=state.quick_mode, target_step=6),
              wave=None)
        return

    variables = _build_wave_variables(state)
    body = render_template(template, variables)

    state.current_step = 3
    save_state(state, sp)

    state.mark_step_complete(3)
    save_state(state, sp)

    _emit(3, body, _next_command(3, quick=state.quick_mode), wave=current_wave)


def handle_step_4(state: SkillState, sp: Path) -> None:
    """Step 4: Wave review -- per-task review loop."""
    template = load_template(TEMPLATE_NAMES[4])
    current_wave = state.custom.get("current_wave", 1)
    variables = _build_wave_variables(state)
    body = render_template(template, variables)

    state.current_step = 4
    save_state(state, sp)

    state.mark_step_complete(4)
    save_state(state, sp)

    _emit(4, body, _next_command(4, quick=state.quick_mode), wave=current_wave)


def handle_step_5(state: SkillState, sp: Path) -> None:
    """Step 5: Wave completion -- merge and decide next wave or proceed."""
    template = load_template(TEMPLATE_NAMES[5])

    current_wave = state.custom.get("current_wave", 1)
    total_waves = state.custom.get("total_waves", 0)

    # Mark this wave as completed
    waves_completed = state.custom.get("waves_completed", 0) + 1
    state.custom["waves_completed"] = waves_completed

    variables = _build_wave_variables(state)
    body = render_template(template, variables)

    state.current_step = 5
    save_state(state, sp)

    # Determine next step: loop back to step 3 for next wave, or proceed to step 6
    if waves_completed < total_waves:
        state.custom["current_wave"] = current_wave + 1
        save_state(state, sp)
        next_step = 3
    else:
        next_step = 6

    next_cmd = _next_command(5, quick=state.quick_mode, target_step=next_step)

    phase_label = PHASE_NAMES[5]
    if waves_completed < total_waves:
        phase_label += f" (Wave {current_wave} done, {total_waves - waves_completed} remaining)"
    else:
        phase_label += " (All waves done)"

    state.mark_step_complete(5)
    save_state(state, sp)

    _emit(5, body, next_cmd, phase_label=phase_label, wave=current_wave)


def handle_step_6(state: SkillState, sp: Path) -> None:
    """Step 6: Integration verification -- cross-wave checks after all waves complete."""
    template = load_template(TEMPLATE_NAMES[6])
    variables = _build_wave_variables(state)
    body = render_template(template, variables)

    state.current_step = 6
    save_state(state, sp)

    state.mark_step_complete(6)
    save_state(state, sp)

    _emit(6, body, _next_command(6, quick=state.quick_mode))


def handle_step_7(state: SkillState, sp: Path) -> None:
    """Step 7: Documentation dispatch."""
    template = load_template(TEMPLATE_NAMES[7])
    variables = _build_doc_variables(state)
    body = render_template(template, variables)

    state.current_step = 7
    save_state(state, sp)

    state.mark_step_complete(7)
    save_state(state, sp)

    _emit(7, body, _next_command(7, quick=state.quick_mode))


def handle_step_8(state: SkillState, sp: Path) -> None:
    """Step 8: Handoff and dashboard."""
    template = load_template(TEMPLATE_NAMES[8])
    variables = _build_handoff_variables(state)
    body = render_template(template, variables)

    state.current_step = 8
    state.mark_step_complete(8)
    state.completed_at = now_iso()
    save_state(state, sp)

    # Write the handoff file
    context = {
        "Feature branch": state.custom.get("feature_branch", "forge/[feature-name]"),
        "Waves completed": str(state.custom.get("waves_completed", 0)),
        "Total waves": str(state.custom.get("total_waves", 0)),
        "Plan path": state.custom.get("plan_path", ""),
    }
    write_handoff(SKILL_NAME, state, context, "code-review")
    clear_state_file(sp)

    # Append dashboard to body
    dashboard = render_dashboard(state)
    body += f"\n\n---\n\n{dashboard}"

    handoff_menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
    _emit(8, body, None, handoff_menu=handoff_menu)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = build_base_parser(SKILL_NAME, MAX_STEP)
    parser.add_argument(
        "--plan", type=str, default=None,
        help="Path to plan file (step 1 only; auto-detected from handoff if omitted)"
    )
    args = parser.parse_args()

    if validate_step_or_complete(args.step, MAX_STEP, SKILL_NAME):
        return

    if args.step == 1:
        handle_step_1(args)
    else:
        # Load existing state for steps 2-8
        state_file = args.state
        sp = validate_state_path(state_file, SKILL_NAME) if state_file else None

        if sp is None:
            found = find_state_file(SKILL_NAME)
            if found:
                sp = found
            else:
                print("ERROR: No implementation in progress. Run step 1 first.")
                print("If the state file is elsewhere, pass --state <path>")
                sys.exit(1)

        try:
            state = load_state(sp)
        except json.JSONDecodeError:
            print(f"ERROR: State file is corrupted: {sp}")
            print("Delete it and re-run step 1.")
            sys.exit(1)
        except (KeyError, FileNotFoundError) as e:
            print(f"ERROR: State file problem — {e}")
            sys.exit(1)

        # Apply quick mode if passed on any step
        if args.quick:
            state.quick_mode = True

        handlers = {
            2: handle_step_2,
            3: handle_step_3,
            4: handle_step_4,
            5: handle_step_5,
            6: handle_step_6,
            7: handle_step_7,
            8: handle_step_8,
        }

        handler = handlers.get(args.step)
        if handler:
            handler(state, sp)
        else:
            print(f"ERROR: No handler for step {args.step}")
            sys.exit(1)


if __name__ == "__main__":
    main()
