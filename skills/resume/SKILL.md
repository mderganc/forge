---
description: |
  Resume any in-progress forge-codex workflow. Detects active skill state files,
  determines where work left off, and outputs the exact command to continue.
  Handles cross-skill transitions (advance to the next skill in the pipeline)
  and surfaces a menu when multiple sessions exist.
---

# forge-codex Resume — Meta-Orchestrator

When this skill activates, invoke the resume orchestrator script.

Read `templates/codex-runtime.md` before executing the workflow if you need a
tooling reminder.

## Invocation

<invoke cmd="python3 [repo-root]/scripts/shared/resume.py" />

## Behavior

- **No active session:** Check for handoff files. If a pipeline skill has
  completed, suggest the next one. Otherwise, report idle state.
- **One active session:** Output the exact resume command, distinguishing
  between re-executing an in-progress step (idempotent) and advancing past
  a completed step.
- **Multiple active sessions:** Output a menu and ask the user directly which
  session to resume.

## Follow-up

After the resume script produces a command, execute that command immediately
to re-enter the skill at the correct step. Do NOT analyze first — run the
script and follow its output.

## Cleanup mode

`python3 scripts/shared/resume.py --cleanup` lists state files eligible for
cleanup (dry-run by default). Add `--force` to delete; `--all-stale --force`
clears every state file regardless of age. After two consecutive same-step
failures (`failure_count >= 2`), the resume command emits an "inspect logs"
hint instead of a third retry.
