# Stage 5 — Implementation

## Purpose
Dispatch developer agents in parallel waves to implement the approved plan, with per-task review loops and blocker handling.

## Lead Agent
**PM** — orchestrates waves and dispatches agents

## Superpowers Integration
- Invoke `superpowers:dispatching-parallel-agents` if available for each wave
- Developers use `superpowers:test-driven-development` if available

## PM Actions

### 1. Create Feature Branch

git checkout -b forge/[feature-name]

### 2. Identify Waves

From the parallelization map in the plan file (under `.codex/forge-codex/memory/plans/`):
- **Wave 1:** All tasks with no blockers
- **Wave 2:** Tasks depending only on Wave 1 completions
- **Wave N:** Tasks depending only on completed waves

### 3. Dispatch Wave

For each task in the wave, send to the assigned agent:

> **Task: [title from plan] [beads-id]**
>
> **Branch:** git checkout -b [sub-branch] from forge/[feature-name]
> **Plan:** Read the plan file (path from handoff), section for Task [N]
> **Beads:** Update status: bd update [id] --status in_progress --claim
> **Memory:** Write progress to `.codex/forge-codex/memory/[role]-dev.md`
> **TDD:** Write failing test before implementation code
>
> On completion: commit, bd close [id], write notes to memory.
> On blocker: stop, write to memory, bd update [id] --status blocked.

Dispatch all tasks in a wave in parallel using the Agent tool.

### 4. Per-Task Review Loop

After each agent completes:

| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Implementing dev | Code matches plan? TDD followed? Any deviations? |
| Cross-review | QA Reviewer | Tests pass on sub-branch? Edge cases covered? |
| Critic challenge | Critic | Edge cases missed? Plan assumptions that didn't hold? Most likely production failure? |
| PM validation | PM | Beads status updated? Memory notes written? |

If issues → agent fixes → re-review. If clean → mark task complete.

### 5. Wave Completion → Next Wave

After all tasks in a wave pass review:
1. Merge wave sub-branches into feature branch (dependency order)
2. Run test suite after each merge
3. If merge conflict → assign to owning agent → critic reviews resolution
4. If tests fail after merge → assign to responsible agent → fix before next merge
5. Proceed to next wave

### 6. Blocker Handling

Agent reports blocker →
  PM reads blocker details from memory file →
  PM assigns Architect:
    - Plan wrong? → Revise (loop to Stage 4 review loop)
    - Code issue? → Architect produces targeted fix approach
    - External? → Log in beads, write to backlog, continue with remaining
  Critic reviews Architect's assessment →
  Agent resumes or task deferred

### 7. Stage Gate

| Autonomy | Behavior |
|----------|----------|
| Level 1 | Present wave completion summaries between waves |
| Level 2 | Auto-proceed between waves, full summary after all waves |
| Level 3 | Auto-proceed entirely, log summaries |

### 8. Git Checkpoint

git add .codex/forge-codex/memory/ && git commit -m "workflow: Stage 5 complete — implementation done"

Record in project.md: `## Stage 5: COMPLETE [timestamp]`

Git state: Feature branch with sub-branches ready for Stage 6 merge.
