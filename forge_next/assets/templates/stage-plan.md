# Stage 4 — Planning

## Purpose
Produce a concrete implementation plan for approved solutions with task breakdown, parallelization map, branch strategy, and TDD steps.

## Lead Agents
- **Planner** — owns the plan file and task breakdown (`templates/writing-plans.md`)
- **Architect** — contributes Architecture Overview and reviews architectural consistency

## Plan modes

Select **`default`** or **`lite`** per `templates/plan-modes.md`. If mode is not passed on the CLI, confirm with the user (orchestrator step 1 includes a recommendation). Both modes require executor-ready tasks with no placeholders.

## PM Actions

### 1. Assign Planning

**Architect (step 2):** Design unified architecture; fill `ARCHITECTURE-OVERVIEW` in the plan file.

**Planner (step 3):** Complete remaining plan sections per `templates/writing-plans.md`.

Send to Planner:

> Read approved solutions from `.codex/forge/memory/project.md` and handoff/develop memory.
> Use Codex runtime conventions from `templates/codex-runtime.md`.
> Plan file: `.codex/forge/memory/plans/` (timestamped path from orchestrator).
>
> Produce:
> 1. Plan header (Goal, scope, plan mode)
> 2. Branch strategy
> 3. Task breakdown — exact paths, TDD, verify command + expected outcome
> 4. Parallelization map
> 5. Interface contracts (when tasks depend on each other)
> 6. Risk register + rollback
>
> Create beads issues for each task with dependencies.

### 2. Branch Strategy Requirements

The plan MUST define:

Feature branch: feat/<short-slug>
  ← Created from: main (or user-specified base)

Task branches (parallel tasks):
  feat/<short-slug>/[task-branch]
  ← Created from feature branch
  ← Merged back after review

Sequential tasks: commit directly to feature branch

### 3. Task Requirements

Each task MUST include:
- Assigned agent (backend-dev or frontend-dev)
- Branch name (sub-branch or feature branch)
- Exact file paths to create/modify
- Dependencies on other tasks
- TDD steps (write test → verify fail → implement → verify pass)
- **Verify:** command + expected outcome (both plan modes)
- Concrete acceptance criteria ("done when")

### 4. Run Review Loop

Per `templates/review-loop.md`:

| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Planner | Paths real? No placeholders? Verify steps on every task? |
| Cross-review | QA Reviewer | Testable tasks? Verification evidence? Integration strategy? |
| Critic challenge | Critic | Hidden deps? Weakest assumption? Rollback realistic? |
| PM validation | PM | Solutions covered? Mode-appropriate depth? Beads cross-referenced? |

### 5. Beads Tracking

For each implementation task:
bd create "[task title]" -t task --parent [epic-id] -l "implementation,stage-4,agent:[role]"
bd dep add [task-id] [solution-id] --type blocks
bd dep add [task-2] [task-1] --type blocks  (inter-task deps)
bd comments add [task-id] "branch: feat/<short-slug>/[task-branch]"

### 6. Stage Gate

| Autonomy | Behavior |
|----------|----------|
| Level 1 | Present plan summary, ask for approval |
| Level 2 | Pause — present plan, ask for approval |
| Level 3 | Auto-proceed, log plan summary |

User can: approve, request changes, reject a solution (→ backlog), change autonomy.

### 7. Git Checkpoint

git add .codex/forge/ && git commit -m "workflow: Stage 4 complete — plan approved"

Record in project.md: `## Stage 4: COMPLETE [timestamp]`
