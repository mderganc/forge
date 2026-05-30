#!/usr/bin/env python3
"""Ship skill orchestrator — Graphify refresh at finalize time.

Workflow skills (develop, plan, implement, code-review, test, diagnose, evaluate)
no longer print GRAPHIFY blocks or spawn background refresh. Run this step (or
``$forge:ship``) before commit/PR/publish so the index matches the tree you ship.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.shared.orchestrator import (
    _detect_repo_root,
    build_base_parser,
    format_step_output,
    validate_step_or_complete,
)

SKILL_NAME = "ship"
MAX_STEP = 1

PHASE_NAMES = {1: "Graphify preflight (before commit)"}

PHASE_TODOS = {
    1: [
        {"content": "Refresh graphify index for shipped code",
         "activeForm": "Refreshing graphify index"},
        {"content": "Continue ship skill: status, commit, push, PR, publish",
         "activeForm": "Running ship preflight"},
    ],
}


def _ship_body(repo_root: Path, *, refresh_note: str) -> str:
    return f"""## Graphify — end-of-session refresh

{refresh_note}

The knowledge graph should now match the tree you are about to commit or open in a PR.

## Next — agent-driven ship

Follow **`.cursor/skills/ship/SKILL.md`** (or the user’s narrowed scope: commit only, PR, publish, etc.):

1. **Preflight** — `git status`, diff, branch tracking, optional tests.
2. **Commit** — stage relevant paths only; never commit secrets.
3. **Push / PR / merge / publish** — only when the user asked.

Graphify is **not** re-run on other `forge <skill> --step` invocations; refresh happens here at ship time.
Repo: `{repo_root}`
"""


def handle_step_1() -> None:
    repo_root = _detect_repo_root(Path.cwd())
    print(
        "forge: ship step 1 — refreshing graphify index (foreground)…",
        file=sys.stderr,
        flush=True,
    )
    refresh_note = "Graphify refresh was not run (no CLI or `FORGE_SKIP_GRAPHIFY=1`)."
    if not __import__(
        "forge_next.graphify_enforcement", fromlist=["graphify_fully_disabled"]
    ).graphify_fully_disabled(repo_root):
        try:
            from forge_next.graphify import refresh

            refresh(repo_root, background=False)
            refresh_note = (
                "Ran **`forge graphify refresh`** (foreground). "
                "If the CLI was missing, set `FORGE_GRAPHIFY_COMMAND` or install `graphify`."
            )
        except Exception as exc:
            refresh_note = f"Graphify refresh failed (non-fatal): {exc}"

    body = _ship_body(repo_root, refresh_note=refresh_note)
    output = format_step_output(
        SKILL_NAME,
        1,
        MAX_STEP,
        PHASE_NAMES[1],
        body,
        next_cmd=None,
        phase_todos=PHASE_TODOS[1],
        all_phase_names=PHASE_NAMES,
        all_phase_todos=PHASE_TODOS,
    )
    print(output, flush=True)


def main() -> None:
    parser = build_base_parser(SKILL_NAME, MAX_STEP)
    args = parser.parse_args()
    if validate_step_or_complete(args.step, MAX_STEP, SKILL_NAME):
        return
    if args.step != 1:
        print(f"ERROR: ship only has step 1 (got {args.step})", file=sys.stderr)
        sys.exit(1)
    handle_step_1()


if __name__ == "__main__":
    main()
