# Beads Integration Patterns

Defines how the forge-codex team uses beads for structured issue tracking. All beads operations are conditional — check `project.md` for `beads: available` before running any `bd` command.

## Degraded Mode

If beads is unavailable (`beads: unavailable` in project.md):
- All tracking falls back to memory files only
- Backlog entries still get written to `.codex/forge-codex/backlog.md`
- Beads ID references in memory files are replaced with sequential IDs (e.g., `[F-001]`, `[RC-001]`, `[S-001]`, `[T-001]`)
- The workflow is otherwise identical

## Epic Structure

One epic per `/forge` invocation:

bd create "[feature name]" -t epic -p [priority] -l "forge,[task-type]" -d "forge-codex team epic. Autonomy: Level N"

All child issues use `--parent [epic-id]`.

## Issue Hierarchy

Epic: [feature name]
├── Finding (stage-1)        -t bug/task  -l "finding,stage-1"
├── Root Cause (stage-1)     -t task      -l "root-cause,stage-1"
├── Solution Option (stage-2) -t task     -l "solution,stage-2,option"
├── Solution Option (stage-2) -t task     -l "solution,stage-2,option"
├── Impl Task (stage-4)      -t task      -l "implementation,stage-4,agent:[role]"
├── Review Finding (stage-6)  -t bug      -l "review-finding,stage-6"
└── ...

## Dependency Chain (all use `blocks` type)

Finding ←blocks── Root Cause ←blocks── Solution ←blocks── Impl Task

Direction: `bd dep add [downstream-id] [upstream-id] --type blocks`
- Downstream depends on (is blocked by) upstream.
- Example: `bd dep add [solution-id] [root-cause-id] --type blocks`

## Provenance (use `discovered-from` type)

bd dep add [root-cause-id] [finding-id] --type discovered-from
bd dep add [review-finding-id] [task-id] --type discovered-from

## Labels

| Label | Applied To | Meaning |
|-------|-----------|---------|
| finding | Findings | Issue surfaced during investigation |
| root-cause | Root causes | Underlying cause identified via five-why |
| solution | Solution options | Proposed solution for a root cause |
| option | Solution options | One of multiple alternatives |
| recommended | Preferred solution | Architect's recommended choice |
| implementation | Impl tasks | Task in the implementation plan |
| review-finding | Review findings | Issue found during Stage 6 review |
| stage-N | All | Which stage created the issue |
| agent:[role] | Impl tasks | Which agent is assigned |
| critic | Critic findings | Finding from the critic agent |
| review | Review findings | General review finding |
| deferred | Deferred items | Deferred by user decision |

## Scores as Comments

bd comments add [solution-id] "Scores: Q=7 T=4 C=3 R=8 E=6 P=5.5"

## Status Transitions

| Action | Command |
|--------|---------|
| Claim work | bd update [id] --status in_progress --claim |
| Block on issue | bd update [id] --status blocked |
| Complete | bd close [id] --reason "[reason]" |
| Defer | bd close [id] --reason "Deferred by user: [reason]" |
| Reopen | bd reopen [id] |

## Epic Closure

Only close the epic when all children are closed or deferred:
bd comments add [epic-id] "Development complete. [summary stats]"
bd close [epic-id] --reason "Feature complete"
