"""State resolution and probe injection for evaluate orchestrator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.evaluate.state import EvalState, STATE_FILENAME, load_state, save_state
from scripts.evaluate.template_engine import render_template
from scripts.shared.orchestrator import _detect_repo_root, is_evaluate_state_stale


def is_evaluate_state_name(name: str) -> bool:
    return name == STATE_FILENAME or name.startswith(".evaluate-state-")


def find_state_file(*, include_stale: bool = False) -> Path | None:
    """Search for evaluate state files and return the most recent one."""
    cwd = Path.cwd()
    repo_root = _detect_repo_root()
    candidates: list[Path] = []

    def _collect(dir_path: Path) -> None:
        if not dir_path.exists():
            return
        direct = dir_path / STATE_FILENAME
        if direct.exists():
            candidates.append(direct)
        candidates.extend(sorted(dir_path.glob(".evaluate-state-*.json")))

    _collect(cwd)
    _collect(repo_root / ".forge" / "state")
    _collect(repo_root / ".codex" / "forge" / "state")
    _collect(repo_root / ".codex" / "forge-codex" / "state")

    docs_dir = cwd / "docs"
    if docs_dir.is_dir():
        candidates.extend(docs_dir.rglob(STATE_FILENAME))
        candidates.extend(docs_dir.rglob(".evaluate-state-*.json"))

    existing = []
    for p in candidates:
        if not p.exists():
            continue
        if not include_stale:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if is_evaluate_state_stale(data, p):
                continue
        existing.append(p)
    if not existing:
        return None
    return max(existing, key=lambda p: p.stat().st_mtime)


def resolve_state_path(
    state_file: str | None,
    *,
    session_id: str | None = None,
    step: int = 2,
) -> Path:
    sp = Path(state_file).resolve() if state_file else None

    if sp is not None:
        repo_root = _detect_repo_root().resolve()
        try:
            sp.relative_to(repo_root)
        except ValueError:
            print(f"WARNING: --state path is outside the repository, ignoring: {state_file}", file=sys.stderr)
            sp = None
        if sp is not None and not is_evaluate_state_name(sp.name):
            from scripts.shared.session_store import is_session_state_path

            if not (is_session_state_path(sp) and sp.is_file()):
                print(
                    f"WARNING: --state path doesn't look like an evaluate state file, ignoring: {state_file}",
                    file=sys.stderr,
                )
                sp = None

    if sp is None or not sp.exists():
        if session_id:
            from scripts.shared.session_store import session_json_path

            sp = session_json_path(session_id)
        else:
            sp = find_state_file()
            if sp is None:
                from scripts.shared.session_store import resolve_session_for_step

                sp = resolve_session_for_step(
                    "evaluate",
                    step,
                    session_id=None,
                    state_file=None,
                )

    if sp is None or not sp.exists():
        print("ERROR: No evaluation in progress. Run step 1 first with --plan.")
        print("If the state file is elsewhere, pass --state <path> or --session <id>")
        sys.exit(1)

    return sp


def load_evaluate_state(state_path: Path) -> EvalState:
    try:
        return load_state(state_path)
    except json.JSONDecodeError:
        print(f"ERROR: State file is corrupted: {state_path}")
        print("Delete it and re-run step 1.")
        sys.exit(1)
    except KeyError as e:
        print(f"ERROR: State file is invalid — {e}")
        print("Delete it and re-run step 1.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: State file not found at {state_path}")
        sys.exit(1)


def load_plan_content(state: EvalState) -> str:
    if state.mode == "review":
        return "(review mode — no plan)"
    plan_path = Path(state.plan_path)
    if plan_path.exists():
        return plan_path.read_text(encoding="utf-8")
    return "(plan file not found)"


def should_inject_structural_probes(state: EvalState, step: int) -> bool:
    return (state.mode == "post" and step == 4) or (state.mode == "review" and step == 1)


def inject_structural_probes(
    body: str,
    state: EvalState,
    state_path: Path,
    step: int,
) -> tuple[str, bool]:
    from scripts.shared.structural_probes import inject_structural_probes_section
    from scripts.shared.structural_probes_gate import probe_gate_is_pending

    body, sidecar, _payload = inject_structural_probes_section(
        body,
        skill_name="evaluate",
        step=step,
        repo_root=_detect_repo_root(),
        state_dir=state_path.parent,
        mode=state.mode,
        quick_mode=bool(state.custom.get("quick_mode"))
        or str(state.custom.get("eval_size") or "").lower() in ("small", "trivial")
        or str(state.custom.get("effort") or "").lower() == "light",
    )
    if sidecar:
        state.custom["structural_probes_sidecar"] = str(sidecar)
    return body, probe_gate_is_pending(state_path.parent)


def render_step_body(
    template: str,
    variables: dict[str, str],
    state: EvalState,
    state_path: Path,
    step: int,
) -> tuple[str, bool]:
    body = render_template(template, variables)
    gate_pending = False
    if should_inject_structural_probes(state, step):
        body, gate_pending = inject_structural_probes(body, state, state_path, step)
    return body, gate_pending
