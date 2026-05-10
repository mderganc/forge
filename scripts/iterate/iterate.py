#!/usr/bin/env python3
"""Iterate meta-workflow orchestrator.

Chains diagnose → plan → evaluate (pre) → implement → evaluate (post) → code-review → test,
with inner loops for evaluate/code-review until findings are clean, and outer loops until
target metric is met or max outer loops reached.

Gate files live under runtime memory `.iterate-gates/` as JSON sidecars the agent fills
after each child workflow step.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.shared.orchestrator import (
    SkillState,
    append_skill_run_memory,
    build_base_parser,
    build_next_command,
    build_skill_handoff_menu,
    clear_state_file,
    load_state,
    now_iso,
    runtime_memory_dir,
    runtime_state_path,
    save_state,
    validate_step_or_complete,
)

SKILL_NAME = "iterate"
MAX_STEP = 9
DEFAULT_MAX_INNER = 50

GATE_SUBDIR = ".iterate-gates"


@dataclass
class TargetSpec:
    metric_name: str
    operator: str
    target_value: float | str
    unit: str | None
    source: str
    measurement_step: str
    confidence: str


def gates_dir(search_dir: Path | None = None) -> Path:
    return runtime_memory_dir(search_dir) / GATE_SUBDIR


def _gate_path(name: str, search_dir: Path | None = None) -> Path:
    return gates_dir(search_dir) / f"{name}.json"


def parse_target_spec(raw: str) -> tuple[TargetSpec | None, str]:
    """Parse a human target string into TargetSpec; second return is confidence."""
    text = (raw or "").strip()
    if not text:
        return None, "low"

    if re.search(r"\b(judge|score|metric|pipeline)\b", text, re.I) and not re.search(r"\d", text):
        return TargetSpec(
            metric_name="unspecified_metric",
            operator="gte",
            target_value=0,
            unit=None,
            source="manual_clarification",
            measurement_step="post_test",
            confidence="low",
        ), "low"

    op = "gte"
    m = re.search(r"(>=|<=|==|!=|>|<)\s*([\d.]+%?|[\w.-]+)", text, re.I)
    num_val: float | str = 0.9
    if m:
        op_sym = m.group(1)
        val_raw = m.group(2).strip()
        op_map = {">": "gt", "<": "lt", ">=": "gte", "<=": "lte", "==": "eq", "!=": "neq"}
        op = op_map.get(op_sym, "gte")
        if val_raw.endswith("%"):
            v = float(val_raw[:-1])
            num_val = v / 100.0 if v > 1 else v
        else:
            try:
                num_val = float(val_raw)
            except ValueError:
                num_val = val_raw
    else:
        pct = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if pct:
            v = float(pct.group(1))
            num_val = v / 100.0 if v > 1 else v
        elif re.search(r"\d", text):
            num_val = float(re.findall(r"[\d.]+", text)[0])
        else:
            return (
                TargetSpec(
                    metric_name="custom_target",
                    operator="eq",
                    target_value=text,
                    unit=None,
                    source="manual_clarification",
                    measurement_step="post_test",
                    confidence="low",
                ),
                "low",
            )

    metric_name = "score"
    if "accuracy" in text.lower():
        metric_name = "accuracy"
    elif "f1" in text.lower():
        metric_name = "f1"
    elif "latency" in text.lower():
        metric_name = "latency"

    conf = "high" if m or isinstance(num_val, float) else "medium"
    spec = TargetSpec(
        metric_name=metric_name,
        operator=op,
        target_value=num_val,
        unit=None,
        source="project_harness",
        measurement_step="post_test",
        confidence=conf,
    )
    return spec, conf


def parse_natural_iterate(text: str) -> tuple[str | None, str | None, int | None, str]:
    """Extract goal, target phrase, max_loops from free text."""
    t = text.strip()
    if not t:
        return None, None, None, "low"

    max_loops: int | None = None
    ml = re.search(r"max\s+loops?\s*:?\s*(\d+)", t, re.I)
    if ml:
        max_loops = int(ml.group(1))

    goal = t
    target_phrase = None
    until = re.split(r"\buntil\b", t, maxsplit=1, flags=re.I)
    if len(until) == 2:
        goal = until[0].strip().strip(",").strip()
        rest = until[1].strip()
        rest_no_ml = re.sub(r",?\s*max\s+loops?\s*:?\s*\d+", "", rest, flags=re.I).strip()
        target_phrase = rest_no_ml.strip().strip(",").strip() or None

    conf = "high" if max_loops is not None and bool(goal and len(goal) > 3) else "medium"
    return goal or None, target_phrase, max_loops, conf


def target_spec_to_dict(spec: TargetSpec | None) -> dict[str, Any] | None:
    if spec is None:
        return None
    return {
        "metric_name": spec.metric_name,
        "operator": spec.operator,
        "target_value": spec.target_value,
        "unit": spec.unit,
        "source": spec.source,
        "measurement_step": spec.measurement_step,
        "confidence": spec.confidence,
    }


def _read_gate(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _stage_result(
    loop_index: int,
    stage: str,
    status: str,
    *,
    open_total: int = 0,
    open_crit: int = 0,
    target_value: Any = None,
    target_met: bool = False,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "loop_index": loop_index,
        "stage": stage,
        "status": status,
        "open_findings_total": open_total,
        "open_findings_critical": open_crit,
        "target_value": target_value,
        "target_met": target_met,
        "evidence_refs": evidence_refs or [],
        "timestamp": now_iso(),
    }


def _append_stage(custom: dict[str, Any], result: dict[str, Any]) -> None:
    hist = custom.setdefault("stage_results", [])
    hist.append(result)
    if len(hist) > 500:
        custom["stage_results"] = hist[-400:]


def _record_inner_loop_cap(
    custom: dict[str, Any],
    outer: int,
    stage_key: str,
    gate: dict[str, Any] | None,
) -> None:
    ot = int(gate.get("open_findings_total", 1)) if gate else 1
    _append_stage(custom, _stage_result(outer, stage_key, "fail", open_total=ot))


def _dict_to_spec(d: dict[str, Any] | None) -> TargetSpec | None:
    if not d:
        return None
    return TargetSpec(
        metric_name=str(d.get("metric_name", "metric")),
        operator=str(d.get("operator", "gte")),
        target_value=d.get("target_value", 0),
        unit=d.get("unit"),
        source=str(d.get("source", "project_harness")),
        measurement_step=str(d.get("measurement_step", "post_test")),
        confidence=str(d.get("confidence", "medium")),
    )


def _target_satisfied(spec: TargetSpec | None, metric_gate: dict[str, Any] | None) -> bool:
    if not metric_gate:
        return False
    if metric_gate.get("status") == "needs_clarification":
        return False
    met = metric_gate.get("target_met")
    if isinstance(met, bool):
        return met
    if spec is None:
        return False
    tv = metric_gate.get("measured_value", metric_gate.get("target_value"))
    if tv is None:
        return False
    tgt = spec.target_value
    if not isinstance(tgt, (int, float)):
        return str(tv) == str(tgt)
    try:
        cur = float(tv)
        tgt_f = float(tgt)
        op = spec.operator
        if op == "gt":
            return cur > tgt_f
        if op == "gte":
            return cur >= tgt_f
        if op == "lt":
            return cur < tgt_f
        if op == "lte":
            return cur <= tgt_f
        if op == "eq":
            return abs(cur - tgt_f) < 1e-9
        if op == "neq":
            return abs(cur - tgt_f) >= 1e-9
    except (TypeError, ValueError):
        return False
    return False


def _init_state() -> SkillState:
    st = SkillState(skill_name=SKILL_NAME, max_step=MAX_STEP)
    st.started_at = now_iso()
    st.custom = {
        "goal": "",
        "target_raw": "",
        "target_spec": None,
        "max_loops": 3,
        "max_inner": DEFAULT_MAX_INNER,
        "current_outer_loop": 0,
        "inner_eval_pre": 0,
        "inner_eval_post": 0,
        "inner_cr": 0,
        "metric_harness_pending": False,
        "stage_results": [],
        "target_met_flag": False,
    }
    return st


def _format_out(title: str, body: str, next_cmd: str | None) -> str:
    bar = "=" * len(title)
    out = f"{title}\n{bar}\n\n{body}"
    if next_cmd:
        out += "\n\n---\n**Continuation token (for tooling):** next step is indicated by your forge launcher."
    return out


def _gate_snapshot(gd: Path) -> dict[str, Any]:
    """Full JSON gate contents for terminal audit artifacts."""
    out: dict[str, Any] = {}
    if not gd.is_dir():
        return out
    for p in sorted(gd.glob("*.json")):
        try:
            out[p.name] = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            out[p.name] = {"_error": str(e)}
    return out


def _write_iterate_terminal_artifacts(
    state: SkillState,
    sp: Path,
    gd: Path,
    outcome: str,
    *,
    target_met: bool,
) -> None:
    """Write JSON + markdown summary under runtime memory (auditable completion bundle)."""
    mem = runtime_memory_dir()
    mem.mkdir(parents=True, exist_ok=True)
    snap = _gate_snapshot(gd)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "outcome": outcome,
        "goal": state.custom.get("goal"),
        "target_raw": state.custom.get("target_raw"),
        "target_spec": state.custom.get("target_spec"),
        "max_outer_loops": state.custom.get("max_loops"),
        "outer_loop_index": state.custom.get("current_outer_loop"),
        "target_met": target_met,
        "metric_harness_pending": state.custom.get("metric_harness_pending"),
        "clarification_needed": state.custom.get("clarification_needed"),
        "stage_results": state.custom.get("stage_results", []),
        "gate_snapshot": snap,
        "iterate_state_path": str(sp),
        "completed_at": now_iso(),
    }
    (mem / "iterate-terminal-report.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Iterate run summary",
        "",
        f"- **Outcome:** {outcome}",
        f"- **Goal:** {state.custom.get('goal', '')}",
        f"- **Target met:** {target_met}",
        f"- **Outer loop (0-based):** {state.custom.get('current_outer_loop', 0)}",
        f"- **Max outer loops:** {state.custom.get('max_loops', '')}",
        "",
        "Gate files and open findings are captured in `iterate-terminal-report.json` under Forge runtime memory.",
        "",
    ]
    (mem / "iterate-summary.md").write_text("\n".join(lines), encoding="utf-8")


def handle_step_1(args: argparse.Namespace, sp: Path) -> None:
    gates_dir().mkdir(parents=True, exist_ok=True)

    state = _init_state()
    goal = (getattr(args, "goal", None) or "").strip()
    target_raw = (getattr(args, "target", None) or "").strip()
    max_loops = getattr(args, "max_loops", None)

    extra = (getattr(args, "text", None) or getattr(args, "natural_text", None) or "")
    nl_conf = "high"
    if isinstance(extra, str) and extra.strip():
        ng, nt, nl, nl_conf = parse_natural_iterate(extra)
        if not goal and ng:
            goal = ng
        if not target_raw and nt:
            target_raw = nt
        if max_loops is None and nl is not None:
            max_loops = nl

    if max_loops is None or max_loops < 1:
        max_loops = 3

    state.custom["goal"] = goal
    state.custom["target_raw"] = target_raw
    state.custom["max_loops"] = int(max_loops)
    state.custom["nl_parse_confidence"] = nl_conf
    if getattr(args, "metric_command", None):
        state.custom["metric_command"] = str(args.metric_command)
    if getattr(args, "harness", None):
        state.custom["harness_hint"] = str(args.harness)

    spec, conf = parse_target_spec(target_raw)
    state.custom["target_spec"] = target_spec_to_dict(spec)

    clarification = False
    if spec and spec.confidence == "low":
        clarification = True
    if not goal:
        clarification = True
    if isinstance(extra, str) and extra.strip() and nl_conf in ("medium", "low"):
        clarification = True

    body_parts = [
        "## Iterate — session initialized",
        "",
        f"**Goal:** {goal or '(not set — provide goal via flags or natural language)'}",
        f"**Target:** {target_raw or '(not set)'}",
        f"**Max outer loops:** {max_loops}",
        "",
        "### Gate directory",
        f"Create JSON gate files under `{GATE_SUBDIR}/` in Forge runtime memory (next to handoffs).",
        "",
        "### Next",
        "Run the **diagnose** workflow through completion. Then write gate file `diagnose.json`:",
        "```json",
        '{"status":"pass","open_findings_total":0,"open_findings_critical":0,"evidence_refs":[]}',
        "```",
        "",
        "Continue iterate at **step 2**.",
    ]
    if clarification:
        body_parts.extend([
            "",
            "### Clarification needed",
            "Confirm measurable target (name, threshold) and verification harness.",
        ])
        if isinstance(extra, str) and extra.strip() and nl_conf in ("medium", "low"):
            body_parts.append(
                f"Natural-language parsing confidence is **{nl_conf}** — confirm goal, target, and max loops explicitly "
                "or restate using `--goal`, `--target`, and `--max-loops`."
            )
        state.custom["clarification_needed"] = True
    else:
        state.custom["clarification_needed"] = False

    state.current_step = 1
    state.mark_step_complete(1)
    save_state(state, sp)

    append_skill_run_memory(
        SKILL_NAME,
        1,
        "Initialize",
        "Initialized iterate session.",
        state=state,
        state_path=sp,
    )

    next_cmd = build_next_command(SCRIPT_DIR / "iterate.py", 1, MAX_STEP)
    title = f"{SKILL_NAME.upper()} — Initialize (Step 1 of {MAX_STEP})"
    print(_format_out(title, "\n".join(body_parts), next_cmd))


def handle_step_n(step: int, sp: Path, _args: argparse.Namespace) -> None:
    state = load_state(sp)
    gd = gates_dir()
    gd.mkdir(parents=True, exist_ok=True)

    goal = str(state.custom.get("goal", ""))
    max_outer = int(state.custom.get("max_loops", 3))
    outer = int(state.custom.get("current_outer_loop", 0))
    max_inner = int(state.custom.get("max_inner", DEFAULT_MAX_INNER))
    spec = _dict_to_spec(state.custom.get("target_spec"))

    body = ""
    next_cmd = build_next_command(SCRIPT_DIR / "iterate.py", step, MAX_STEP) if step < MAX_STEP else ""

    def _save() -> None:
        state.current_step = step
        save_state(state, sp)

    def _log(summary: str) -> None:
        append_skill_run_memory(SKILL_NAME, step, f"Step {step}", summary, state=state, state_path=sp)

    if step == 2:
        g = _read_gate(gd / "diagnose.json")
        if not g or int(g.get("open_findings_total", 1)) > 0:
            body = (
                "## Diagnose\n\nComplete **diagnose**. Write `diagnose.json` with "
                "`open_findings_total` (0 when done). Re-run **step 2** until clean."
            )
            _save()
            _log("Await diagnose gate")
        else:
            _append_stage(state.custom, _stage_result(outer, "diagnose", str(g.get("status", "pass")), open_total=int(g.get("open_findings_total", 0))))
            state.mark_step_complete(2)
            body = "## Diagnose complete\n\nRun **step 3** for plan."
            _save()
            _log("Diagnose gate pass")

    elif step == 3:
        g = _read_gate(gd / "plan.json")
        if not g:
            body = "## Plan\n\nComplete **plan** workflow. Write `plan.json` with `status` and `evidence_refs`."
            _save()
            _log("Await plan gate")
        else:
            _append_stage(state.custom, _stage_result(outer, "plan", "pass", evidence_refs=list(g.get("evidence_refs") or [])))
            state.mark_step_complete(3)
            body = "## Plan recorded\n\nRun **step 4** for evaluate (pre)."
            _save()
            _log("Plan gate pass")

    elif step == 4:
        g = _read_gate(gd / "evaluate-pre.json")
        inner = int(state.custom.get("inner_eval_pre", 0))
        if not g or int(g.get("open_findings_total", 1)) > 0:
            inner += 1
            state.custom["inner_eval_pre"] = inner
            if inner > max_inner:
                _record_inner_loop_cap(state.custom, outer, "evaluate_pre", g)
                body = f"## Evaluate (pre) — stopped at inner cap ({max_inner})"
                state.mark_step_complete(4)
            else:
                body = (
                    "## Evaluate (pre)\n\nRun **evaluate** pre mode until clean. "
                    "Write `evaluate-pre.json` with `open_findings_total: 0`.\n\n"
                    f"Attempt {inner}/{max_inner}. Re-run **step 4**."
                )
            _save()
            _log("Evaluate pre gate pending or capped")
        else:
            _append_stage(state.custom, _stage_result(outer, "evaluate_pre", "pass", open_total=0))
            state.mark_step_complete(4)
            body = "## Evaluate (pre) clean\n\nRun **step 5** for implement."
            state.custom["inner_eval_pre"] = 0
            _save()
            _log("Evaluate pre clean")

    elif step == 5:
        g = _read_gate(gd / "implement.json")
        if not g:
            body = "## Implement\n\nComplete **implement**. Write `implement.json`."
            _save()
            _log("Await implement gate")
        else:
            _append_stage(state.custom, _stage_result(outer, "implement", "pass"))
            state.mark_step_complete(5)
            body = "## Implement recorded\n\nRun **step 6** for evaluate (post)."
            _save()
            _log("Implement gate pass")

    elif step == 6:
        g = _read_gate(gd / "evaluate-post.json")
        inner = int(state.custom.get("inner_eval_post", 0))
        if not g or int(g.get("open_findings_total", 1)) > 0:
            inner += 1
            state.custom["inner_eval_post"] = inner
            if inner > max_inner:
                _record_inner_loop_cap(state.custom, outer, "evaluate_post", g)
                body = "## Evaluate (post) — inner cap"
                state.mark_step_complete(6)
            else:
                body = (
                    "## Evaluate (post)\n\nRun **evaluate** post mode. Write `evaluate-post.json`.\n\n"
                    f"Attempt {inner}/{max_inner}."
                )
            _save()
            _log("Evaluate post pending")
        else:
            _append_stage(state.custom, _stage_result(outer, "evaluate_post", "pass", open_total=0))
            state.mark_step_complete(6)
            body = "## Evaluate (post) clean\n\nRun **step 7** for code-review."
            state.custom["inner_eval_post"] = 0
            _save()
            _log("Evaluate post clean")

    elif step == 7:
        g = _read_gate(gd / "code-review.json")
        inner = int(state.custom.get("inner_cr", 0))
        if not g or int(g.get("open_findings_total", 1)) > 0:
            inner += 1
            state.custom["inner_cr"] = inner
            if inner > max_inner:
                _record_inner_loop_cap(state.custom, outer, "code_review", g)
                body = "## Code review — inner cap"
                state.mark_step_complete(7)
            else:
                body = (
                    "## Code review\n\nRun **code-review**. Write `code-review.json`.\n\n"
                    f"Attempt {inner}/{max_inner}."
                )
            _save()
            _log("CR pending")
        else:
            _append_stage(state.custom, _stage_result(outer, "code_review", "pass", open_total=0))
            state.mark_step_complete(7)
            body = "## Code review clean\n\nRun **step 8** for tests + metric."
            state.custom["inner_cr"] = 0
            _save()
            _log("CR clean")

    elif step == 8:
        tg = _read_gate(gd / "test.json")
        mg = _read_gate(gd / "metric.json")
        if not tg:
            body = "## Test\n\nRun **test** (run mode). Write `test.json` with `failed` count."
            _save()
            _log("Await test gate")
        elif int(tg.get("failed", 1)) != 0:
            body = "## Tests failing\n\nFix tests; update `test.json`."
            _save()
            _log("Tests failed")
        elif not mg:
            body = "## Metric\n\nWrite `metric.json` with `measured_value`, `target_met`, or `status: needs_clarification`."
            state.custom["metric_harness_pending"] = True
            _save()
            _log("Await metric")
        elif mg.get("status") == "needs_clarification":
            _append_stage(state.custom, _stage_result(outer, "test", "needs_clarification"))
            body = "## Metric / harness clarification\n\nExtend plan or harness; then restart from plan step."
            _save()
            _log("Metric clarification")
        else:
            target_met = _target_satisfied(spec, mg)
            state.custom["target_met_flag"] = target_met
            _append_stage(
                state.custom,
                _stage_result(
                    outer,
                    "test",
                    "pass",
                    target_value=mg.get("measured_value"),
                    target_met=target_met,
                    evidence_refs=[str(_gate_path("metric"))],
                ),
            )
            state.mark_step_complete(8)
            body = "## Test + metric recorded\n\nRun **step 9** to finalize or continue outer loop."
            _save()
            _log("Test stage pass")

    elif step == 9:
        mg = _read_gate(gd / "metric.json")
        target_met = bool(state.custom.get("target_met_flag")) or _target_satisfied(spec, mg or {})

        parts = [
            "## Iterate — report",
            "",
            f"**Goal:** {goal}",
            f"**Outer loop:** {outer + 1} / {max_outer}",
            f"**Target met:** {target_met}",
            "",
        ]

        if target_met:
            parts.append("### Outcome\nTarget satisfied.")
            state.completed_at = now_iso()
            _log("Complete target met")
            _write_iterate_terminal_artifacts(state, sp, gd, "target_met", target_met=True)
            append_skill_run_memory(SKILL_NAME, 9, "Complete", "Target met.", state=state, state_path=sp)
            clear_state_file(sp)
            menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
            print(_format_out(f"{SKILL_NAME.upper()} — Complete", "\n".join(parts) + "\n\n" + menu, None))
            return

        if outer + 1 >= max_outer:
            parts.append("### Outcome\nMax outer loops reached without meeting target.")
            state.completed_at = now_iso()
            _log("Complete max loops")
            _write_iterate_terminal_artifacts(state, sp, gd, "max_outer_loops", target_met=False)
            append_skill_run_memory(SKILL_NAME, 9, "Complete", "Max loops.", state=state, state_path=sp)
            clear_state_file(sp)
            menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
            print(_format_out(f"{SKILL_NAME.upper()} — Complete", "\n".join(parts) + "\n\n" + menu, None))
            return

        # Outer loop continues
        state.custom["current_outer_loop"] = outer + 1
        state.custom["inner_eval_pre"] = 0
        state.custom["inner_eval_post"] = 0
        state.custom["inner_cr"] = 0
        state.custom["target_met_flag"] = False
        state.current_step = 2
        state.last_completed_step = 1
        save_state(state, sp)
        parts.append("### Next\nOuter loop continues — proceed from **step 2** (diagnose).")
        _log("Outer loop advance")
        next_cmd = build_next_command(SCRIPT_DIR / "iterate.py", 8, MAX_STEP, next_step=2)
        print(_format_out(f"{SKILL_NAME.upper()} — Step 9", "\n".join(parts), next_cmd))
        return

    else:
        body = f"Unknown step {step}"
        _save()
        _log("Unknown")

    if step != 9:
        print(_format_out(f"{SKILL_NAME.upper()} — Step {step} of {MAX_STEP}", body, next_cmd))


def main() -> None:
    parser = build_base_parser(SKILL_NAME, MAX_STEP)
    parser.add_argument("--goal", type=str, default=None)
    parser.add_argument("--target", type=str, default=None)
    parser.add_argument("--max-loops", type=int, dest="max_loops", default=None)
    parser.add_argument("--metric-command", type=str, default=None)
    parser.add_argument("--harness", type=str, default=None)
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help='Natural language, e.g. "improve X until score > 0.9, max loops 10"',
    )
    args = parser.parse_args()
    args.natural_text = ""

    if validate_step_or_complete(args.step, MAX_STEP, SKILL_NAME):
        return

    sp = runtime_state_path(SKILL_NAME)
    if args.step == 1:
        handle_step_1(args, sp)
        return

    if not sp.exists():
        print("ERROR: No iterate session. Run step 1 first.", file=sys.stderr)
        sys.exit(1)

    handle_step_n(args.step, sp, args)


if __name__ == "__main__":
    main()
