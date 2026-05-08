# Phase 2: Branch Setup

Create the feature branch and identify implementation waves.

## Branch Strategy

From the plan:
- Feature branch: `forge/[feature-name]`
- Task sub-branches: `forge/[feature-name]/[task-name]`

## Wave Identification

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
git checkout -b forge/[feature-name]
```

Record branch name in `.codex/forge-codex/memory/project.md`.
