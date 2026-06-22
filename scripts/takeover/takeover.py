#!/usr/bin/env python3
"""Takeover meta-workflow — infer epic, route, drive skills until ship-ready."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.shared.orchestrator import (
    SkillState,
    append_skill_run_memory,
    apply_resolved_workflow_step,
    build_base_parser,
    build_next_command,
    build_skill_handoff_menu,
    clear_state_file,
    load_state,
    now_iso,
    resolve_step1_state_path,
    runtime_memory_dir,
    save_state,
    validate_step_or_complete,
)
from scripts.shared.skill_phases import agent_skill_token, infer_resume_step
from scripts.shared.workflow_step import run_workflow_step
from scripts.takeover.cleanup import run_cleanup
from scripts.takeover.deviations import (
    empty_deviations,
    record_assumption,
    record_inference,
    write_deviations,
    write_summary,
)
from scripts.takeover.router import RoutePlan, build_route_plan

SKILL_NAME = "takeover"
MAX_STEP = 6
DEFAULT_MAX_INNER = 50
GATE_SUBDIR = ".takeover-gates"

TAKEOVER_PHASE_NAMES = {
    1: "Initialize + route",
    2: "Upstream / continue",
    3: "Plan + evaluate (pre)",
    4: "Implement + evaluate (post)",
    5: "Code review + test",
    6: "Report",
}

TAKEOVER_PHASE_TODOS = {
    1: [
        {"content": "Infer epic and write route plan", "activeForm": "Routing", "status": "pending"},
        {"content": "Initialize takeover gate directory", "activeForm": "Initializing gates", "status": "pending"},
    ],
}


def gates_dir(search_dir: Path | None = None) -> Path:
    return runtime_memory_dir(search_dir) / GATE_SUBDIR


def _gate_path(name: str, search_dir: Path | None = None) -> Path:
    return gates_dir(search_dir) / f"{name}.json"


def _read_gate(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _metric_gate_open(
    gd: Path,
    gate_file: str,
    metric_key: str,
    *,
    missing_is_open: bool = True,
    fail_above: int = 0,
) -> bool:
    """True when the gate file is absent or the metric is still above the pass threshold."""
    gate = _read_gate(gd / gate_file)
    if not gate:
        return missing_is_open
    return int(gate.get(metric_key, fail_above + 1)) > fail_above


def _metric_gate_not_equal(
    gd: Path,
    gate_file: str,
    metric_key: str,
    required: int,
) -> bool:
    """True when the gate is missing or the metric does not equal ``required``."""
    gate = _read_gate(gd / gate_file)
    if not gate:
        return True
    return int(gate.get(metric_key, required + 1)) != required


def _handle_primary_then_metric_stage(
    gd: Path,
    state: SkillState,
    *,
    primary_gate: str,
    primary_body: str,
    secondary_gate: str,
    metric_key: str,
    inner_key: str,
    inner: int,
    max_inner: int,
    cap_body: str,
    pending_body: str,
    pass_body: str,
    complete_step: int,
    await_primary_log: str,
    pending_log: str,
    pass_log: str,
) -> tuple[str, str]:
    if not _read_gate(gd / primary_gate):
        return primary_body, await_primary_log

    if _metric_gate_open(gd, secondary_gate, metric_key):
        inner += 1
        state.custom[inner_key] = inner
        if inner > max_inner:
            state.mark_step_complete(complete_step)
            return cap_body, pending_log
        return pending_body, pending_log

    state.mark_step_complete(complete_step)
    state.custom[inner_key] = 0
    return pass_body, pass_log


def _init_state() -> SkillState:
    st = SkillState(skill_name=SKILL_NAME, max_step=MAX_STEP)
    st.started_at = now_iso()
    st.custom = {
        "goal": "ship-ready",
        "route_plan": None,
        "deviations": empty_deviations(),
        "max_inner": DEFAULT_MAX_INNER,
        "inner_eval_pre": 0,
        "inner_eval_post": 0,
        "inner_cr": 0,
        "ship_ready": False,
    }
    return st


def _route_plan_from_custom(custom: dict[str, Any]) -> RoutePlan | None:
    raw = custom.get("route_plan")
    if not raw:
        return None
    return RoutePlan(
        entry_skill=raw.get("entry_skill", "plan"),
        entry_reason=raw.get("entry_reason", ""),
        upstream_skills=list(raw.get("upstream_skills") or []),
        active_session_id=raw.get("active_session_id"),
        active_session_path=raw.get("active_session_path"),
        design_path=raw.get("design_path"),
        issue_ref=raw.get("issue_ref"),
        goal=raw.get("goal", "ship-ready"),
    )


def _route_plan_to_dict(plan: RoutePlan) -> dict[str, Any]:
    return {
        "entry_skill": plan.entry_skill,
        "entry_reason": plan.entry_reason,
        "upstream_skills": plan.upstream_skills,
        "active_session_id": plan.active_session_id,
        "active_session_path": plan.active_session_path,
        "design_path": plan.design_path,
        "issue_ref": plan.issue_ref,
        "goal": plan.goal,
    }


def _child_resume_command(skill: str, session_path: str | None, session_id: str | None) -> str:
    import os

    from scripts.shared.skill_phases import phase_for_step, variant_from_session

    if not session_path and not session_id:
        return f"forge {agent_skill_token(skill)} --step 1"

    sp = Path(session_path) if session_path else None
    step = 1
    variant = None
    if sp and sp.exists():
        try:
            child = load_state(sp)
            step = infer_resume_step(child)
            variant = variant_from_session(
                {
                    "skill": child.skill_name,
                    "custom": child.custom,
                    "current_step": child.current_step,
                    "last_completed_step": child.last_completed_step,
                    "max_step": child.max_step,
                },
                child.skill_name,
            )
        except Exception:
            step = 1
    phase = phase_for_step(skill, step, variant=variant)
    extra = ""
    if skill == "evaluate" and variant:
        extra = f" --mode {variant}"
    elif skill == "test" and variant and variant != "run":
        extra = f" --mode {variant}"
    if os.environ.get("FORGE_USE_LAUNCHER") == "1":
        if session_id:
            return f"forge {agent_skill_token(skill)} --phase {phase}{extra} --session {session_id}"
        if session_path:
            return f"forge {agent_skill_token(skill)} --phase {phase}{extra} --state '{session_path}'"
    base = f"forge {agent_skill_token(skill)} --phase {phase}{extra}"
    if session_id:
        return f"{base} --session {session_id}"
    if session_path:
        return f"{base} --state '{session_path}'"
    return base


def handle_step_1(args: argparse.Namespace, sp: Path) -> None:
    from scripts.shared.orchestrator import _detect_repo_root

    if getattr(args, "cleanup", False):
        run_cleanup(force=getattr(args, "force", False), all_stale=getattr(args, "all_stale", False))
        return

    gates_dir().mkdir(parents=True, exist_ok=True)
    state = load_state(sp) if sp.exists() else _init_state()

    goal = (getattr(args, "goal", None) or "").strip() or "ship-ready"
    plan, inferences = build_route_plan(
        repo_root=_detect_repo_root(),
        issue=getattr(args, "issue", None),
        design=getattr(args, "design", None),
        goal=goal,
    )

    dev = state.custom.setdefault("deviations", empty_deviations())
    for inf in inferences:
        record_inference(dev, inf["field"], inf["chosen"], inf["reason"])
    record_assumption(dev, f"Default goal: {goal}")

    state.custom["goal"] = plan.goal
    state.custom["route_plan"] = _route_plan_to_dict(plan)
    state.current_step = 1
    state.mark_step_complete(1)
    save_state(state, sp)

    append_skill_run_memory(
        SKILL_NAME, 1, "Initialize + route", f"Entry: {plan.entry_skill} ({plan.entry_reason})", state=state, state_path=sp
    )

    body_parts = [
        "# Takeover — routed",
        "",
        f"**Goal:** {plan.goal}",
        f"**Entry skill:** `{plan.entry_skill}` — {plan.entry_reason}",
    ]
    if plan.upstream_skills:
        body_parts.append(f"**Upstream:** {', '.join(plan.upstream_skills)}")
    if plan.design_path:
        body_parts.append(f"**Design:** `{plan.design_path}`")
    if plan.issue_ref:
        body_parts.append(f"**Issue:** `{plan.issue_ref}`")
    body_parts.extend(
        [
            "",
            "Run the child skill commands emitted on subsequent steps until ship-ready gates pass.",
            f"Gate directory: `{GATE_SUBDIR}/`",
        ]
    )

    next_cmd = build_next_command(SCRIPT_DIR / "takeover.py", 1, MAX_STEP)
    print(
        run_workflow_step(
            SKILL_NAME,
            1,
            MAX_STEP,
            TAKEOVER_PHASE_NAMES[1],
            "\n".join(body_parts),
            next_cmd=next_cmd,
            all_phase_names=TAKEOVER_PHASE_NAMES,
            all_phase_todos=TAKEOVER_PHASE_TODOS,
            title=f"{SKILL_NAME.upper()} — Initialize + route (Step 1 of {MAX_STEP})",
        )
    )


def handle_step_n(step: int, sp: Path, _args: argparse.Namespace) -> None:
    state = load_state(sp)
    gd = gates_dir()
    gd.mkdir(parents=True, exist_ok=True)
    plan = _route_plan_from_custom(state.custom)
    max_inner = int(state.custom.get("max_inner", DEFAULT_MAX_INNER))
    goal = str(state.custom.get("goal", "ship-ready"))
    dev = state.custom.setdefault("deviations", empty_deviations())

    body = ""
    next_cmd = build_next_command(SCRIPT_DIR / "takeover.py", step, MAX_STEP) if step < MAX_STEP else ""

    def _save() -> None:
        state.current_step = step
        save_state(state, sp)

    def _log(summary: str) -> None:
        append_skill_run_memory(SKILL_NAME, step, TAKEOVER_PHASE_NAMES.get(step, f"Step {step}"), summary, state=state, state_path=sp)

    if step == 2:
        if plan and plan.active_session_path:
            cmd = _child_resume_command(plan.entry_skill, plan.active_session_path, plan.active_session_id)
            body = (
                f"## Continue active session\n\nRun:\n\n`{cmd}`\n\n"
                "When the child skill completes its handoff, write `upstream.json` with "
                '`{"status": "pass"}` and re-run **step 2**.'
            )
            _save()
            _log("Continue active child session")
        elif plan and plan.upstream_skills:
            g = _read_gate(gd / "upstream.json")
            if not g or g.get("status") != "pass":
                skills = ", ".join(plan.upstream_skills)
                body = (
                    f"## Upstream ({skills})\n\n"
                    f"Complete upstream skills: **{skills}**. "
                    "Write `upstream.json` with `status: pass` when intent/design is ready."
                )
                _save()
                _log("Await upstream gate")
            else:
                state.mark_step_complete(2)
                body = "## Upstream complete\n\nProceed to **step 3** (plan)."
                _save()
                _log("Upstream gate pass")
        else:
            state.mark_step_complete(2)
            body = "## Upstream skipped\n\nRun **step 3** for plan + evaluate (pre)."
            _save()
            _log("Upstream skipped")

    elif step == 3:
        body, log_msg = _handle_primary_then_metric_stage(
            gd,
            state,
            primary_gate="plan.json",
            primary_body="## Plan\n\nComplete **plan**. Write `plan.json` with `status: pass`.",
            secondary_gate="evaluate-pre.json",
            metric_key="open_findings_total",
            inner_key="inner_eval_pre",
            inner=int(state.custom.get("inner_eval_pre", 0)),
            max_inner=max_inner,
            cap_body=f"## Evaluate (pre) — inner cap ({max_inner})",
            pending_body=(
                "## Evaluate (pre)\n\nRun **evaluate** pre mode. "
                "Write `evaluate-pre.json` with `open_findings_total: 0`."
            ),
            pass_body="## Plan + evaluate (pre) clean\n\nRun **step 4** for implement.",
            complete_step=3,
            await_primary_log="Await plan gate",
            pending_log="Evaluate pre pending",
            pass_log="Plan + eval pre pass",
        )
        _save()
        _log(log_msg)

    elif step == 4:
        body, log_msg = _handle_primary_then_metric_stage(
            gd,
            state,
            primary_gate="implement.json",
            primary_body="## Implement\n\nComplete **implement**. Write `implement.json` with `status: pass`.",
            secondary_gate="evaluate-post.json",
            metric_key="open_findings_total",
            inner_key="inner_eval_post",
            inner=int(state.custom.get("inner_eval_post", 0)),
            max_inner=max_inner,
            cap_body="## Evaluate (post) — inner cap",
            pending_body=(
                "## Evaluate (post)\n\nRun **evaluate** post mode. "
                "Write `evaluate-post.json` with `open_findings_total: 0`."
            ),
            pass_body="## Implement + evaluate (post) clean\n\nRun **step 5**.",
            complete_step=4,
            await_primary_log="Await implement gate",
            pending_log="Evaluate post pending",
            pass_log="Implement stage pass",
        )
        _save()
        _log(log_msg)

    elif step == 5:
        inner = int(state.custom.get("inner_cr", 0))
        if _metric_gate_open(gd, "code-review.json", "open_findings_total"):
            inner += 1
            state.custom["inner_cr"] = inner
            if inner > max_inner:
                body = "## Code review — inner cap"
            else:
                body = (
                    "## Code review\n\nRun **code-review**. "
                    "Write `code-review.json` with `open_findings_total: 0`."
                )
            _save()
            _log("CR pending")
        elif _metric_gate_not_equal(gd, "test.json", "failed", 0):
            body = "## Test\n\nRun **test** (run mode). Write `test.json` with `failed: 0`."
            _save()
            _log("Await test gate")
        else:
            state.mark_step_complete(5)
            state.custom["ship_ready"] = True
            state.custom["inner_cr"] = 0
            body = "## Ship-ready gates passed\n\nRun **step 6** for report + handoff to ship."
            _save()
            _log("Ship-ready")

    elif step == 6:
        sidecar = sp.parent / "sidecars" / ".takeover-deviations.json"
        write_deviations(sidecar, dev)
        mem = runtime_memory_dir()
        write_summary(mem / "takeover-summary.md", dev, outcome="ship_ready", goal=goal)
        state.completed_at = now_iso()
        state.custom["ship_ready"] = True
        _log("Complete ship-ready")
        clear_state_file(sp)
        parts = [
            "## Takeover — complete",
            "",
            f"**Goal:** {goal}",
            "**Outcome:** ship-ready quality gates passed.",
            "",
            f"Deviations: `{sidecar}`",
            f"Summary: `{mem / 'takeover-summary.md'}`",
            "",
        ]
        menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
        print(
            run_workflow_step(
                SKILL_NAME,
                6,
                MAX_STEP,
                TAKEOVER_PHASE_NAMES[6],
                "\n".join(parts) + "\n\n" + menu,
                next_cmd=None,
                title=f"{SKILL_NAME.upper()} — Report (Step 6 of {MAX_STEP})",
            )
        )
        return

    else:
        body = f"Unknown step {step}"
        _save()

    print(
        run_workflow_step(
            SKILL_NAME,
            step,
            MAX_STEP,
            TAKEOVER_PHASE_NAMES.get(step, f"Step {step}"),
            body,
            next_cmd=next_cmd,
            all_phase_names=TAKEOVER_PHASE_NAMES,
            all_phase_todos=TAKEOVER_PHASE_TODOS,
            title=f"{SKILL_NAME.upper()} — Step {step} of {MAX_STEP}",
        )
    )


def main() -> None:
    parser = build_base_parser(SKILL_NAME, MAX_STEP)
    parser.add_argument("--issue", type=str, default=None, help="GitHub issue number or URL")
    parser.add_argument("--design", type=str, default=None, help="Path to design spec")
    parser.add_argument("--goal", type=str, default=None, help="Override default ship-ready goal")
    parser.add_argument("--cleanup", action="store_true", help="Legacy state file cleanup (dry-run)")
    parser.add_argument("--force", action="store_true", help="With --cleanup: delete files")
    parser.add_argument("--all-stale", action="store_true", dest="all_stale", help="Cleanup all state files")
    args = parser.parse_args()
    apply_resolved_workflow_step(args, SKILL_NAME, MAX_STEP)

    if getattr(args, "cleanup", False) and args.step == 1:
        run_cleanup(force=args.force, all_stale=args.all_stale)
        return

    if validate_step_or_complete(args.step, MAX_STEP, SKILL_NAME):
        return

    if args.step == 1:
        sp = resolve_step1_state_path(
            SKILL_NAME,
            args.state,
            parallel=getattr(args, "parallel", False),
            label=getattr(args, "label", None),
            session_id=getattr(args, "session", None),
        )
        handle_step_1(args, sp)
        return

    from scripts.shared.orchestrator import resolve_step_state_path

    sp = resolve_step_state_path(
        SKILL_NAME,
        args.step,
        state_file=args.state,
        session_id=getattr(args, "session", None),
    )
    if not sp.exists():
        print("ERROR: No takeover session. Run step 1 first.", file=sys.stderr)
        sys.exit(1)
    handle_step_n(args.step, sp, args)


if __name__ == "__main__":
    main()
