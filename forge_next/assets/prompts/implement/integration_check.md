# Phase 6: Integration Verification

All waves are complete. Verify that the combined implementation works as a whole.

Dispatch QA Reviewer (lead) + Critic, following `templates/review-loop.md`.
Scale by overall plan **Size** (`templates/scope-size-model.md`).

## Size → integration depth

| Size | Consumer / impact analysis | Test run |
|------|----------------------------|----------|
| **small** | **Targeted** — importers of the few changed symbols only (no exhaustive repo-wide consumer grep) | Targeted suite for touched modules + one golden-path smoke if user-facing |
| **medium** | Grep consumers of changed public APIs / shared modules | Full suite preferred; at least integration + regression for touched areas |
| **large** | Full dependency impact across all changed files | Full suite mandatory; run twice if flaky-looking failures |

## Verification Areas

### 1. Dependency Impact Analysis

Map files changed across waves. Scope the analysis to the size row above.

- Identify importers, callers, and consumers of the **changed** code (small: only direct consumers of edited symbols)
- Verify every **in-scope** consumer still works with the changes
- Flag any in-scope consumer that is not covered by existing tests

Pay special attention to:
- Shared utilities modified in one wave but consumed in another
- Data models or schemas changed in ways that affect downstream code
- Configuration changes that affect multiple components

### 2. Cross-Wave Interface Verification

- Do components built in different waves connect correctly? *(single-wave / single-task: treat as N/A with one-line note)*
- Function signatures match at wave boundaries? (caller in wave 1, callee in wave 2)
- Data flows work end-to-end across wave boundaries?
- Watch for cross-task **cycles** and duplicate shapes that should be shared (`templates/structural-build-charter.md`)
- Run the integration test command appropriate to size (see table). All required tests must pass.

### 3. Architectural Fitness *(medium/large; light touch for small)*

- No circular imports introduced across wave boundaries
- Dependency direction rules respected (e.g., core modules don't import from adapter layers, data layer doesn't import from presentation)
- Layer separation maintained — no cross-cutting concerns leaked across module boundaries
- Module cohesion preserved — related code stays together, unrelated code stays apart

Use Grep on **changed** import surfaces (small: skip repo-wide import archaeology).

### 4. Regression + Performance Integration

- Required suite for size passes after all wave merges
- Smoke test the golden path end-to-end when the change is user-facing
- Combined system performance is acceptable — *skip deep perf for small unless the task was performance-scoped*
- No test flakiness introduced (run tests twice if any failures look intermittent) — *large / flaky-suspect only*

## Output

For each issue found, create a finding per `templates/review-loop.md` format.

Severity:
- FAIL — Cross-wave interface broken, circular dependency introduced, tests failing after merge
- WARN — Consumer not covered by tests, potential performance regression, architectural rule bent
- PASS — Area verified clean

If all areas pass, record PASS and proceed to Documentation.
If FAIL findings exist, route to the responsible wave's developer for remediation before proceeding.
