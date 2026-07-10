# Parallel Dispatch Protocol

Used by the implement skill. Defines how the PM orchestrates parallel agent waves, manages sub-branches, and gates progress between waves.

Apply `templates/codex-runtime.md` when translating these instructions into
actual Codex tool usage.

## Prerequisite

A reviewed and approved plan exists in `.forge/memory/plans/` (timestamped filename) with:
- Task breakdown (with agents, file paths, TDD steps, acceptance criteria)
- Parallelization map (with waves and dependencies)
- Interface contracts (for cross-task dependencies)

## Phase 1 — Wave Identification

Extract waves from the parallelization map using topological sort of the dependency graph.

```
## Waves
- Wave 1: [Task 1, Task 2, Task 3] — no dependencies
- Wave 2: [Task 4, Task 5] — depends on Wave 1
- Wave 3: [Task 6] — depends on Wave 2
```

### Wave Validation

Before dispatching, verify:
- [ ] Every task appears in exactly one wave.
- [ ] No task's dependencies are in the same wave or a later wave.
- [ ] No circular dependencies exist.
- [ ] Every dependency references a task that exists in the plan.

## Phase 2 — Sub-Branch Creation

Create a sub-branch for each task in the current wave:

```bash
# From the feature branch
git checkout feat/<short-slug>
git checkout -b feat/<short-slug>/task-[N]
```

Each agent works exclusively on its sub-branch. No two agents commit to the same branch.

## Phase 3 — Agent Dispatch

> **Lifecycle reminder.** Every `spawn_agent` in this phase must be paired with
> a `close_agent` once the agent reports completion (Phase 4 review loop exit)
> or is otherwise no longer needed. See `templates/codex-runtime.md` →
> *Parallel work* for the required spawn → wait → capture → close pattern.
> Codex caps concurrent agents; leaked sessions block later waves.

For each task in the wave, send to the assigned agent:

```
**Task: [title] [beads-id if applicable]**

Read the plan file (path from handoff), section: Task [N].

**Your branch:** feat/<short-slug>/task-[N]
**Files to modify:** [exact file paths from plan]
**Dependencies available:** [list of completed tasks and their branches, or "none — Wave 1"]
**Interface contract:** [contract definition from plan, if this task has upstream deps]

Follow `templates/tdd-protocol.md` for implementation:
1. Write failing test
2. Verify it fails for the right reason
3. Implement minimum code to pass
4. Verify it passes
5. Run full test suite — no regressions

**Acceptance criteria (done when):**
- [ ] [criteria from plan]

When done, report completion to PM.
```

### Agent Dispatch Rules

1. Each agent receives the full task description from the plan — do not abbreviate or summarize.
2. Include the interface contract verbatim if the task depends on another task's output.
3. For Wave 1 tasks, note explicitly that no dependencies exist yet.
4. For Wave 2+ tasks, provide the branch names of completed dependencies so agents can merge them into their sub-branch.

## Phase 4 — Per-Task Review Loop

When an agent reports a task complete, run the review loop from `templates/review-loop.md`:

1. **Self-review:** Producing agent reviews own work.
2. **Cross-agent review:** A different agent reviews (typically Architect for code structure, QA for test quality).
3. **Critic challenge:** Devil's advocate review.
4. **PM validation:** PM checks completeness against acceptance criteria.

A task is not done until the review loop exits clean (all four steps pass with no findings in the same round).

## Phase 5 — Wave Completion Gate

A wave is complete when **all** tasks in the wave have passed their review loops.

### Gate Checklist

- [ ] Every task in the wave has a clean review round (no open findings).
- [ ] Every task's tests pass on its sub-branch.
- [ ] No task has unresolved blockers.
- [ ] **Every agent spawned for this wave has been closed via `close_agent`.**
      No spawned agent may remain open across the wave boundary.

**Do not start Wave N+1 until Wave N passes this gate.**

## Phase 6 — Merge Protocol

Merge completed sub-branches back to the feature branch in dependency order:

```bash
git checkout feat/<short-slug>

# Merge in dependency order
git merge feat/<short-slug>/task-[N] --no-ff
# Run full test suite after each merge
[test command]
# If tests fail, stop and resolve before next merge
```

### Merge Rules

1. **Dependency order.** If Task 4 depends on Task 1, merge Task 1 first.
2. **Test after each merge.** Run the full test suite after each sub-branch merge. If tests fail, resolve before merging the next branch.
3. **No-ff merges.** Use `--no-ff` to preserve branch history for audit trail.
4. **Conflict resolution.** If a merge has conflicts, the PM assigns resolution to the agent most familiar with the conflicting code (typically the agent whose task touches more of the affected file).

## Phase 7 — Wave Transition

After all sub-branches for Wave N are merged and the full test suite passes on the feature branch:

```
## Wave [N] — Complete
- Tasks merged: [list]
- Test suite: [N passed, 0 failed]
- Open issues: [none | list]

Proceeding to Wave [N+1].
```

Create sub-branches for Wave N+1 tasks from the updated feature branch, then repeat from Phase 3.

## Blocker Handling

When an agent reports a blocker:

1. **Agent reports to PM:** "[Task N] is blocked because [reason]."
2. **PM classifies the blocker:**
   - **Missing dependency output:** Route to the agent responsible for the upstream task.
   - **Unclear requirement:** Route to Architect for clarification.
   - **Technical obstacle:** Route to Architect for design guidance.
   - **External blocker (API, infrastructure):** PM records in risk register, reassigns if possible.
3. **PM updates the plan** if the blocker changes wave structure or task assignments.
4. **Other agents in the wave continue.** A blocked task does not block unrelated parallel tasks.

## Rules

1. **Waves are atomic.** Either all tasks in a wave complete and merge, or the wave is not done.
2. **No skipping ahead.** An agent must not start a Wave N+1 task while Wave N is incomplete, even if their specific dependency is done.
3. **Sub-branches are disposable.** If a task needs to be redone from scratch, delete the sub-branch and create a fresh one from the feature branch.
4. **PM is the single point of coordination.** Agents communicate through PM, not directly with each other.
5. **Close every agent.** Each `spawn_agent` is paired with `close_agent` as soon as the agent has reported (or has been determined no longer useful). PM never carries open agents across wave boundaries — Codex caps concurrent agents and leaked sessions block later dispatch.
