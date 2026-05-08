# Stage 4 — Planning

## Purpose
Produce a concrete implementation plan for approved solutions with task breakdown, parallelization map, branch strategy, and TDD steps.

## Lead Agent
**Architect** — produces the implementation plan

## Superpowers Integration
- Invoke `superpowers:writing-plans` if available

## PM Actions

### 1. Assign Planning

Send to Architect:

> **Task: Create implementation plan for approved solutions**
>
> Read approved solutions from `.codex/forge-codex/memory/project.md` (Stage 3 decisions).
> Read `.codex/forge-codex/memory/solutions.md` for full solution details.
> Use Codex runtime conventions from `templates/codex-runtime.md`.
>
> Produce a unified plan in `.codex/forge-codex/memory/plans/` (timestamped filename):
> 1. Architecture — how approved solutions fit together
> 2. Branch strategy — feature branch + task sub-branches for parallel work
> 3. Task breakdown — exact file paths, steps (TDD), acceptance criteria
> 4. Parallelization map — which tasks can run simultaneously
> 5. Risk register — what could go wrong, mitigation
> 6. Rollback strategy — how to undo
>
> Create beads issues for each task with dependencies.

### 2. Branch Strategy Requirements

The plan MUST define:

Feature branch: forge/[feature-name]
  ← Created from: main (or user-specified base)

Task branches (parallel tasks):
  forge/[feature-name]/[task-name]
  ← Created from feature branch
  ← Merged back after Stage 6 review

Sequential tasks: commit directly to feature branch

### 3. Task Requirements

Each task MUST include:
- Assigned agent (backend-dev or frontend-dev)
- Branch name (sub-branch or feature branch)
- Exact file paths to create/modify
- Dependencies on other tasks
- TDD steps (write test → verify fail → implement → verify pass)
- Concrete acceptance criteria ("done when")

### 4. Run Review Loop

Per `templates/review-loop.md`:

| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Architect | File paths real? Tasks specific enough? Parallelization respects deps? Rollback realistic? |
| Cross-review | QA Reviewer | Every task testable? Acceptance criteria concrete? Test strategy covers integration? |
| Critic challenge | Critic | Hidden deps between parallel tasks? Weakest assumption? What if Task N breaks Task M? |
| PM validation | PM | Plan covers all approved solutions? All tasks in beads? Parallelization maximized? |

### 5. Beads Tracking

For each implementation task:
bd create "[task title]" -t task --parent [epic-id] -l "implementation,stage-4,agent:[role]"
bd dep add [task-id] [solution-id] --type blocks
bd dep add [task-2] [task-1] --type blocks  (inter-task deps)
bd comments add [task-id] "branch: forge/[feature]/[task]"

### 6. Stage Gate

| Autonomy | Behavior |
|----------|----------|
| Level 1 | Present plan summary, ask for approval |
| Level 2 | Pause — present plan, ask for approval |
| Level 3 | Auto-proceed, log plan summary |

User can: approve, request changes, reject a solution (→ backlog), change autonomy.

### 7. Git Checkpoint

git add .codex/forge-codex/ && git commit -m "workflow: Stage 4 complete — plan approved"

Record in project.md: `## Stage 4: COMPLETE [timestamp]`
