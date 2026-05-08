#!/usr/bin/env python3
"""Plan skill orchestrator.

Script-driven workflow that outputs formatted prompts for Codex to follow.
Each --step invocation loads state, selects the appropriate prompt template,
substitutes variables, and prints the prompt for Codex to execute.

Steps:
  1. Context Detection — check for handoff, read memory, initialize state
  2. Architecture Dispatch — Architect designs unified architecture
  3. Plan Creation Dispatch — Planner creates detailed implementation plan
  4. Plan Review Loop — self -> cross -> critic -> PM review
  5. User Approval — present plan for approval
  6. Handoff — write handoff file and render dashboard
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Auto-detect repo root so this works from any working directory
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # scripts/plan/ -> scripts/ -> repo root

# Add repo root to sys.path so imports resolve without PYTHONPATH
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.shared.orchestrator import (
    SkillState,
    build_base_parser,
    build_next_command,
    build_skill_handoff_menu,
    check_same_skill_clobber,
    clear_state_file,
    detect_active_sessions,
    find_state_file,
    format_active_session_warning,
    format_step_output,
    get_conflicting_sessions,
    load_state,
    now_iso,
    read_handoff,
    read_memory_file,
    render_dashboard,
    runtime_memory_dir,
    runtime_state_path,
    save_state,
    validate_state_path,
    validate_step,
    validate_step_or_complete,
    write_handoff,
)
from scripts.evaluate.template_engine import load_template, render_template

PROMPTS_DIR = REPO_ROOT / "prompts"
SKILL_NAME = "plan"
MAX_STEP = 6

PHASE_NAMES = {
    1: "Context Detection",
    2: "Architecture Dispatch",
    3: "Plan Creation Dispatch",
    4: "Plan Review Loop",
    5: "User Approval",
    6: "Handoff",
}

PHASE_TODOS = {
    1: [
        {"content": "Read handoff-develop.md and memory files",
         "activeForm": "Reading handoff and memory"},
        {"content": "Initialize plan state",
         "activeForm": "Initializing state"},
    ],
    2: [
        {"content": "Dispatch Architect for architecture design",
         "activeForm": "Dispatching Architect"},
        {"content": "Wait for architecture artifacts",
         "activeForm": "Waiting for architecture"},
    ],
    3: [
        {"content": "Dispatch Planner with INVEST validation",
         "activeForm": "Dispatching Planner"},
        {"content": "Validate each task against INVEST criteria",
         "activeForm": "Validating INVEST"},
    ],
    4: [
        {"content": "Run 4-step review loop on plan",
         "activeForm": "Running plan review loop"},
        {"content": "Record and resolve findings",
         "activeForm": "Resolving findings"},
    ],
    5: [
        {"content": "Run pre-mortem analysis on plan",
         "activeForm": "Running pre-mortem"},
        {"content": "Present plan to user for approval",
         "activeForm": "Presenting plan for approval"},
    ],
    6: [
        {"content": "Write handoff file for implement skill",
         "activeForm": "Writing handoff"},
        {"content": "Render dashboard and complete",
         "activeForm": "Rendering dashboard"},
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_path() -> Path:
    """Return the default state file path."""
    return runtime_state_path(SKILL_NAME)




def _slugify(text: str, max_words: int = 5) -> str:
    """Convert text to a kebab-case slug suitable for filenames."""
    # Lowercase and keep only alphanumeric + spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    words = text.split()
    # Take first N meaningful words (skip very short ones except common ones)
    meaningful = [w for w in words if len(w) > 1][:max_words]
    return "-".join(meaningful) if meaningful else "plan"


def _extract_summary(handoff_content: str) -> str:
    """Extract a short summary from handoff content for the plan filename."""
    if not handoff_content:
        return "plan"
    # Try to find a heading first
    for line in handoff_content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return _slugify(re.sub(r"^#+\s*", "", line))
    # Fall back to first non-empty line
    for line in handoff_content.splitlines():
        line = line.strip()
        if line and not line.startswith(("-", "|", ">")):
            return _slugify(line)
    return "plan"


def generate_plan_filename(handoff_content: str = "") -> str:
    """Generate a timestamped plan filename like 20260414-1926-api-change-implementation.md."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    slug = _extract_summary(handoff_content)
    return f"{ts}-{slug}.md"


# Sections from templates/writing-plans.md (Plan Structure, lines 9-15).
# Order matters — agents fill these in order.
PLAN_SECTIONS = [
    ("ARCHITECTURE-OVERVIEW", "Architecture Overview"),
    ("BRANCH-STRATEGY", "Branch Strategy"),
    ("TASK-BREAKDOWN", "Task Breakdown"),
    ("PARALLELIZATION-MAP", "Parallelization Map"),
    ("INTERFACE-CONTRACTS", "Interface Contracts"),
    ("RISK-REGISTER", "Risk Register"),
    ("ROLLBACK-STRATEGY", "Rollback Strategy"),
]

# Distinctive marker so a plan section that legitimately quotes HTML comments
# (in code blocks etc.) doesn't trigger the unfilled-section gate.
SKELETON_MARKER_PREFIX = "<!-- FORGE_SKELETON: "
SKELETON_MARKER_SUFFIX = " -->"


def _is_stub_skeleton(content: str) -> bool:
    """True if the file contains only skeleton scaffolding (markers + headings)."""
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            continue
        if stripped.startswith("## "):
            continue
        if stripped.startswith(SKELETON_MARKER_PREFIX) and stripped.endswith(SKELETON_MARKER_SUFFIX):
            continue
        return False
    return True


def write_plan_skeleton(plan_path: Path, force: bool = False) -> None:
    """Materialize the canonical plan structure with section markers.

    Sections come from `templates/writing-plans.md` (the single source of
    truth). Each section is followed by a `<!-- FORGE_SKELETON: ID -->`
    marker on its own line — agents replace the marker with their content,
    and the step-6 completion gate refuses to mark the workflow complete
    while any markers remain.

    Overwrite policy:
      - File missing → write skeleton.
      - File exists but contains only scaffolding → overwrite.
      - File exists with real content → refuse unless `force=True`.
    """
    if plan_path.exists():
        existing = plan_path.read_text(encoding="utf-8")
        if existing.strip() and not _is_stub_skeleton(existing) and not force:
            sys.exit(
                f"ERROR: Plan file already exists with content: {plan_path}\n"
                "Delete it or pass --force to overwrite."
            )

    lines = ["# Implementation Plan", ""]
    for marker_id, heading in PLAN_SECTIONS:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(f"{SKELETON_MARKER_PREFIX}{marker_id}{SKELETON_MARKER_SUFFIX}")
        lines.append("")

    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("\n".join(lines), encoding="utf-8")


def find_unfilled_sections(plan_path: Path) -> list[str]:
    """Return human-readable section names that still contain skeleton markers."""
    if not plan_path.exists():
        return [name for _, name in PLAN_SECTIONS]
    content = plan_path.read_text(encoding="utf-8")
    unfilled = []
    for marker_id, heading in PLAN_SECTIONS:
        marker = f"{SKELETON_MARKER_PREFIX}{marker_id}{SKELETON_MARKER_SUFFIX}"
        if marker in content:
            unfilled.append(heading)
    return unfilled


def _build_variables(state: SkillState) -> dict[str, str]:
    """Build template variable dict from state."""
    handoff_content = state.custom.get("handoff_content", "")
    if handoff_content:
        handoff_section = (
            "## Handoff from Develop\n\n"
            "<handoff>\n"
            f"{handoff_content}\n"
            "</handoff>"
        )
    else:
        handoff_section = (
            "## No Handoff Found\n\n"
            "No handoff-develop.md was found. Ask the user what needs to be planned."
        )

    plan_context = state.custom.get("plan_context", "(not yet captured)")
    architecture_notes = state.custom.get("architecture_notes", "(not yet designed)")

    # Build review assignments based on quick mode
    if state.quick_mode:
        review_assignments = (
            "**Quick mode active** — abbreviated review:\n\n"
            "| Step | Agent | Focus |\n"
            "|------|-------|-------|\n"
            "| Self-review | Planner | File paths real? TDD steps complete? |\n"
            "| PM validation | PM | All solutions covered? Interfaces match? |\n"
        )
    else:
        review_assignments = ""  # Template has full table

    # Findings summary
    findings_text = ""
    if state.findings:
        for f in state.findings:
            status = f" [{f['status']}]" if f.get("status") != "open" else ""
            findings_text += f"- **{f['id']}** ({f['severity']}): {f['title']}{status}\n"
    else:
        findings_text = "(No findings yet)"

    plan_file = state.custom.get("plan_file")
    if not plan_file:
        sys.exit(
            "ERROR: state.custom['plan_file'] missing — "
            "re-run step 1 to initialize the plan file."
        )
    handoff_file = str(runtime_memory_dir() / "handoff-plan.md")

    return {
        "HANDOFF_CONTENT": handoff_section,
        "PLAN_CONTEXT": plan_context,
        "ARCHITECTURE_NOTES": architecture_notes,
        "REVIEW_ASSIGNMENTS": review_assignments,
        "FINDINGS": findings_text,
        "QUICK_MODE": "yes" if state.quick_mode else "no",
        "SKILL_NAME": SKILL_NAME,
        "PLAN_FILE": plan_file,
        "HANDOFF_FILE": handoff_file,
    }


def _next_command(step: int, state_path: str = "") -> str:
    """Build the command for the next step."""
    extra = {}
    if state_path:
        extra["state"] = state_path
    return build_next_command(SCRIPT_DIR / "plan.py", step, MAX_STEP, **extra)


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------

def handle_step_1(args: argparse.Namespace) -> None:
    """Step 1: Context Detection — check for handoff, read memory, init state."""
    # Same-skill abort: refuse to silently overwrite an in-progress session.
    check_same_skill_clobber(SKILL_NAME)

    handoff_content = read_handoff("develop")

    # Cross-skill detection: warn only (different skills don't conflict).
    conflicting_sessions = get_conflicting_sessions(
        SKILL_NAME,
        sessions=detect_active_sessions(),
    )
    if conflicting_sessions:
        print(format_active_session_warning(conflicting_sessions, SKILL_NAME), file=sys.stderr)

    # If a prior fresh start left a state file with a plan_file path, reuse it
    # so we don't orphan the prior skeleton at a new timestamp. The
    # check_same_skill_clobber call above already aborted on in-progress
    # state; if we got here the prior state was either absent or completed.
    sp = _state_path()
    plan_file = None
    if sp.exists():
        try:
            prior = load_state(sp)
            if prior.completed_at is None:
                plan_file = prior.custom.get("plan_file")
        except Exception:
            plan_file = None

    if not plan_file:
        plan_filename = generate_plan_filename(handoff_content)
        plans_dir = runtime_memory_dir() / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        plan_file = str(plans_dir / plan_filename)

    # Materialize the skeleton file so Architect/Planner replace markers
    # rather than invent structure.
    write_plan_skeleton(Path(plan_file), force=getattr(args, "force", False))

    state = SkillState(skill_name=SKILL_NAME, max_step=MAX_STEP)
    state.current_step = 1
    state.quick_mode = args.quick
    state.started_at = now_iso()
    state.custom["handoff_content"] = handoff_content
    state.custom["plan_file"] = plan_file

    save_state(state, sp)

    # Print state path so Codex knows where it is
    print(f"STATE FILE: {sp}\n", file=sys.stderr)

    template = load_template("plan/context")
    variables = _build_variables(state)
    body = render_template(template, variables)

    # Mark step 1 complete
    state.mark_step_complete(1)
    save_state(state, sp)

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
    """Steps 2-6: Load state, render template, output prompt."""
    # Find state file
    sp = validate_state_path(state_file, SKILL_NAME) if state_file else None
    if sp is None:
        sp = find_state_file(SKILL_NAME)
        if sp is None:
            sp = _state_path()

    if not sp.exists():
        print("ERROR: No plan session in progress. Run step 1 first.")
        print(f"Expected state file at: {_state_path()}")
        sys.exit(1)

    try:
        state = load_state(sp)
    except Exception as e:
        print(f"ERROR: Failed to load state: {e}")
        print("Delete the state file and re-run step 1.")
        sys.exit(1)

    # Map steps to template names
    template_map = {
        2: "plan/architecture",
        3: "plan/creation",
        4: "plan/review_loop",
        5: "plan/approval",
        6: "plan/handoff",
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
    if step == MAX_STEP:
        plan_file = state.custom.get("plan_file")
        if not plan_file:
            sys.exit(
                "ERROR: state.custom['plan_file'] missing at handoff — "
                "re-run step 1 to initialize."
            )

        # Completion gate: refuse to mark complete while skeleton markers remain.
        unfilled = find_unfilled_sections(Path(plan_file))
        if unfilled:
            warning = (
                "\n\n---\n\n"
                "**WORKFLOW NOT COMPLETE — unfilled plan sections detected.**\n\n"
                "The following sections still contain `<!-- FORGE_SKELETON: ... -->` "
                "markers and need to be filled in before the plan is ready:\n\n"
                + "\n".join(f"- {s}" for s in unfilled)
                + f"\n\nFile: `{plan_file}`\n\n"
                "Fill these sections, then re-run step 6."
            )
            body += warning
            # Don't set completed_at; don't write handoff; don't clear state.
            # Preserve in-progress status so resume can pick up.
            save_state(state, sp)
        else:
            state.mark_step_complete(step)
            state.completed_at = now_iso()
            save_state(state, sp)

            handoff_path = write_handoff(
                skill_name=SKILL_NAME,
                state=state,
                context={
                    "Plan location": plan_file,
                    "Task count": state.custom.get("task_count", "see plan"),
                    "Dependencies": state.custom.get("dependencies_summary", "see plan"),
                },
                suggested_next="implement",
            )

            dashboard = render_dashboard(state)
            body += f"\n\n---\n\n{dashboard}"
            body += f"\n\nHandoff written to: {handoff_path}"
            handoff_menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
            clear_state_file(sp)

    if step != MAX_STEP:
        state.mark_step_complete(step)
        save_state(state, sp)

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
        "--force",
        action="store_true",
        help="Overwrite an existing plan file at step 1 even if it contains content.",
    )
    args = parser.parse_args()

    if validate_step_or_complete(args.step, MAX_STEP, SKILL_NAME):
        return

    if args.step == 1:
        handle_step_1(args)
    else:
        handle_step_n(args.step, state_file=args.state)


if __name__ == "__main__":
    main()
