# Writing Plans Protocol

Used by the plan skill and planner agent. Defines the required structure, format, and quality bar for implementation plans.

See also `templates/plan-modes.md` for `default` vs `lite` ceremony; **correctness requirements are identical in both modes**.

## Plan Header (required at top of every plan file)

After `# Implementation Plan`, include:

```markdown
**Goal:** [One sentence]
**Spec reference:** [Handoff, develop memory, or user request]
**In scope:** [Bullets]
**Out of scope:** [Bullets — explicit]
**Plan mode:** default | lite
```

## Plan Structure

Every plan must contain all of the following sections. Missing sections are a review blocker.

1. Architecture Overview
2. Branch Strategy
3. Task Breakdown
4. Parallelization Map
5. Interface Contracts
6. Risk Register
7. Rollback Strategy
8. Documentation *(plan-time documentation scope — feeds implement documentation gate)*

## 1. Architecture Overview

A concise description of the architectural approach. Include:

- **What changes:** Which modules, services, or layers are affected.
- **Why this approach:** Reference the selected solution candidate and its scoring rationale.
- **Key decisions:** Architectural choices that constrain the implementation (e.g., sync vs async, library choice, data model shape).
- **Diagram (optional):** ASCII diagram of component relationships if the architecture is non-trivial.

## 2. Branch Strategy

Use a Conventional-Branch-style prefix: **`feat/`** (default), or **`fix/`**, **`chore/`**, **`refactor/`**, **`docs/`**, **`hotfix/`** as appropriate. The implement orchestrator stores the prefix from `forge implement --branch-prefix` (default **feat**).

```
main
 └─ feat/<short-slug>              ← feature branch (created by PM)
     ├─ feat/<short-slug>/task-1   ← sub-branch per task (created by assigned agent)
     ├─ feat/<short-slug>/task-2
     └─ feat/<short-slug>/task-3
```

- Feature branch is created from main before any work begins.
- Each task gets its own sub-branch off the feature branch.
- Sub-branches are merged back to the feature branch in dependency order after review.
- Feature branch is merged to main after all tasks pass verification.
- If parallel tasks touch the same file, the plan must specify merge order and conflict resolution strategy.

## No Placeholders (plan failures)

Never write these in any mode:

- `TBD`, `TODO`, "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases" without specifics
- "Write tests for the above" without actual test description or code
- "Similar to Task N" without repeating needed detail
- Steps that describe what to do without how (verification must name command + expected outcome)

## 3. Task Breakdown

Each task is a discrete unit of work assigned to one agent. Every task must include all of the following fields:

```
### Task [N]: [Title]
**Agent:** [Architect | Dev-1 | Dev-2 | QA | ...]
**Branch:** feat/<short-slug>/task-[N]
**Files:** [Exact file paths to create or modify — no wildcards, no "and related files"]
**Dependencies:** [Task IDs this depends on, or "none"]

**TDD Steps:**
1. Write test: [describe the test — what it asserts, which file]
2. Verify fail: Run test, confirm it fails with [expected error or assertion failure]
3. Implement: [describe the implementation — what to build, which files to modify]
4. Verify pass: Run test, confirm it passes
5. Run full suite: Confirm no regressions

**Acceptance Criteria (done when):**
- [ ] [Observable, verifiable condition]
- [ ] [Observable, verifiable condition]
- [ ] Tests pass (unit + integration if applicable)
- [ ] No regressions in full test suite
```

### Task Breakdown Rules

1. **Exact file paths.** Every task must list the specific files it will create or modify. "Update the auth module" is too vague — list the actual files.
2. **One agent per task.** If a task needs multiple skill sets, split it.
3. **TDD is mandatory.** Every task that changes runtime code must have TDD steps. Config-only or documentation tasks are exempt but must say so explicitly.
4. **Acceptance criteria must be observable.** "Code is clean" is not observable. "Linter passes with zero warnings" is.
5. **No task should take more than ~2 hours of agent work.** If it's bigger, break it down further.
6. **YAGNI on tasks.** No speculative or "future" tasks; no framework-building unless explicitly in scope. Prefer fewer, smaller tasks.
7. **INVEST validation.** Every task must pass the INVEST criteria:
   - **I**ndependent — Can be completed without waiting for other in-progress tasks
   - **N**egotiable — Implementation approach is flexible (not over-specified)
   - **V**aluable — Delivers testable, observable value on its own
   - **E**stimable — Scope is clear enough to estimate effort
   - **S**mall — Fits within ~2 hours (see rule 5)
   - **T**estable — Has concrete acceptance criteria with pass/fail tests

   If a task fails any INVEST criterion, re-split or rewrite it before proceeding.

### Lite mode task format

When **plan mode is `lite`**, keep the same fields but allow shorter narrative. Each task **must** still include:

- **Verify:** `command` → expected: `PASS` | `FAIL with "…"` | observable outcome
- No placeholder steps; split until each task is independently executable

### Default mode task format

When **plan mode is `default`**, expand TDD steps with explicit commands and expected outputs per step (not only "run test").

## 4. Parallelization Map

A table showing which tasks can run in parallel and their dependencies:

| Task | Agent | Depends On | Wave | Can Parallel With |
|------|-------|-----------|------|-------------------|
| Task 1 | Dev-1 | none | 1 | Task 2, Task 3 |
| Task 2 | Dev-2 | none | 1 | Task 1, Task 3 |
| Task 3 | QA | none | 1 | Task 1, Task 2 |
| Task 4 | Dev-1 | Task 1 | 2 | Task 5 |
| Task 5 | Dev-2 | Task 2 | 2 | Task 4 |
| Task 6 | Dev-1 | Task 4, Task 5 | 3 | none |

### Wave Rules

- **Wave 1:** All tasks with no dependencies.
- **Wave N:** Tasks whose dependencies are all in completed waves.
- **Within a wave:** All tasks run in parallel.
- **Between waves:** Wave N+1 starts only after all Wave N tasks are merged and tested.

## 5. Interface Contracts

When tasks have dependencies, the plan must define the interface between them so the downstream task can start coding against a contract before the upstream task is complete.

```
### Contract: [upstream task] → [downstream task]
**Type:** [function signature | API endpoint | data schema | event format]
**Definition:**
[Exact type signature, API spec, or schema — concrete enough to write tests against]

**Example:**
// Task 1 exposes this function for Task 4 to call
export function validateToken(token: string): Promise<{ valid: boolean; userId: string; expires: Date }>
```

### Contract Rules

1. Contracts must be concrete — types, function signatures, or API shapes. "Task 4 will use Task 1's output" is not a contract.
2. Downstream tasks write tests against the contract. If the upstream implementation doesn't match the contract, the upstream task is not done.
3. Contract changes after plan approval require PM sign-off and notification to all affected task agents.

## 6. Risk Register

| Risk | Likelihood (L/M/H) | Impact (L/M/H) | Mitigation |
|------|-------------------|----------------|------------|
| [description] | M | H | [specific mitigation action] |
| [description] | L | H | [specific mitigation action] |

### Risk Register Rules

1. Every plan must identify at least 2 risks. Zero risks means the analysis was insufficient.
2. Mitigations must be specific actions, not "be careful" or "monitor closely."
3. High-likelihood + high-impact risks may warrant plan revision rather than just mitigation.

## 7. Rollback Strategy

What to do if the implementation fails after merge.

### Required Content

- **Rollback trigger:** What conditions indicate rollback is needed (e.g., test failures on main, production errors above threshold).
- **Rollback steps:** Specific commands or procedures — not just "revert the commits."
- **Data migration rollback:** If the change includes data/schema migrations, how to reverse them.
- **Partial rollback:** If only some tasks need reverting, which ones can be reverted independently?
- **Verification after rollback:** How to confirm the rollback succeeded.

```
## Rollback Strategy
**Trigger:** [conditions that require rollback]
**Steps:**
1. [specific command or action]
2. [specific command or action]
**Data rollback:** [migration reversal steps, or "N/A — no data changes"]
**Partial rollback possible:** [yes/no, which tasks are independently revertible]
**Verify:** [how to confirm rollback succeeded]
```

## 8. Documentation

Design documentation **before** implementation. This section is filled during **plan step 6 (Documentation Planning)** and consumed by **implement step 7 (documentation)** and the **step 8 documentation gate**.

### Documentation inventory

List targets you will touch:

- **Tracked markdown/docs:** `README.md`, `docs/**`, `CHANGELOG*`, ADRs, root-level `*.md`.
- **Wiki mirrors (if present):** `wiki/`, `.wiki/`, `docs/wiki/`.
- **External wikis:** systems outside the repo (GitHub Wiki, Confluence, Notion, etc.) — tracked only as checklist rows here.

### Audience applicability matrix (required)

Three audiences — **pick applicability per change** (do not assume all three every time):

| audience_level | applicable | justification |
|----------------|------------|---------------|
| architect_expert | yes / no | Why docs for architects/experts are in or out of scope |
| technical_operator | yes / no | Why runbooks/ops/deploy content is in or out of scope |
| user | yes / no | Why end-user docs are in or out of scope |

Allowed values for `audience_level`: `architect_expert`, `technical_operator`, `user`.

### Documentation Definition of Done (machine-checkable table)

Include one row per documentation target (repo path or external system). Use this schema:

| Field | Meaning |
|-------|---------|
| `audience_level` | One of `architect_expert` \| `technical_operator` \| `user` |
| `applicable` | `true` / `false` — aligns with the applicability matrix |
| `applicability_reason` | Short rationale when `applicable` is `false`, or “matches matrix” when `true` |
| `target_path_or_system` | Repo path (`README.md`, `docs/...`) **or** external system label (`GitHub Wiki`, `Confluence/...`) |
| `change_type` | `create` \| `update` \| `na` |
| `acceptance_check` | Observable check that docs are correct (command, link, or reviewer assertion) |
| `owner` | Role or person |
| `status` | `planned` → becomes `done` during implement documentation phase |
| `evidence` | PR link, commit, path, or placeholder for external wiki |

During implement, agents record completion in `.implement-documentation-gate.json` beside the implement state file (see `prompts/implement/documentation.md`).

### External wiki checklist (required section — may be empty)

If no external wikis apply, state **“None — N/A”** and one matrix row explaining why.

| system | page/slug | owner | status | evidence_link |

### Done criteria for implement

Implement step 8 refuses to complete until documentation artifacts satisfy the gate unless the user passes **`--allow-docs-incomplete`** with override metadata (see README).

## Self-Review Checklist (planner, before review loop)

1. **Spec coverage:** Each requirement in scope maps to at least one task.
2. **Placeholder scan:** Search for forbidden patterns in "No Placeholders" above; fix inline.
3. **Type/signature consistency:** Names and signatures match across tasks and interface contracts.
4. **Verification:** Every task has command + expected outcome.
5. **Mode fit:** `lite` plans are concise but not less correct; `default` plans include full governance depth.
6. **Structural charter:** Tasks respect complexity budgets, avoid planned copy-paste, keep deps acyclic, and do not add speculative exports (`templates/structural-build-charter.md`).

## Rules

1. **No vague tasks.** If a reviewer can't determine exactly what files to change and what tests to write from the task description, it's too vague.
2. **No orphan dependencies.** Every dependency referenced in a task must correspond to another task in the plan.
3. **No circular dependencies.** The dependency graph must be a DAG.
4. **Plans are living documents.** Update the plan when reality diverges. Record what changed and why.
