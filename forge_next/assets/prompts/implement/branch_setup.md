# Phase 2: Branch Setup

Set up branch context and identify implementation waves.

## Parsed plan metadata

When `forge implement --step 1 --plan <path>` was used (or the plan path is otherwise recorded), the orchestrator reads the **Parallelization Map** table in the plan (see `templates/writing-plans.md`) and stores:

- `total_waves` — max **Wave** column value
- Per-task rows — used to populate wave dispatch prompts

Use **`forge implement --branch-prefix`** on step 1 to choose a git prefix (default **`feat`**): `feat`, `fix`, `chore`, `refactor`, `docs`, or `hotfix`.

## Branch Strategy

From the plan and branch prefix:

- Feature branch pattern: `{{FEATURE_BRANCH_PATTERN}}`
- Task sub-branches: `{{TASK_BRANCH_PATTERN}}`

## Wave Identification

If the parallelization table was parsed, wave counts are already in state. Otherwise:

Read the parallelization map from the plan.
Identify waves (groups of tasks that can run in parallel).
Wave 1 = tasks with no dependencies.
Wave N = tasks whose dependencies are all in waves < N.

If you still cannot produce a reliable wave map, **do not prompt the user to pick a fallback**. Continue automatically with direct implementation from the plan in dependency order (single-pass mode).

Record waves in `{{MEMORY_DIR}}/project.md`:

```
## Implementation Waves
Wave 1: [task list]
Wave 2: [task list]
...
Total waves: [N]
```

## Validation

Before proceeding, verify:
- [ ] Every task appears in exactly one wave
- [ ] No task's dependencies are in the same wave or a later wave
- [ ] No circular dependencies exist
- [ ] Every dependency references a task that exists in the plan

## Create or Reuse Feature Branch

1. Check current branch:
   - `git branch --show-current`
2. If already on the intended feature branch for this work (for example `{{BRANCH_PREFIX}}/...`), **reuse it**.
3. Only create a new branch when still on `main` (or other base branch):
   - `git checkout -b {{FEATURE_BRANCH_PATTERN}}`
4. **Never create branches with `forge/` prefix.** Valid prefixes are only: `feat/`, `fix/`, `chore/`, `refactor/`, `docs/`, `hotfix/`.

Record branch name in `{{MEMORY_DIR}}/project.md`.

## Optional: git worktree (second checkout)

**Default:** Parallel tasks use **task sub-branches** from one working tree per `templates/parallel-dispatch.md`.

**When to consider `git worktree` instead:** You want **`main` untouched** in the current directory, or a **long-lived second line of work** in parallel without constantly switching branches in a single tree — i.e. a separate folder linked to the same repo is simpler than many short-lived sub-branches.

If the team chooses a worktree:

1. From the repo root, add a linked checkout (example — adjust paths for your OS; `main` may be `master`):
   - `git worktree add ../my-repo-workstream {{FEATURE_BRANCH_PATTERN}}`
2. Run project setup and a **clean test baseline** in that tree before implementation (same expectations as a normal branch checkout).

This is **optional** — do not treat worktrees and sub-branches as two mandatory patterns; pick one strategy per effort.
