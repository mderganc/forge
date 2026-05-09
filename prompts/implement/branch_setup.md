# Phase 2: Branch Setup

Create the feature branch and identify implementation waves.

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

Record waves in `.codex/forge-codex/memory/project.md`:

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

## Create Feature Branch

```
git checkout -b {{FEATURE_BRANCH_PATTERN}}
```

Record branch name in `.codex/forge-codex/memory/project.md`.
