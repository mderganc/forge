#!/usr/bin/env python3
"""Diagnose skill orchestrator.

Script-driven workflow that outputs formatted prompts for Codex to follow.
Each --step invocation loads state, selects the appropriate prompt template,
substitutes variables, and prints the prompt for Codex to execute.

7-phase pipeline:
  1. Define & Classify — incident profile, first-principles baseline, technique routing
  2. Observe & Gather Evidence — observations vs assumptions
  3. Decompose (MECE) — MECE tree + 5 Whys on branches (mandatory core quartet)
  4. Analyze & Rank — full-register elimination; hypothesis register gate
  5. Solution Generation
  6. Implement & Validate (complexity-gated)
  7. Report & Prevention — full 20-technique coverage matrix + quartet verification

See ``prompts/diagnose/technique_catalog.md`` for toolbox + use-case routing rules.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Auto-detect repo root so this works from any working directory
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # scripts/diagnose/ -> scripts/ -> repo root

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
    ensure_runtime_dirs,
    find_state_file,
    format_step_output,
    print_remaining_session_warning,
    run_step1_session_hygiene,
    load_state,
    now_iso,
    resolve_step1_state_path,
    runtime_state_path,
    save_state,
    validate_state_path,
    validate_step,
    validate_step_or_complete,
    write_handoff,
    render_dashboard,
)
from scripts.diagnose.hypothesis_register import (
    format_gate_block,
    load_register,
    register_path,
    summarize_register,
    validate_elimination,
    validate_register,
)
from scripts.evaluate.template_engine import load_template, render_template

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_NAME = "diagnose"
MAX_STEP = 7

PROMPTS_DIR = REPO_ROOT / "prompts"

PHASE_TEMPLATES = {
    1: "diagnose/define",
    2: "diagnose/evidence",
    3: "diagnose/decompose",
    4: "diagnose/analyze",
    5: "diagnose/solutions",
    6: "diagnose/quick_fix",
    7: "diagnose/report",
}

PHASE_NAMES = {
    1: "Define & Classify",
    2: "Observe & Gather Evidence",
    3: "Decompose (MECE)",
    4: "Analyze & Rank",
    5: "Solution Generation",
    6: "Implement & Validate",
    7: "Report & Prevention",
}

PHASE_TODOS = {
    1: [
        {"content": "Build Kepner-Tregoe IS/IS-NOT matrix",
         "activeForm": "Building IS/IS-NOT matrix"},
        {"content": "Classify problem domain via Cynefin framework",
         "activeForm": "Classifying domain"},
        {"content": "First-principles baseline + incident-profile technique routing",
         "activeForm": "First-principles + routing"},
    ],
    2: [
        {"content": "Gather evidence via log analyzer and git hotspots",
         "activeForm": "Gathering evidence"},
        {"content": "Collect metrics and establish baseline",
         "activeForm": "Collecting metrics"},
        {"content": "Separate observations vs assumptions with falsification paths",
         "activeForm": "Sorting observations"},
    ],
    3: [
        {"content": "Build MECE cause tree (Fishbone categories)",
         "activeForm": "Building cause tree"},
        {"content": "Draft ≥10 falsifiable hypotheses in register sidecar",
         "activeForm": "Writing hypothesis register"},
        {"content": "Advance 5 Whys + MECE quartet on primary branches",
         "activeForm": "5 Whys + MECE"},
    ],
    4: [
        {"content": "Eliminate all hypotheses via falsification tests (discriminating order)",
         "activeForm": "Eliminating hypotheses"},
        {"content": "Run FMEA scoring on full candidate list",
         "activeForm": "Running FMEA scoring"},
        {"content": "Apply counterfactual validation on plausible hypotheses",
         "activeForm": "Running counterfactual validation"},
        {"content": "Confirm root cause with evidence; persist register",
         "activeForm": "Confirming root cause"},
    ],
    5: [
        {"content": "Generate solutions only for confirmed root causes",
         "activeForm": "Generating solutions"},
        {"content": "Run pre-mortem on each proposed fix",
         "activeForm": "Running pre-mortem"},
    ],
    6: [
        {"content": "Apply fix (if simple complexity)",
         "activeForm": "Applying fix"},
        {"content": "Validate fix addresses root cause",
         "activeForm": "Validating fix"},
    ],
    7: [
        {"content": "Finalize Technique Coverage Matrix (all 20 + quartet audit)",
         "activeForm": "Technique matrix"},
        {"content": "Write diagnostic report with prevention measures",
         "activeForm": "Writing diagnostic report"},
        {"content": "Write handoff and render dashboard",
         "activeForm": "Writing handoff"},
    ],
}

# Phases where each autonomy mode pauses for user approval
AUTONOMY_GATES = {
    "guided": {2, 4, 6},       # After evidence, after ranking, before fix
    "autonomous": set(),        # No pauses
    "interactive": {1, 2, 3, 4, 5, 6, 7},  # Every phase
}


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _init_state(mode: str, quick: bool) -> SkillState:
    """Create a fresh diagnose state."""
    state = SkillState(skill_name=SKILL_NAME)
    state.max_step = MAX_STEP
    state.current_step = 1
    state.quick_mode = quick
    state.started_at = now_iso()
    state.custom["autonomy_mode"] = mode
    state.custom["fix_complexity"] = "unknown"  # set in phase 5/6
    state.custom.setdefault("hypothesis_min", 10)
    state.custom.setdefault("hypothesis_regen_attempts", 0)
    state.custom.setdefault("hypothesis_validation_attempts", 0)
    return state


def _state_path() -> Path:
    """Return default state file location."""
    return runtime_state_path(SKILL_NAME)


def _load_or_fail(state_file: str | None) -> tuple[SkillState, Path]:
    """Load state or exit with error."""
    sp = validate_state_path(state_file, SKILL_NAME) if state_file else None

    if sp is None:
        sp = find_state_file(SKILL_NAME)

    if sp is None or not sp.exists():
        print("ERROR: No diagnosis in progress. Run step 1 first.")
        print("If the state file is elsewhere, pass --state <path>")
        sys.exit(1)

    try:
        state = load_state(sp)
    except json.JSONDecodeError:
        print(f"ERROR: State file is corrupted: {sp}")
        print("Delete it and re-run step 1.")
        sys.exit(1)
    except (KeyError, FileNotFoundError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    return state, sp


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def _build_variables(
    state: SkillState,
    *,
    state_path: Path | None = None,
    step: int | None = None,
) -> dict[str, str]:
    """Build template variable dict from state."""
    mode = state.custom.get("autonomy_mode", "guided")
    complexity = state.custom.get("fix_complexity", "unknown")
    hypothesis_min = int(state.custom.get("hypothesis_min", 10))
    hypothesis_gate = ""
    hypothesis_summary = "(Not evaluated yet)"

    if state_path is not None:
        reg_file = register_path(state_path.parent)
        reg_data = load_register(reg_file)
        hypothesis_summary = summarize_register(reg_data)
        active_step = step if step is not None else state.current_step
        if active_step >= 4:
            ok, _ = validate_register(reg_data, min_required=hypothesis_min, path=reg_file)
            if ok and reg_data:
                state.custom["hypothesis_register_summary"] = hypothesis_summary

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

    # Build dispatch history
    dispatch_text = ""
    if state.dispatches:
        for d in state.dispatches:
            agent = d.agent if hasattr(d, "agent") else d.get("agent", "?")
            step = d.step if hasattr(d, "step") else d.get("step", "?")
            done = d.completed if hasattr(d, "completed") else d.get("completed", False)
            mark = "done" if done else "pending"
            dispatch_text += f"- {agent} (step {step}): {mark}\n"
    else:
        dispatch_text = "(None yet)"

    # Autonomy gate message
    gates = AUTONOMY_GATES.get(mode, AUTONOMY_GATES["guided"])
    if state.current_step in gates:
        autonomy_gate = (
            f"**AUTONOMY GATE ({mode} mode):** Pause here. Present findings to "
            f"the user and wait for approval before proceeding to the next phase."
        )
    else:
        autonomy_gate = (
            f"**Mode: {mode}** — No pause required at this phase. "
            f"Proceed directly to the next step."
        )

    # Complexity check for phase 6
    if complexity == "simple":
        complexity_check = (
            "Complexity assessment: **SIMPLE** (<=2 files, no architectural changes).\n"
            "Proceed with implementation below."
        )
    elif complexity == "complex":
        complexity_check = (
            "Complexity assessment: **COMPLEX** (multi-file or architectural, but a single "
            "dominant implementation path is clear).\n"
            "Skip this phase. Hand off to **`plan`** then `implement`.\n"
            "Write the handoff file with root causes and recommended solution."
        )
    elif complexity == "large":
        complexity_check = (
            "Complexity assessment: **LARGE / SYSTEMIC** (under-specified solution space, "
            "major cross-subsystem trade-offs, or multiple viable architectures).\n"
            "Skip quick implementation in this phase. Hand off to **`develop`** first for "
            "design/brainstorming, then **`plan`**.\n"
            "Write the handoff file with root causes, constraints, and known unknowns."
        )
    else:
        complexity_check = (
            "Complexity not yet assessed. Before proceeding, evaluate:\n"
            "- How many files does the fix touch?\n"
            "- Does it require architectural changes?\n"
            "- Is there one clear implementation shape, or are major design choices still open?\n\n"
            "If <=2 files and no architectural changes → set `fix_complexity` to `simple` and proceed.\n"
            "If multi-file / architectural **and** one dominant fix path → set to `complex` and hand off to `plan`.\n"
            "If systemic / multi-strategy / unclear best shape → set to `large` and hand off to `develop` first."
        )

    return {
        "AUTONOMY_MODE": mode,
        "AUTONOMY_GATE": autonomy_gate,
        "FIX_COMPLEXITY": complexity,
        "COMPLEXITY_CHECK": complexity_check,
        "PREVIOUS_FINDINGS": findings_text.strip(),
        "DISPATCH_HISTORY": dispatch_text.strip(),
        "PLUGIN_ROOT": str(REPO_ROOT),
        "SCRIPT_DIR": str(SCRIPT_DIR),
        "HYPOTHESIS_MIN": str(hypothesis_min),
        "HYPOTHESIS_GATE": hypothesis_gate,
        "HYPOTHESIS_REGISTER_SUMMARY": hypothesis_summary,
    }


@dataclass
class _HypothesisGateResult:
    """Outcome of a hypothesis register gate check."""

    passed: bool
    gate_body: str = ""
    next_step_override: int | None = None
    require_confirmation: bool = False


def _has_hypothesis_override(state: SkillState) -> bool:
    """True when user approved proceeding under minimum (documented override)."""
    reason = state.custom.get("hypothesis_override_reason")
    return bool(reason and str(reason).strip())


def _log_hypothesis_override_bypass(phase: str) -> None:
    print(
        f"[diagnose] hypothesis gate bypassed for {phase}: "
        "hypothesis_override_reason is set",
        file=sys.stderr,
    )


def _check_register_gate(state: SkillState, sp: Path, step: int) -> _HypothesisGateResult:
    """Validate register at step 4 entry."""
    if _has_hypothesis_override(state):
        _log_hypothesis_override_bypass("register")
        return _HypothesisGateResult(passed=True)

    reg_file = register_path(sp.parent)
    reg_data = load_register(reg_file)
    min_required = int(state.custom.get("hypothesis_min", 10))
    ok, issues = validate_register(reg_data, min_required=min_required, path=reg_file)

    if ok:
        return _HypothesisGateResult(passed=True)

    attempts = int(state.custom.get("hypothesis_regen_attempts", 0))
    retry_step = None
    if attempts < 1:
        state.custom["hypothesis_regen_attempts"] = attempts + 1
        retry_step = 3

    gate = format_gate_block(
        issues,
        phase=PHASE_NAMES.get(step, f"Step {step}"),
        retry_step=retry_step,
        attempt=attempts,
        max_attempts=1,
        state_path=str(sp),
    )
    return _HypothesisGateResult(
        passed=False,
        gate_body=gate,
        next_step_override=retry_step,
        require_confirmation=True,
    )


def _check_elimination_gate(state: SkillState, sp: Path, step: int) -> _HypothesisGateResult:
    """Validate elimination at step 5 entry."""
    if _has_hypothesis_override(state):
        _log_hypothesis_override_bypass("elimination")
        return _HypothesisGateResult(passed=True)

    reg_file = register_path(sp.parent)
    reg_data = load_register(reg_file)
    ok, issues = validate_elimination(reg_data, path=reg_file)

    if ok:
        return _HypothesisGateResult(passed=True)

    attempts = int(state.custom.get("hypothesis_validation_attempts", 0))
    retry_step = None
    if attempts < 1:
        state.custom["hypothesis_validation_attempts"] = attempts + 1
        retry_step = 4

    gate = format_gate_block(
        issues,
        phase=PHASE_NAMES.get(step, f"Step {step}"),
        retry_step=retry_step,
        attempt=attempts,
        max_attempts=1,
        state_path=str(sp),
    )
    return _HypothesisGateResult(
        passed=False,
        gate_body=gate,
        next_step_override=retry_step,
        require_confirmation=True,
    )


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------

def handle_step_1(args) -> None:
    """Step 1: Initialize state, render Define & Classify prompt."""
    sp = resolve_step1_state_path(
        SKILL_NAME,
        args.state,
        parallel=getattr(args, "parallel", False),
    )
    # Same-skill abort: refuse to silently overwrite an in-progress session.
    check_same_skill_clobber(
        SKILL_NAME,
        allow_parallel=bool(getattr(args, "parallel", False) or args.state),
        target_state_path=sp,
    )

    run_step1_session_hygiene(SKILL_NAME, sp)
    print_remaining_session_warning(SKILL_NAME)

    mode = getattr(args, "mode", "guided") or "guided"
    quick = getattr(args, "quick", False)

    if sp.exists():
        try:
            state = load_state(sp)
        except Exception:
            state = _init_state(mode, quick)
    else:
        state = _init_state(mode, quick)

    ensure_runtime_dirs()
    save_state(state, sp)

    print(f"STATE FILE: {sp}\n", file=sys.stderr)

    template = load_template(PHASE_TEMPLATES[1])
    variables = _build_variables(state, state_path=sp, step=1)
    body = render_template(template, variables)

    if quick:
        body += (
            "\n\n---\n\n"
            "**QUICK MODE:** Investigator-only. Skip full team dispatch.\n"
            "After this phase, jump to abbreviated evidence collection, "
            "then analyze, fix, and report.\n"
        )

    state.mark_step_complete(1)
    save_state(state, sp)
    append_skill_run_memory(
        SKILL_NAME,
        1,
        PHASE_NAMES[1],
        "Initialized diagnose session and classified incident context.",
        state=state,
        state_path=sp,
    )

    next_cmd = build_next_command(
        SCRIPT_DIR / "orchestrate.py", 1, MAX_STEP,
        mode=mode,
    )
    print(format_step_output(
        SKILL_NAME, 1, MAX_STEP, PHASE_NAMES[1], body,
        next_cmd=next_cmd,
        phase_todos=PHASE_TODOS.get(1, []),
        all_phase_names=PHASE_NAMES,
        all_phase_todos=PHASE_TODOS,
    ))


def handle_step_n(step: int, state_file: str | None = None, mode: str | None = None) -> None:
    """Steps 2-7: Load state, render template, output prompt."""
    state, sp = _load_or_fail(state_file)

    # Load template before mutating state — a missing template must not leave
    # state half-written.
    template_name = PHASE_TEMPLATES.get(step)
    if not template_name:
        print(f"ERROR: No template for step {step}")
        sys.exit(1)

    template = load_template(template_name)
    gate_result: _HypothesisGateResult | None = None
    if step == 4:
        gate_result = _check_register_gate(state, sp, step)
    elif step == 5:
        gate_result = _check_elimination_gate(state, sp, step)

    variables = _build_variables(state, state_path=sp, step=step)
    if gate_result and not gate_result.passed:
        variables["HYPOTHESIS_GATE"] = gate_result.gate_body
    body = render_template(template, variables)

    # Update state
    state.current_step = step
    if mode:
        state.custom["autonomy_mode"] = mode
    save_state(state, sp)

    # Phase 6 special: complexity gate
    fc = state.custom.get("fix_complexity", "unknown")
    if step == 6 and fc == "complex":
        body += (
            "\n\n---\n\n"
            "**COMPLEXITY GATE TRIGGERED (complex):** Fix is too broad for quick implementation here.\n"
            "Write handoff file and direct user to `plan` -> `implement`.\n"
            "Then skip to Phase 7 (Report).\n"
        )
    if step == 6 and fc == "large":
        body += (
            "\n\n---\n\n"
            "**COMPLEXITY GATE TRIGGERED (large / systemic):** Solution space needs design work before planning.\n"
            "Write handoff file and direct user to **`develop`** (brainstorm / design) → then **`plan`** → `implement`.\n"
            "Then skip to Phase 7 (Report).\n"
        )

    # Phase 7: mark complete and write handoff
    is_last = step >= MAX_STEP
    cross_skill_next = None
    handoff_menu = None
    handoff_path: Path | None = None
    run_summary = f"Completed step {step} ({PHASE_NAMES.get(step, f'Step {step}')})."
    if is_last:
        state.mark_step_complete(step)
        state.completed_at = now_iso()
        save_state(state, sp)

        complexity = state.custom.get("fix_complexity", "unknown")
        if complexity == "large":
            suggested_next = "develop"
        elif complexity == "complex":
            suggested_next = "plan"
        else:
            suggested_next = "(end of flow)"

        routing = (
            "develop → plan"
            if complexity == "large"
            else ("plan → implement" if complexity == "complex" else "resolved / choose next skill from menu")
        )

        handoff_path = write_handoff(
            skill_name=SKILL_NAME,
            state=state,
            context={
                "Root cause": state.custom.get("root_cause", "see report"),
                "Fix complexity": complexity,
                "Routing": routing,
                "Autonomy mode": state.custom.get("autonomy_mode", "guided"),
                "Open findings": str(len(state.open_findings())),
            },
            suggested_next=suggested_next,
        )
        handoff_menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
        clear_state_file(sp)
        run_summary = "Completed diagnose workflow, wrote handoff, and closed session state."

    if not is_last:
        gate_blocked = gate_result is not None and not gate_result.passed
        if not gate_blocked:
            state.mark_step_complete(step)
        save_state(state, sp)
        if step == 6 and state.custom.get("fix_complexity") == "complex":
            run_summary = "Complexity gate triggered; diagnose prepared handoff path for planning flow."
        if step == 6 and state.custom.get("fix_complexity") == "large":
            run_summary = "Large-complexity gate triggered; diagnose prepared handoff path for develop → plan."

    # Build next command
    gate_confirm = False
    if is_last:
        next_cmd = None
    else:
        extra = {}
        if state.custom.get("autonomy_mode"):
            extra["mode"] = state.custom["autonomy_mode"]
        next_step_override = (
            gate_result.next_step_override
            if gate_result and not gate_result.passed
            else None
        )
        if next_step_override is not None:
            next_cmd = build_next_command(
                SCRIPT_DIR / "orchestrate.py",
                step,
                MAX_STEP,
                next_step=next_step_override,
                **extra,
            )
            gate_confirm = gate_result.require_confirmation
        else:
            next_cmd = build_next_command(
                SCRIPT_DIR / "orchestrate.py", step, MAX_STEP, **extra
            )

    phase_name = PHASE_NAMES.get(step, f"Step {step}")
    output = format_step_output(
        SKILL_NAME, step, MAX_STEP, phase_name, body,
        next_cmd=next_cmd,
        phase_todos=PHASE_TODOS.get(step, []),
        cross_skill_next=cross_skill_next,
        handoff_menu=handoff_menu,
        all_phase_names=PHASE_NAMES,
        all_phase_todos=PHASE_TODOS,
        require_confirmation=gate_confirm if gate_confirm else None,
    )

    # Append dashboard on final step
    if is_last:
        output += "\n\n" + render_dashboard(state)

    append_skill_run_memory(
        SKILL_NAME,
        step,
        phase_name,
        run_summary,
        state=state,
        state_path=sp,
        handoff_path=handoff_path,
    )
    print(output)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = build_base_parser(SKILL_NAME, MAX_STEP)
    parser.add_argument(
        "--mode", type=str, default=None,
        choices=["guided", "autonomous", "interactive"],
        help="Autonomy mode (default: guided)"
    )

    args = parser.parse_args()
    if validate_step_or_complete(args.step, MAX_STEP, SKILL_NAME):
        return

    if args.step == 1:
        handle_step_1(args)
    else:
        handle_step_n(args.step, state_file=args.state, mode=args.mode)


if __name__ == "__main__":
    main()
