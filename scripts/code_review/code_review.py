#!/usr/bin/env python3
"""Code review skill orchestrator.

Script-driven workflow that outputs formatted prompts for Codex to follow.
Each --step invocation loads state, selects the appropriate prompt template,
substitutes variables, and prints the prompt for Codex to execute.

Steps:
  1. Target Detection — detect PR/branch/files/handoff, initialize state
  2. Mode Selection — auto-detect or use --mode flag, output mode-specific instructions
  3. Team Dispatch — dispatch all reviewers in parallel with mode-specific focus
  4. Deep Dive — Investigator deep-dives on critical findings
  5. Discussion — interactive review with user
  6. Report — write code review report, handoff, dashboard
"""

from __future__ import annotations

import sys
from pathlib import Path

# Auto-detect repo root so this works from any working directory
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # scripts/code-review/ -> scripts/ -> repo root

# Add repo root to sys.path so imports resolve without PYTHONPATH
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.evaluate.plan_resolver import (
    AmbiguousPlanError,
    extract_title,
    format_native_plan_hints,
    resolve_plan_file,
)
from scripts.shared.orchestrator import (
    SkillState,
    append_skill_run_memory,
    build_base_parser,
    build_next_command,
    build_skill_handoff_menu,
    check_same_skill_clobber,
    clear_state_file,
    _detect_repo_root,
    detect_active_sessions,
    find_state_file,
    format_active_session_warning,
    format_step_output,
    get_conflicting_sessions,
    load_state,
    now_iso,
    consume_handoff,
    read_memory_file,
    render_dashboard,
    runtime_state_path,
    save_state,
    validate_state_path,
    validate_step,
    validate_step_or_complete,
    write_handoff,
)
from scripts.evaluate.template_engine import load_template, render_template

PROMPTS_DIR = REPO_ROOT / "prompts"
SKILL_NAME = "code-review"
MAX_STEP = 6

PHASE_NAMES = {
    1: "Target Detection",
    2: "Mode Selection",
    3: "Team Dispatch",
    4: "Deep Dive",
    5: "Discussion",
    6: "Report",
}

PHASE_TODOS = {
    1: [
        {"content": "Detect PR/branch/files target",
         "activeForm": "Detecting review target"},
        {"content": "Read handoff-implement.md",
         "activeForm": "Reading handoff"},
    ],
    2: [
        {"content": "Select review mode (pr/deep/architecture)",
         "activeForm": "Selecting mode"},
    ],
    3: [
        {"content": "Dispatch reviewers in parallel",
         "activeForm": "Dispatching reviewers"},
        {"content": "Wait for all reviewer findings",
         "activeForm": "Waiting for findings"},
    ],
    4: [
        {"content": "Dispatch Investigator for deep dive on critical findings",
         "activeForm": "Deep-diving critical findings"},
    ],
    5: [
        {"content": "Run interactive triage with user",
         "activeForm": "Running triage with user"},
        {"content": "Resolve or dismiss findings",
         "activeForm": "Resolving findings"},
    ],
    6: [
        {"content": "Write code review report",
         "activeForm": "Writing report"},
        {"content": "Write handoff and render dashboard",
         "activeForm": "Writing handoff"},
    ],
}

# Maps mode -> template name for step 3
MODE_TEMPLATES = {
    "pr": "code-review/diff_analysis",
    "deep": "code-review/security_scan",
    "architecture": "code-review/architecture_check",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_path() -> Path:
    """Return the default state file path."""
    return runtime_state_path(SKILL_NAME)




def _detect_mode(target: str, handoff_content: str) -> str:
    """Auto-detect review mode from target and handoff content.

    Returns 'pr', 'deep', or 'architecture'.
    """
    if not target and not handoff_content:
        return "pr"

    combined = (target + " " + handoff_content).lower()

    # If target looks like a PR number
    if target and target.strip().isdigit():
        return "pr"

    # If target starts with # (PR reference)
    if target and target.strip().startswith("#"):
        return "pr"

    # Deep mode indicators
    deep_keywords = ["bug", "issue", "error", "fail", "crash", "troubleshoot",
                     "investigate", "trace", "debug", "security", "vulnerability"]
    if any(kw in combined for kw in deep_keywords):
        return "deep"

    # Architecture mode indicators
    arch_keywords = ["architecture", "design", "pattern", "coupling", "solid",
                     "refactor", "structure", "dependency", "module"]
    if any(kw in combined for kw in arch_keywords):
        return "architecture"

    return "pr"


def _build_variables(state: SkillState) -> dict[str, str]:
    """Build template variable dict from state."""
    mode = state.custom.get("mode", "pr")
    target = state.custom.get("target", "(auto-detected)")
    handoff_content = state.custom.get("handoff_content", "")
    plan_path = (state.custom.get("plan_path") or "").strip()
    repo_root = _detect_repo_root(Path.cwd())
    native_plan_hints = format_native_plan_hints(repo_root)
    if plan_path:
        plan_link_section = (
            "## Plan reference\n\n"
            f"Compare the review target against this plan (intent vs code): `{plan_path}`\n"
        )
    else:
        plan_link_section = ""

    # Build handoff section
    if handoff_content:
        handoff_section = (
            "## Handoff from Implement\n\n"
            "<handoff>\n"
            f"{handoff_content}\n"
            "</handoff>"
        )
    else:
        handoff_section = (
            "## No Handoff Found\n\n"
            "No handoff-implement.md was found. Using target from arguments or git state."
        )

    # Build findings summary
    findings_text = ""
    if state.findings:
        for f in state.findings:
            status = f" [{f['status']}]" if f.get("status") != "open" else ""
            note = f" -- User: {f['user_note']}" if f.get("user_note") else ""
            findings_text += (
                f"- **{f['id']}** ({f['severity']}): {f['title']}{status}{note}\n"
                f"  {f['detail']}\n\n"
            )
    else:
        findings_text = "(No findings yet)"

    # Mode display
    mode_display = {
        "pr": "PR Review -- analyze diff and changes",
        "deep": "Deep Troubleshooting Review -- trace code paths, investigate issues",
        "architecture": "Architecture Review -- design patterns, coupling, SOLID principles",
    }

    # Team assignments based on quick mode
    if state.quick_mode:
        team_section = (
            "**Quick mode active** -- abbreviated review:\n\n"
            "| Agent | Focus |\n"
            "|-------|-------|\n"
            "| Architect | Design and structure review |\n"
            "| QA Reviewer | Correctness and test coverage |\n"
        )
    else:
        team_section = (
            "| Agent | Focus |\n"
            "|-------|-------|\n"
            "| Architect | Design patterns, structure, coupling |\n"
            "| Security Reviewer | Auth, data flow, injection, secrets |\n"
            "| QA Reviewer | Correctness, edge cases, test coverage |\n"
            "| Critic | Assumptions, missed cases, over-engineering |\n"
            "| Investigator | Deep code path tracing, dependency analysis |\n"
            "| Doc-writer | Documentation completeness, API docs |\n"
        )

    return {
        "MODE": mode,
        "MODE_DISPLAY": mode_display.get(mode, mode),
        "TARGET": target,
        "HANDOFF_CONTENT": handoff_section,
        "FINDINGS": findings_text.strip(),
        "TEAM_ASSIGNMENTS": team_section,
        "QUICK_MODE": "yes" if state.quick_mode else "no",
        "SKILL_NAME": SKILL_NAME,
        "PLAN_PATH": plan_path or "(none)",
        "PLAN_LINK_SECTION": plan_link_section,
        "NATIVE_PLAN_HINTS": native_plan_hints,
    }


def _next_command(step: int, state_path: str = "") -> str:
    """Build the command for the next step."""
    extra = {}
    if state_path:
        extra["state"] = state_path
    return build_next_command(SCRIPT_DIR / "code_review.py", step, MAX_STEP, **extra)


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------

def handle_step_1(args) -> None:
    """Step 1: Target Detection -- detect PR/branch/files/handoff, init state."""
    # Same-skill abort: refuse to silently overwrite an in-progress session.
    check_same_skill_clobber(SKILL_NAME)

    # Cross-skill detection: warn only.
    conflicting_sessions = get_conflicting_sessions(
        SKILL_NAME,
        sessions=detect_active_sessions(),
    )
    if conflicting_sessions:
        print(format_active_session_warning(conflicting_sessions, SKILL_NAME), file=sys.stderr)

    # Read handoff from implement
    handoff_content = consume_handoff("implement")

    # Optional plan: path or keywords (includes native Cursor/Claude/Codex plan dirs)
    plan_path = ""
    plan_arg = (getattr(args, "plan", None) or "").strip()
    if plan_arg:
        try:
            plan_path = str(resolve_plan_file(plan_arg, Path.cwd()))
        except AmbiguousPlanError as e:
            print("Multiple plans matched. Choose one:\n", file=sys.stderr)
            for i, p in enumerate(e.matches, 1):
                print(f"  {i}. {p} — {extract_title(p)}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    # Determine target
    target = getattr(args, "target", None) or ""

    # Determine mode
    mode = getattr(args, "mode", None) or ""
    if not mode:
        mode = _detect_mode(target, handoff_content)

    state = SkillState(skill_name=SKILL_NAME, max_step=MAX_STEP)
    state.current_step = 1
    state.quick_mode = args.quick
    state.started_at = now_iso()
    state.custom["mode"] = mode
    state.custom["target"] = target
    state.custom["handoff_content"] = handoff_content
    state.custom["plan_path"] = plan_path

    sp = _state_path()
    save_state(state, sp)

    # Print state path so Codex knows where it is
    print(f"STATE FILE: {sp}\n", file=sys.stderr)

    template = load_template("code-review/target_detection")
    variables = _build_variables(state)
    body = render_template(template, variables)

    state.mark_step_complete(1)
    save_state(state, sp)
    append_skill_run_memory(
        SKILL_NAME,
        1,
        PHASE_NAMES[1],
        "Initialized code-review session and detected target/mode.",
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
    """Steps 2-6: Load state, render template, output prompt."""
    sp = validate_state_path(state_file, SKILL_NAME) if state_file else None
    if sp is None:
        sp = find_state_file(SKILL_NAME)
        if sp is None:
            sp = _state_path()

    if not sp.exists():
        print("ERROR: No code-review session in progress. Run step 1 first.")
        print(f"Expected state file at: {_state_path()}")
        sys.exit(1)

    try:
        state = load_state(sp)
    except Exception as e:
        print(f"ERROR: Failed to load state: {e}")
        print("Delete the state file and re-run step 1.")
        sys.exit(1)

    # Map steps to template names
    mode = state.custom.get("mode", "pr")

    template_map = {
        2: "code-review/mode_selection",
        3: MODE_TEMPLATES.get(mode, "code-review/diff_analysis"),
        4: "code-review/deep_dive",
        5: "code-review/discussion",
        6: "code-review/report",
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

        open_count = len(state.open_findings())
        total_count = len(state.findings)

        handoff_path = write_handoff(
            skill_name=SKILL_NAME,
            state=state,
            context={
                "Review mode": mode,
                "Target": state.custom.get("target", "N/A"),
                "Findings": f"{open_count} open, {total_count - open_count} resolved of {total_count} total",
                "Critical findings": str(sum(
                    1 for f in state.open_findings() if f.get("severity") == "critical"
                )),
            },
            suggested_next="test",
        )

        dashboard = render_dashboard(state)
        body += f"\n\n---\n\n{dashboard}"
        body += f"\n\nHandoff written to: {handoff_path}"
        handoff_menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
        clear_state_file(sp)
        run_summary = "Completed code-review workflow, wrote handoff, and closed session state."

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
        "--mode", type=str, choices=["pr", "deep", "architecture"],
        default=None,
        help="Review mode: pr (PR diff), deep (troubleshooting), architecture (design patterns)"
    )
    parser.add_argument(
        "--target", type=str, default=None,
        help="PR number, branch name, or file paths to review"
    )
    parser.add_argument(
        "--plan", type=str, default=None,
        help="Optional plan file path or keywords (searches repo + native .cursor/.claude/.codex plans)",
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
