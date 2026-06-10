---
description: |
  Show current position in the workflow. Reports which skills have completed,
  what's in progress, open findings, and beads state.
---

# Forge Status — Flow Dashboard

You are reporting the current state of the Forge development flow.

Runtime root: **`.codex/forge/`** by default (legacy **`.codex/forge-codex/`** if not migrated).

## Instructions

1. Read `.codex/forge/memory/project.md` for the Skill Flow section
2. Check handoffs: `.codex/forge/memory/handoff-*.md` and per-session `sessions/<id>/handoff.md`
3. Check active sessions: `.codex/forge/sessions/*/session.json` and legacy `.codex/forge/state/*.json`
4. Read handoff files that exist to build the dashboard

## Report Format

Present a composite dashboard:

### Forge Flow Status

| Skill | Status | Key Output |
|-------|--------|------------|
| sketch | COMPLETE / IN_PROGRESS / NOT_STARTED | Intent decisions logged |
| design | COMPLETE / IN_PROGRESS / NOT_STARTED | Approved N solutions |
| plan | ... | N tasks planned |
| evaluate | ... | N findings (mode) |
| implement | ... | N files changed |
| code-review | ... | N findings |
| test | ... | N pass, M fail |
| diagnose | ... | Root cause: ... |

### How to Determine Status

- **COMPLETE**: A `handoff-{skill}.md` exists under `memory/` or the session's `handoff.md`
- **IN_PROGRESS**: Active `sessions/<id>/session.json` or legacy `state/{skill}.json` without handoff
- **NOT_STARTED**: Neither applies

### Open Findings

Collect findings from state sidecars and handoff files. Present grouped by source skill:

| ID | Skill | Severity | Title | Status |
|----|-------|----------|-------|--------|

### Beads State

Read beads state from `project.md` or state files:
- Epic ID (if any)
- Open issue count
- Closed issue count

### Suggested Next

Based on flow position, suggest the next skill:
- If intent is fuzzy: suggest `sketch` then `design`
- If no skills have run: suggest `design`
- If design is complete but plan is not: suggest `plan`
- If implement is complete but code-review is not: suggest `code-review`
- If code-review is complete but test is not: suggest `test`
- If test has failures: suggest `diagnose`
- If all are complete: suggest `ship` or report "Flow complete"

## Invocation

Use the global launcher:

<invoke cmd="forge status" />
