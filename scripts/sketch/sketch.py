#!/usr/bin/env python3
"""Sketch skill orchestrator — organize intent before develop.

Three steps: startup, sketch session (one question at a time), handoff.
Optional --with-domain-docs allows CONTEXT.md glossary and sparse ADRs.
Develop (not sketch) authors docs/forge/specs/*-design.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.evaluate.template_engine import load_template, render_template
from scripts.shared.orchestrator import (
    SkillState,
    append_skill_run_memory,
    build_base_parser,
    build_next_command,
    build_skill_handoff_menu,
    check_same_skill_clobber,
    clear_state_file,
    find_state_file,
    format_step_output,
    load_state,
    now_iso,
    print_remaining_session_warning,
    resolve_step1_state_path,
    run_step1_session_hygiene,
    runtime_memory_dir,
    runtime_state_path,
    save_state,
    validate_state_path,
    validate_step_or_complete,
    write_handoff,
)

SKILL_NAME = "sketch"
MAX_STEP = 3

PHASE_NAMES = {
    1: "Startup",
    2: "Sketch session",
    3: "Handoff",
}

PHASE_TODOS = {
    1: [
        {"content": "Confirm topic and domain-docs mode",
         "activeForm": "Confirming sketch setup"},
        {"content": "Initialize sketch state and memory directory",
         "activeForm": "Initializing sketch session"},
    ],
    2: [
        {"content": "Run sketch protocol (one question at a time)",
         "activeForm": "Running sketch session"},
        {"content": "Write sketch-decisions.md with resolved branches",
         "activeForm": "Recording sketch decisions"},
    ],
    3: [
        {"content": "Write handoff-sketch.md for develop",
         "activeForm": "Writing sketch handoff"},
        {"content": "Present handoff menu (default develop)",
         "activeForm": "Completing sketch handoff"},
    ],
}


def _memory_dir() -> Path:
    return runtime_memory_dir()


def _sketch_decisions_path() -> Path:
    return _memory_dir() / "sketch-decisions.md"


def _detect_domain_docs(repo_root: Path) -> str:
    lines: list[str] = []
    ctx = repo_root / "CONTEXT.md"
    cmap = repo_root / "CONTEXT-MAP.md"
    adr = repo_root / "docs" / "adr"
    if cmap.is_file():
        lines.append(f"- `CONTEXT-MAP.md` present at repo root.")
    elif ctx.is_file():
        lines.append(f"- `CONTEXT.md` present at repo root.")
    else:
        lines.append("- No root `CONTEXT.md` or `CONTEXT-MAP.md` yet.")
    if adr.is_dir() and any(adr.glob("*.md")):
        lines.append(f"- ADRs under `docs/adr/` ({len(list(adr.glob('*.md')))} file(s)).")
    else:
        lines.append("- No `docs/adr/` entries yet (create lazily when needed).")
    return "\n".join(lines)


def _no_edit_policy(with_domain_docs: bool) -> str:
    base = (
        "## Permission to modify files\n\n"
        "**Default:** Read-only on the codebase unless exploring answers a question.\n\n"
        "**Session memory (always allowed):** `.codex/forge-codex/memory/` — "
        "especially `sketch-decisions.md` and `project.md`.\n\n"
        "**Do not write** `docs/forge/specs/*-design.md` — that is **develop's** design spec.\n"
    )
    if with_domain_docs:
        base += (
            "\n**`--with-domain-docs` is on:** You may create or update:\n"
            "- `CONTEXT.md` (glossary only — see `templates/CONTEXT-FORMAT.md`)\n"
            "- `docs/adr/*.md` when all three ADR criteria apply (see `templates/ADR-FORMAT.md`)\n"
            "- `CONTEXT-MAP.md` only when the repo has multiple bounded contexts\n"
        )
    else:
        base += (
            "\n**Domain docs off:** Do not edit `CONTEXT.md` or `docs/adr/` in this session.\n"
        )
    return base


def _ensure_sketch_custom(state: SkillState) -> None:
    defaults: dict[str, str | bool] = {
        "topic": "",
        "with_domain_docs": False,
    }
    for k, v in defaults.items():
        state.custom.setdefault(k, v)


def _build_variables(state: SkillState, repo_root: Path) -> dict[str, str]:
    with_docs = bool(state.custom.get("with_domain_docs"))
    mem = _memory_dir()
    decisions_rel = "sketch-decisions.md"
    return {
        "SKETCH_NO_EDIT_POLICY": _no_edit_policy(with_docs),
        "WITH_DOMAIN_DOCS": "yes" if with_docs else "no",
        "MEMORY_DIR": str(mem),
        "SKETCH_DECISIONS_PATH": str(mem / decisions_rel),
        "SKETCH_DECISIONS_REL": decisions_rel,
        "DOMAIN_DOCS_STATUS": _detect_domain_docs(repo_root),
        "TOPIC": str(state.custom.get("topic", "")).strip() or "(set during startup dialogue)",
    }


def _state_path() -> Path:
    return runtime_state_path(SKILL_NAME)


def _next_command(
    step: int,
    state_path: str = "",
    *,
    with_domain_docs: bool = False,
) -> str:
    extra: dict[str, str] = {}
    if state_path:
        extra["state"] = state_path
    flags = ("with-domain-docs",) if with_domain_docs else ()
    return build_next_command(
        SCRIPT_DIR / "sketch.py",
        step,
        MAX_STEP,
        flags=flags,
        **extra,
    )


def _format(
    step: int,
    body: str,
    next_cmd: str | None = None,
    handoff_menu: str | None = None,
) -> str:
    return format_step_output(
        SKILL_NAME,
        step,
        MAX_STEP,
        PHASE_NAMES.get(step, f"Step {step}"),
        body,
        next_cmd=next_cmd,
        phase_todos=PHASE_TODOS.get(step, []),
        handoff_menu=handoff_menu,
        all_phase_names=PHASE_NAMES,
        all_phase_todos=PHASE_TODOS,
    )


def _repo_root() -> Path:
    from scripts.shared.orchestrator import _detect_repo_root

    return _detect_repo_root(Path.cwd())


def handle_step_1(args: argparse.Namespace) -> None:
    sp = resolve_step1_state_path(
        SKILL_NAME,
        args.state,
        parallel=getattr(args, "parallel", False),
        label=getattr(args, "label", None),
        session_id=getattr(args, "session", None),
    )
    sp.parent.mkdir(parents=True, exist_ok=True)

    check_same_skill_clobber(
        SKILL_NAME,
        allow_parallel=bool(getattr(args, "parallel", False) or args.state),
        target_state_path=sp,
    )
    run_step1_session_hygiene(SKILL_NAME, sp)

    existing = None
    if args.state:
        existing = validate_state_path(args.state, SKILL_NAME)
    elif sp.exists():
        existing = sp

    state = None
    if existing is not None:
        try:
            loaded = load_state(existing)
            state = loaded
            sp = existing
        except Exception:
            state = None

    if state is None:
        state = SkillState(skill_name=SKILL_NAME, max_step=MAX_STEP)
        state.started_at = now_iso()

    _ensure_sketch_custom(state)
    state.custom["with_domain_docs"] = bool(getattr(args, "with_domain_docs", False))
    save_state(state, sp)
    print_remaining_session_warning(SKILL_NAME)
    print(f"STATE FILE: {sp}\n", file=sys.stderr)

    mem = _memory_dir()
    mem.mkdir(parents=True, exist_ok=True)

    template = load_template("sketch/startup")
    body = render_template(template, _build_variables(state, _repo_root()))

    state.mark_step_complete(1)
    save_state(state, sp)
    append_skill_run_memory(
        SKILL_NAME,
        1,
        PHASE_NAMES[1],
        "Initialized sketch session.",
        state=state,
        state_path=sp,
    )

    print(
        _format(
            1,
            body,
            _next_command(
                1,
                state_path=str(sp),
                with_domain_docs=bool(state.custom.get("with_domain_docs")),
            ),
        )
    )


def _load_existing_state(
    step: int,
    state_file: str | None,
    session_id: str | None = None,
) -> tuple[SkillState, Path]:
    from scripts.shared.orchestrator import resolve_step_state_path

    sp = resolve_step_state_path(
        SKILL_NAME, step, state_file=state_file, session_id=session_id
    )
    if not sp.exists():
        print("ERROR: No sketch session in progress. Run step 1 first.")
        print("If the state file is elsewhere, pass --state <path>")
        sys.exit(1)
    try:
        state = load_state(sp)
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as exc:
        print(f"ERROR: Cannot load state at {sp}: {exc}")
        sys.exit(1)
    return state, sp


def handle_step_n(
    step: int,
    state_file: str | None = None,
    session_id: str | None = None,
) -> None:
    state, sp = _load_existing_state(step, state_file, session_id=session_id)
    _ensure_sketch_custom(state)
    save_state(state, sp)

    template_map = {
        2: "sketch/session",
        3: "sketch/handoff",
    }
    template_name = template_map.get(step)
    if not template_name:
        print(f"ERROR: Invalid step {step}")
        sys.exit(1)

    template = load_template(template_name)
    body = render_template(template, _build_variables(state, _repo_root()))

    handoff_menu = None
    handoff_path: Path | None = None
    run_summary = f"Completed step {step} ({PHASE_NAMES.get(step, '')})."

    if step == MAX_STEP:
        state.mark_step_complete(step)
        state.completed_at = now_iso()
        save_state(state, sp)

        decisions_note = (
            str(_sketch_decisions_path())
            if _sketch_decisions_path().is_file()
            else "(sketch-decisions.md not found — create before handoff)"
        )
        handoff_path = write_handoff(
            skill_name=SKILL_NAME,
            state=state,
            context={
                "Topic": str(state.custom.get("topic", "")),
                "Domain docs mode": (
                    "with-domain-docs"
                    if state.custom.get("with_domain_docs")
                    else "memory-only"
                ),
                "Decisions artifact": decisions_note,
                "Next": (
                    "Run forge develop — develop investigates, scores solutions, "
                    "and writes docs/forge/specs/...-design.md when scope is medium/large."
                ),
            },
            suggested_next="develop",
        )
        body += f"\n\nHandoff written to: {handoff_path}"
        handoff_menu = build_skill_handoff_menu(SKILL_NAME, state, sp)
        clear_state_file(sp)
        run_summary = "Completed sketch workflow and wrote handoff."
    else:
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

    next_cmd = (
        _next_command(
            step,
            state_path=str(sp),
            with_domain_docs=bool(state.custom.get("with_domain_docs")),
        )
        if step < MAX_STEP
        else None
    )
    print(_format(step, body, next_cmd, handoff_menu=handoff_menu))


def main() -> None:
    parser = build_base_parser(SKILL_NAME, MAX_STEP)
    parser.add_argument(
        "--with-domain-docs",
        action="store_true",
        help="Allow inline CONTEXT.md glossary and sparse docs/adr/ updates",
    )
    args = parser.parse_args()
    if validate_step_or_complete(args.step, MAX_STEP, SKILL_NAME):
        return
    if args.step == 1:
        handle_step_1(args)
    else:
        handle_step_n(
            args.step,
            state_file=args.state,
            session_id=getattr(args, "session", None),
        )


if __name__ == "__main__":
    main()
