# Dashboard Template

Defines the skill completion dashboard format rendered by every orchestrator at skill completion and in handoff files.

## Purpose

The dashboard provides a quick-scan summary of what a skill did, how it went, and what comes next. It's rendered at skill completion and appended to the handoff file.

## Dashboard Format

```
## Workflow — Skill Summary
**Skill:** [name]
**Status:** COMPLETE | IN_PROGRESS | PARTIAL | BLOCKED
**Duration:** [start → end]
**Autonomy level:** [1/2/3]
**Quick mode:** [yes/no]
**Agents dispatched:** [list with roles, e.g., "Architect, Dev-1, Dev-2, QA"]
**Review rounds:** [N total across all review loops in this skill]
**Findings:** [N open, M resolved]
**Beads:** [epic link or "none", N issues]
**Memory files updated:** [list of .codex/forge-codex/memory/ files written or modified]
**Next suggested:** [next-skill]
```

## Field Definitions

| Field | Description |
|-------|-------------|
| **Skill** | The skill that just completed (develop, plan, implement, test, diagnose, code-review, evaluate). |
| **Status** | COMPLETE = all work done. IN_PROGRESS = still running (mid-skill render). PARTIAL = some work done, not all. BLOCKED = cannot proceed. |
| **Duration** | Wall clock time from skill start to skill end. Format: `HH:MM` or descriptive (e.g., "~15 minutes"). |
| **Autonomy level** | 1 = user approves each step. 2 = user approves key decisions. 3 = fully autonomous. |
| **Quick mode** | Whether the skill ran in quick mode (reduced review loops, faster but less thorough). |
| **Agents dispatched** | Which agent personas were activated during this skill. |
| **Review rounds** | Total number of review loop rounds across all review points in the skill. |
| **Findings** | Count of review findings: open (unresolved) and resolved. Zero open is the target. |
| **Beads** | Link to the epic in beads (if active) and count of issues created/updated. |
| **Memory files updated** | List of `.codex/forge-codex/memory/` files that were created or modified during this skill. Helps the next skill know what to read. |
| **Next suggested** | The next skill to run. |

## When to Render

1. **Skill completion:** Render the dashboard as the last output of the skill, before writing the handoff file.
2. **Handoff file:** Append the dashboard as Section 5 of the handoff file (see `templates/handoff-protocol.md`).
3. **Mid-skill status:** If the user requests status mid-skill, render with Status = IN_PROGRESS and current counts.

## Composite Dashboard — `status`

The `status` skill renders a composite view of all skill dashboards from the current session:

```
## Workflow — Session Dashboard

### develop
**Status:** COMPLETE | **Duration:** ~12 min | **Findings:** 0 open, 3 resolved
**Next:** plan

### plan
**Status:** COMPLETE | **Duration:** ~8 min | **Findings:** 0 open, 1 resolved
**Next:** implement

### implement
**Status:** IN_PROGRESS | **Duration:** ~20 min (ongoing) | **Findings:** 2 open, 5 resolved
**Agents:** Architect, Dev-1, Dev-2, QA | **Wave:** 2/3

### test
**Status:** PENDING
```

### Composite Dashboard Rules

1. Show all skills in pipeline order: develop → plan → implement → test.
2. Use a compact single-line format per skill for scannability.
3. Show PENDING for skills that haven't started yet.
4. For IN_PROGRESS skills, include current progress indicators (wave number, task count, etc.).

## Rendering Rules

1. **All fields are required.** If a field doesn't apply (e.g., no agents dispatched for a solo skill), use "none" — do not omit the field.
2. **Findings count must be accurate.** Count from the review loop records, not from memory.
3. **Memory files list must be complete.** Every `.codex/forge-codex/memory/` file touched during the skill must be listed.
4. **Next suggested must be actionable.** It should be a valid next skill that the user can run immediately.
5. **Keep it scannable.** The dashboard is meant to be read in 5 seconds. Do not add prose or explanations inside the dashboard block.
