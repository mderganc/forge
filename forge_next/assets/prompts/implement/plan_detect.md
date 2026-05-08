# Phase 1: Plan Detection

Detect and load the implementation plan.

## Detection Order

1. If `--plan` argument provided, use that path
2. If `.codex/forge-codex/memory/handoff-plan.md` exists, read plan path from it
3. If `.codex/forge-codex/memory/plans/` exists, use the most recent plan file (sorted by filename)
4. Otherwise, ask the user for the plan location

## Instructions

1. Read the plan file
2. Validate that file paths in the plan exist or can be created
3. Count total tasks and identify assigned agents
4. Record plan summary in `.codex/forge-codex/memory/project.md`

## Team Composition

Based on plan agent assignments, activate:

{{TEAM_COMPOSITION}}

Record active team in `.codex/forge-codex/memory/project.md` under `## Team`.

## Plan Summary

After loading, confirm with the user:
- Plan name and location
- Number of tasks identified
- Agents to be dispatched
- Estimated number of waves

Then proceed to branch setup.
