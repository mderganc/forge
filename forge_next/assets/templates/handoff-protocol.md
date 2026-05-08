# Handoff Protocol

Defines the handoff file format used by all skills to chain together. When a skill completes, it writes a handoff file providing context for the next skill in the chain.

## Purpose

Skills in the forge-codex pipeline run sequentially: develop → plan → implement → test (or variations). Each skill needs context from the previous one. The handoff file is the structured interface between skills — it ensures no context is lost and the next skill can start without re-investigating.

## File Location

```
.codex/forge-codex/memory/handoff-{skill-name}.md
```

Examples:
- `.codex/forge-codex/memory/handoff-develop.md` — written by develop, read by plan
- `.codex/forge-codex/memory/handoff-plan.md` — written by plan, read by implement
- `.codex/forge-codex/memory/handoff-implement.md` — written by implement, read by test
- `.codex/forge-codex/memory/handoff-diagnose.md` — written by diagnose, read by develop

## Required Sections

Every handoff file must contain all of the following sections.

### Section 1: Completed

```
## Completed
- **Skill:** [skill name]
- **Timestamp:** [ISO 8601]
- **Status:** COMPLETE | PARTIAL | BLOCKED
- **Quick mode:** [yes/no]
- **Duration:** [start → end, or elapsed time]
```

Status meanings:
- **COMPLETE:** Skill finished all work successfully. Next skill can proceed.
- **PARTIAL:** Skill completed some work but not all (e.g., user deferred some decisions). Next skill should check what's missing.
- **BLOCKED:** Skill could not complete due to a blocker. Next skill should not proceed — resolve the blocker first.

### Section 2: Context for Next Skill

Key-value pairs specific to what the next skill needs. Content varies by skill.

```
## Context for Next Skill

### develop → plan
- **Task type:** [bugfix | feature | refactor]
- **Root cause:** [one-line summary]
- **Investigation file:** [path to investigation.md]
- **Selected solution:** [title and one-line summary]
- **Solution scoring:** [path or inline summary]
- **Key constraints:** [from brainstorming requirements context]
- **Open questions:** [any unresolved items the plan must address]

### plan → implement
- **Plan file:** [path to plan.md]
- **Total tasks:** [N]
- **Total waves:** [N]
- **Feature branch:** [branch name]
- **Interface contracts:** [count, with note if any are complex]
- **Key risks:** [top 2-3 from risk register]

### implement → test
- **Feature branch:** [branch name]
- **Tasks completed:** [N/N]
- **Review rounds:** [total across all tasks]
- **Unresolved findings:** [count and severity]
- **Merge status:** [all sub-branches merged | partial]
- **Known gaps:** [anything implementation couldn't complete]

### diagnose → develop
- **Diagnosis:** [root cause summary]
- **Evidence file:** [path to diagnosis output]
- **Reproduction case:** [path or inline minimal repro]
- **Suggested approach:** [fix direction]
```

### Section 3: Beads State

```
## Beads State
- **Epic:** [beads ID or "none"]
- **Open issues:** [count, with IDs]
- **Closed issues:** [count]
- **Instructions for next skill:** [any beads-specific context — e.g., "close issue #5 when test passes"]
```

If beads is not in use, this section should state: `Beads not active for this session.`

### Section 4: Suggested Next

```
## Suggested Next
`[next-skill-name]`

[One-line rationale for why this is the suggested next step.]
```

If the status is BLOCKED, this section should suggest the resolution action instead of the next skill.

### Section 5: Dashboard

Append the skill completion dashboard as defined in `templates/dashboard.md`.

## Reading Convention

The **first thing** a skill does when it starts is check for a handoff file from the previous skill:

1. Read `.codex/forge-codex/memory/handoff-{previous-skill}.md`.
2. If it exists and status is COMPLETE or PARTIAL, extract the context and proceed.
3. If it exists and status is BLOCKED, report the blocker to the user and stop.
4. If it doesn't exist, proceed without handoff context (first skill in chain, or manual invocation).

## Resume Logic

If a skill is interrupted and restarted:

1. Check if a handoff file exists for the **current** skill (e.g., implement checks for `handoff-implement.md`).
2. If it exists with status PARTIAL, read it to understand what was already done and resume from there.
3. If it exists with status COMPLETE, the skill already finished — notify user and suggest the next skill.
4. If it doesn't exist, start fresh.

## Cleanup

- Handoff files are **preserved** after the next skill reads them. They serve as an audit trail of the full pipeline execution.
- Handoff files are only cleared when the user passes the `--new` flag, which signals a fresh session.
- When `--new` is passed, all files in `.codex/forge-codex/memory/handoff-*.md` are deleted before the skill starts.

## Rules

1. **Every skill writes a handoff file on completion.** No exceptions, even if the skill thinks the next step is obvious.
2. **Handoff files are append-only during a session.** If a skill reruns (e.g., after review findings), it updates the existing handoff file — it does not delete and recreate.
3. **Context must be self-contained.** The next skill should not need to re-read investigation files or plan files to understand the handoff — the key information is summarized in the handoff. (Detailed files are referenced by path for deep dives.)
4. **Status must be honest.** Do not write COMPLETE if there are known gaps. Use PARTIAL and document what's missing.
