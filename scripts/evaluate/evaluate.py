#!/usr/bin/env python3
"""Evaluate skill orchestrator.

Script-driven workflow that outputs formatted prompts for Codex to follow.
Each --step invocation loads state, selects the appropriate prompt template,
substitutes variables, and prints the prompt for Codex to execute.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Auto-detect repo root so this works from any working directory
SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent  # scripts/evaluate/ -> scripts/ -> forge/

# Add repo root to sys.path so imports resolve without PYTHONPATH
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from scripts.evaluate.state import EvalState, load_state, save_state, state_path_for_plan, STATE_FILENAME
from scripts.evaluate.state import clear_state
from scripts.evaluate.plan_resolver import resolve_plan, extract_title
from scripts.evaluate.mode_detector import extract_file_references, detect_mode
from scripts.evaluate.template_engine import load_template, render_template
from scripts.shared.orchestrator import (
    build_next_command,
    build_skill_handoff_menu,
    build_skill_todos,
    detect_active_sessions,
    format_active_session_warning,
    format_phase_todos,
    format_same_skill_continuation,
    get_conflicting_sessions,
    parse_continuation_command,
    validate_step_or_complete,
)

PROMPTS_DIR = PLUGIN_ROOT / "prompts"

PRE_PHASES = {
    2: "pre/feasibility",
    3: "pre/completeness",
    4: "pre/codebase_alignment",
    5: "pre/risk_dependencies",
    6: "shared/discussion",
    7: "report",
}

POST_PHASES = {
    2: "post/completeness_audit",
    3: "post/correctness",
    4: "post/code_quality",
    5: "post/performance",
    6: "post/operational_readiness",
    7: "shared/discussion",
    8: "report",
}

REVIEW_PHASES = {
    1: "review/team_dispatch",
    2: "review/findings_aggregation",
    3: "review/remediation",
    4: "shared/discussion",
    5: "report",
}

PHASE_NAMES = {
    "pre": {1: "Plan Parsing", 2: "Feasibility", 3: "Completeness", 4: "Codebase Alignment", 5: "Risk & Dependencies", 6: "Discussion", 7: "Report"},
    "post": {1: "Plan Parsing", 2: "Completeness Audit", 3: "Correctness", 4: "Code Quality", 5: "Performance", 6: "Operational Readiness", 7: "Discussion", 8: "Report"},
    "review": {1: "Team Dispatch", 2: "Findings Aggregation", 3: "Remediation", 4: "Discussion", 5: "Report"},
}

# Phase todos keyed by (mode, step)
PHASE_TODOS = {
    ("pre", 1): [
        {"content": "Parse plan and extract file references",
         "activeForm": "Parsing plan"},
        {"content": "Detect pre vs post implementation mode",
         "activeForm": "Detecting mode"},
    ],
    ("pre", 2): [
        {"content": "Assess feasibility of each plan step",
         "activeForm": "Assessing feasibility"},
    ],
    ("pre", 3): [
        {"content": "Check plan completeness (error handling, edge cases, tests)",
         "activeForm": "Checking completeness"},
    ],
    ("pre", 4): [
        {"content": "Check plan against existing code patterns and conventions",
         "activeForm": "Checking codebase alignment"},
    ],
    ("pre", 5): [
        {"content": "Analyze dependencies, risks, rollback strategies, and failure modes",
         "activeForm": "Analyzing risks and dependencies"},
    ],
    ("pre", 6): [
        {"content": "Present findings to user for triage",
         "activeForm": "Running triage with user"},
    ],
    ("pre", 7): [
        {"content": "Write evaluation report alongside plan",
         "activeForm": "Writing report"},
    ],
    ("post", 1): [
        {"content": "Parse plan and extract file references",
         "activeForm": "Parsing plan"},
    ],
    ("post", 2): [
        {"content": "Audit completeness (what was implemented vs planned)",
         "activeForm": "Auditing completeness"},
    ],
    ("post", 3): [
        {"content": "Verify correctness of implementation",
         "activeForm": "Verifying correctness"},
    ],
    ("post", 4): [
        {"content": "Review code quality and test quality",
         "activeForm": "Reviewing code quality"},
    ],
    ("post", 5): [
        {"content": "Review performance patterns and scalability concerns",
         "activeForm": "Reviewing performance"},
    ],
    ("post", 6): [
        {"content": "Check operational readiness (error handling, logging, resources, deployment)",
         "activeForm": "Checking operational readiness"},
    ],
    ("post", 7): [
        {"content": "Present findings to user for triage",
         "activeForm": "Running triage with user"},
    ],
    ("post", 8): [
        {"content": "Write evaluation report alongside plan",
         "activeForm": "Writing report"},
    ],
    ("review", 1): [
        {"content": "Dispatch full review team in parallel",
         "activeForm": "Dispatching review team"},
    ],
    ("review", 2): [
        {"content": "Aggregate findings from all reviewers",
         "activeForm": "Aggregating findings"},
    ],
    ("review", 3): [
        {"content": "Run remediation review loop",
         "activeForm": "Running remediation"},
    ],
    ("review", 4): [
        {"content": "Present findings to user for triage",
         "activeForm": "Running triage with user"},
    ],
    ("review", 5): [
        {"content": "Write review report",
         "activeForm": "Writing review report"},
    ],
}


def _findings_sidecar_path(state_dir: Path, step: int) -> Path:
    """Sidecar file where the LLM dumps findings emitted during step N."""
    return state_dir / f".evaluate-findings-step{step}.json"


def _ingest_findings_sidecars(state: EvalState, state_dir: Path, current_step: int) -> int:
    """Ingest any findings sidecars emitted by prior steps.

    Looks for `.evaluate-findings-stepN.json` at the same path as the state
    file for every step before `current_step`, parses each as a JSON array
    of `{phase, severity, title, detail}` objects, calls `state.add_finding`
    for each, then deletes the sidecar.

    Returns the number of findings ingested. Tolerant of malformed files —
    bad entries are skipped with a warning to stderr.
    """
    ingested = 0
    for step in range(1, current_step):
        sidecar = _findings_sidecar_path(state_dir, step)
        if not sidecar.exists():
            continue
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARNING: skipping malformed findings sidecar {sidecar}: {e}", file=sys.stderr)
            continue
        if not isinstance(data, list):
            print(f"WARNING: findings sidecar {sidecar} is not a JSON array, skipping", file=sys.stderr)
            continue
        for entry in data:
            if not isinstance(entry, dict):
                continue
            try:
                state.add_finding(
                    phase=str(entry.get("phase", f"step{step}")),
                    severity=str(entry.get("severity", "warning")),
                    title=str(entry.get("title", "(untitled)")),
                    detail=str(entry.get("detail", "")),
                )
                ingested += 1
            except Exception as e:
                print(f"WARNING: failed to add finding from {sidecar}: {e}", file=sys.stderr)
        try:
            sidecar.unlink()
        except OSError:
            pass
    return ingested


def _build_variables(
    state: EvalState,
    plan_content: str,
    state_dir: Path | None = None,
    step: int | None = None,
) -> dict[str, str]:
    """Build template variable dict from state."""
    findings_text = ""
    if state.findings:
        for f in state.findings:
            status = f" [{f['status']}]" if f.get('status') != 'open' else ""
            note = f" — User: {f['user_note']}" if f.get('user_note') else ""
            findings_text += f"- **{f['id']}** ({f['severity']}): {f['title']}{status}{note}\n  {f['detail']}\n\n"
    else:
        findings_text = "(No findings yet)"

    sidecar_path = ""
    if state_dir is not None and step is not None:
        sidecar_path = str(_findings_sidecar_path(state_dir, step))

    return {
        "PLAN_CONTENT": plan_content,
        "PLAN_PATH": state.plan_path,
        "PLAN_NAME": state.plan_name,
        "MODE": state.mode or "unknown",
        "REFERENCED_FILES": ", ".join(state.referenced_files) if state.referenced_files else "(none extracted yet)",
        "PREVIOUS_FINDINGS": findings_text.strip(),
        "REVIEW_ROUND": str(state.review_round),
        "QUICK_MODE_NOTE": "",
        "FINDINGS_SIDECAR": sidecar_path,
    }


def _max_step_for_mode(mode: str | None) -> int:
    """Return the maximum step number for the given evaluation mode."""
    if mode == "review":
        return 5
    if mode == "post":
        return 8
    return 7  # pre (default)


def _next_command(step: int, state_path: str = "", mode: str | None = None) -> str:
    """Build agent-facing continuation for the next step (``$forge-evaluate`` / slash)."""
    max_step = _max_step_for_mode(mode)
    extra = {}
    if state_path:
        extra["state"] = state_path
    return build_next_command(SCRIPT_DIR / "evaluate.py", step, max_step, **extra)


def _mode_phase_todos(mode: str) -> dict[int, list[dict]]:
    """Convert mode-keyed PHASE_TODOS to step-keyed dict for a given mode."""
    return {
        step: todos
        for (m, step), todos in PHASE_TODOS.items()
        if m == mode
    }


def _format_output(
    title: str,
    body: str,
    next_cmd: str,
    phase_todos: list[dict] | None = None,
    mode: str | None = None,
    step: int | None = None,
    handoff_menu: str | None = None,
) -> str:
    """Format step output with title, todos, and continuation directive."""
    header = f"{title}\n{'=' * len(title)}\n\n"

    # Build full skill-level todos when mode info is available
    if mode and step and mode in PHASE_NAMES:
        mode_names = PHASE_NAMES[mode]
        mode_todos = _mode_phase_todos(mode)
        skill_todos = build_skill_todos(
            mode_names, mode_todos,
            current_step=step,
            last_completed_step=step - 1,
        )
        todos_section = format_phase_todos(skill_todos)
    elif phase_todos:
        todos_section = format_phase_todos(phase_todos)
    else:
        todos_section = ""
    output = header + todos_section + body

    if handoff_menu:
        return output + handoff_menu
    elif next_cmd:
        ns, sp_ = parse_continuation_command(next_cmd)
        if ns is None and step is not None:
            ns = step + 1
        elif ns is None:
            ns = 2
        return output + format_same_skill_continuation(ns, sp_)
    else:
        return output + "\n\nWORKFLOW COMPLETE — return the report location to the user."


def handle_step_1(args: argparse.Namespace) -> None:
    """Step 1: Plan resolution, parsing, and mode detection (or review dispatch)."""
    # Cross-session detection: only warn on fresh starts (no --state arg)
    if not getattr(args, "state", None):
        conflicting_sessions = get_conflicting_sessions(
            "evaluate",
            sessions=detect_active_sessions(),
        )
        if conflicting_sessions:
            print(format_active_session_warning(conflicting_sessions, "evaluate"), file=sys.stderr)

    # Review mode: skip plan resolution entirely
    if getattr(args, "mode", None) == "review":
        handle_step_1_review(args)
        return

    if not args.plan:
        print("ERROR: --plan is required for step 1. Provide a file path or keywords.")
        sys.exit(1)

    cwd = Path.cwd()
    try:
        result = resolve_plan(args.plan, cwd, return_matches=True)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if isinstance(result, list) and len(result) > 1:
        print("Multiple plans found. Present these to the user and ask which one to evaluate:\n")
        for i, p in enumerate(result, 1):
            title = extract_title(p)
            print(f"  {i}. {p} — {title}")
        print(
            "\nThen ask which plan to use and continue with "
            "`$forge:evaluate --step 1 --plan '<chosen path>'`."
        )
        return

    plan_path = result[0] if isinstance(result, list) else result
    plan_content = plan_path.read_text(encoding="utf-8")
    plan_name = plan_path.stem

    refs = extract_file_references(plan_content)

    plan_mtime = datetime.fromtimestamp(plan_path.stat().st_mtime, tz=timezone.utc).isoformat()
    forced_mode = getattr(args, "mode", None)
    if forced_mode in ("pre", "post"):
        mode = forced_mode
        matched, total = 0, 0
    else:
        mode, matched, total = detect_mode(refs, str(cwd), plan_mtime)

    state = EvalState(
        plan_path=str(plan_path.resolve()),
        plan_name=plan_name,
    )
    state.mode = mode
    state.current_step = 1
    state.referenced_files = refs
    sp = state_path_for_plan(str(plan_path))
    save_state(state, sp)

    # Print state path so user/Codex knows where it is
    print(f"STATE FILE: {sp}\n", file=sys.stderr)

    template = load_template("shared/plan_parsing")
    variables = _build_variables(state, plan_content)
    body = render_template(template, variables)

    body += f"\n\n---\n\n## Mode Detection\n\n"
    if forced_mode in ("pre", "post"):
        body += f"**Forced mode:** {mode.upper()}\n\n"
    else:
        body += f"**Detected mode:** {'POST-IMPLEMENTATION' if mode == 'post' else 'PRE-IMPLEMENTATION'}"
        body += f" ({matched}/{total} referenced files show matching changes)\n\n"
    body += f"Confirm this mode with the user. If they want to switch, update the mode.\n"
    body += f"Then proceed to the next step.\n"

    # Mark step 1 complete
    state.mark_step_complete(1)
    save_state(state, sp)

    max_step = _max_step_for_mode(mode)
    title = f"EVALUATE — Plan Parsing (Step 1 of {max_step})"
    next_cmd = _next_command(1, state_path=str(sp), mode=mode)
    phase_todos = PHASE_TODOS.get((mode, 1), [])
    print(_format_output(title, body, next_cmd, phase_todos=phase_todos, mode=mode, step=1))


def handle_step_1_review(args: argparse.Namespace) -> None:
    """Step 1 for review mode: team dispatch (no plan needed)."""
    cwd = Path.cwd()

    state = EvalState(
        plan_path="(review mode)",
        plan_name="review",
    )
    state.mode = "review"
    state.current_step = 1
    state.review_round = 0

    sp = cwd / STATE_FILENAME
    save_state(state, sp)

    print(f"STATE FILE: {sp}\n", file=sys.stderr)

    template = load_template("review/team_dispatch")
    variables = _build_variables(state, "(review mode — no plan)")
    body = render_template(template, variables)

    state.mark_step_complete(1)
    save_state(state, sp)

    title = f"EVALUATE (REVIEW) — Team Dispatch (Step 1 of {_max_step_for_mode('review')})"
    next_cmd = _next_command(1, state_path=str(sp), mode="review")
    phase_todos = PHASE_TODOS.get(("review", 1), [])
    print(_format_output(title, body, next_cmd, phase_todos=phase_todos, mode="review", step=1))


def _find_state_file() -> Path | None:
    """Search for the state file near cwd or in docs/ tree."""
    from scripts.evaluate.state import STATE_FILENAME

    # 1. Current working directory (fast path)
    cwd_candidate = Path.cwd() / STATE_FILENAME
    if cwd_candidate.exists():
        return cwd_candidate

    # 2. Search docs/ tree only (state is written alongside the plan)
    docs_dir = Path.cwd() / "docs"
    if docs_dir.is_dir():
        candidates = list(docs_dir.rglob(STATE_FILENAME))
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            # Multiple evaluations — pick most recently modified
            return max(candidates, key=lambda p: p.stat().st_mtime)

    return None


def handle_step_n(step: int, state_file: str | None = None) -> None:
    """Steps 2-6: Load state, render appropriate template, output prompt."""
    sp = Path(state_file) if state_file else None

    # Search for state file if not provided or doesn't exist
    if sp is None or not sp.exists():
        sp = _find_state_file()

    if sp is None or not sp.exists():
        print("ERROR: No evaluation in progress. Run step 1 first with --plan.")
        print("If the state file is elsewhere, pass --state <path>")
        sys.exit(1)

    try:
        state = load_state(sp)
    except json.JSONDecodeError:
        print(f"ERROR: State file is corrupted: {sp}")
        print("Delete it and re-run step 1.")
        sys.exit(1)
    except KeyError as e:
        print(f"ERROR: State file is invalid — {e}")
        print("Delete it and re-run step 1.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: State file not found at {sp}")
        sys.exit(1)

    # Pull in findings the LLM dumped to sidecar files during prior steps.
    ingested = _ingest_findings_sidecars(state, sp.parent, step)
    if ingested:
        save_state(state, sp)

    plan_path = Path(state.plan_path)
    if state.mode == "review":
        plan_content = "(review mode — no plan)"
    elif plan_path.exists():
        plan_content = plan_path.read_text(encoding="utf-8")
    else:
        plan_content = "(plan file not found)"

    if state.mode == "review":
        phases = REVIEW_PHASES
    elif state.mode == "post":
        phases = POST_PHASES
    else:
        phases = PRE_PHASES
    max_step = _max_step_for_mode(state.mode)

    template_name = phases.get(step)
    if not template_name:
        print(f"ERROR: Invalid step {step} for mode {state.mode}")
        sys.exit(1)

    # Load template before mutating state — a missing template must not leave
    # state half-written.
    template = load_template(template_name)
    variables = _build_variables(state, plan_content, state_dir=sp.parent, step=step)
    body = render_template(template, variables)

    state.current_step = step
    save_state(state, sp)

    # Mark this step complete
    state.mark_step_complete(step)
    save_state(state, sp)

    mode_label = state.mode.upper() if state.mode else "UNKNOWN"
    phase_name = PHASE_NAMES.get(state.mode or "pre", {}).get(step, f"Step {step}")
    title = f"EVALUATE ({mode_label}) — {phase_name} (Step {step} of {max_step})"

    next_cmd = _next_command(step, state_path=str(sp), mode=state.mode)
    phase_todos = PHASE_TODOS.get((state.mode or "pre", step), [])
    handoff_menu = None
    if not next_cmd:
        handoff_menu = build_skill_handoff_menu("evaluate", state, sp)
        clear_state(sp)
    print(_format_output(title, body, next_cmd, phase_todos=phase_todos, mode=state.mode or "pre", step=step, handoff_menu=handoff_menu))


def main():
    parser = argparse.ArgumentParser(description="Evaluate skill orchestrator")
    parser.add_argument("--step", type=int, required=True, help="Phase number (1-7 for pre, 1-8 for post, 1-5 for review)")
    parser.add_argument("--plan", type=str, help="Plan file path or keywords (step 1 only, pre/post modes)")
    parser.add_argument("--state", type=str, help="Path to .evaluate-state.json (auto-detected if omitted)")
    parser.add_argument("--mode", choices=["pre", "post", "review"], help="Force evaluation mode")
    parser.add_argument("--team", action="store_true", help="Enable team dispatch in pre/post modes")

    args = parser.parse_args()

    # Resolve mode for max_step: prefer args.mode, but if resuming (step > 1
    # with no --mode passed), fall back to the saved state's mode so the cap
    # matches what the workflow is actually running. Without this, a post-mode
    # session resumed without --mode would advertise "of 8" in the title but
    # validate_step_or_complete would say "ends at step 7" using pre's default.
    effective_mode = args.mode
    if effective_mode is None and args.step > 1:
        sp = Path(args.state) if args.state else _find_state_file()
        if sp is not None and sp.exists():
            try:
                effective_mode = load_state(sp).mode
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                pass  # fall through to None → default

    max_step = _max_step_for_mode(effective_mode)
    if validate_step_or_complete(args.step, max_step, "evaluate"):
        return

    if args.step == 1:
        handle_step_1(args)
    else:
        handle_step_n(args.step, state_file=args.state)


if __name__ == "__main__":
    main()
