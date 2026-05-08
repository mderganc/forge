---
description: |
  Show current position in the workflow. Reports which skills have completed,
  what's in progress, open findings, and beads state.
---

# forge-codex Status — Flow Dashboard

You are reporting the current state of the forge-codex development flow.

## Instructions

1. Read `.codex/forge-codex/memory/project.md` for the Skill Flow section
2. Check for handoff files: `.codex/forge-codex/memory/handoff-*.md`
3. Check for state files under `.codex/forge-codex/state/`
4. Read all handoff files that exist to get dashboards

## Report Format

Present a composite dashboard:

### forge-codex Flow Status

| Skill | Status | Key Output |
|-------|--------|------------|
| develop | COMPLETE / IN_PROGRESS / NOT_STARTED | Approved N solutions |
| plan | ... | N tasks planned |
| evaluate | ... | N findings (mode) |
| implement | ... | N files changed |
| code-review | ... | N findings |
| test | ... | N pass, M fail |
| diagnose | ... | Root cause: ... |

### How to Determine Status

- **COMPLETE**: A `handoff-{skill}.md` file exists in `.codex/forge-codex/memory/`
- **IN_PROGRESS**: A `.codex/forge-codex/state/{skill}.json` file exists but no handoff
- **NOT_STARTED**: Neither file exists

### Open Findings

Collect findings from all state files and handoff files. Present them grouped
by source skill:

| ID | Skill | Severity | Title | Status |
|----|-------|----------|-------|--------|

### Beads State

Read beads state from `project.md` or state files:
- Epic ID (if any)
- Open issue count
- Closed issue count

### Suggested Next

Based on the flow position, suggest the next skill to run:
- If no skills have run: suggest `develop`
- If develop is complete but plan is not: suggest `plan`
- If implement is complete but code-review is not: suggest `code-review`
- If code-review is complete but test is not: suggest `test`
- If test has failures: suggest `diagnose`
- If all are complete: report "Flow complete"
