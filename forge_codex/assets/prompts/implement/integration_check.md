# Phase 6: Integration Verification

All waves are complete. Verify that the combined implementation works as a whole.

Dispatch QA Reviewer (lead) + Critic, following `templates/review-loop.md`.

## Verification Areas

### 1. Dependency Impact Analysis

Map all files changed across all waves. For each changed file:

- Use Grep to identify all importers, callers, and consumers of the changed code
- Verify every consumer still works correctly with the changes
- Flag any consumer that is not covered by existing tests

Pay special attention to:
- Shared utilities modified in one wave but consumed in another
- Data models or schemas changed in ways that affect downstream code
- Configuration changes that affect multiple components

### 2. Cross-Wave Interface Verification

- Do components built in different waves connect correctly?
- Function signatures match at wave boundaries? (caller in wave 1, callee in wave 2)
- Data flows work end-to-end across wave boundaries?
- Run the full test suite as a cross-wave integration check. All tests must pass.

### 3. Architectural Fitness

- No circular imports introduced across wave boundaries
- Dependency direction rules respected (e.g., core modules don't import from adapter layers, data layer doesn't import from presentation)
- Layer separation maintained — no cross-cutting concerns leaked across module boundaries
- Module cohesion preserved — related code stays together, unrelated code stays apart

Use Grep to check import patterns across the changed files.

### 4. Regression + Performance Integration

- Full test suite passes after all wave merges
- Smoke test the golden path end-to-end (the primary user workflow this implementation supports)
- Combined system performance is acceptable — no compounding latency from incremental additions across waves
- No test flakiness introduced (run tests twice if any failures look intermittent)

## Output

For each issue found, create a finding per `templates/review-loop.md` format.

Severity:
- FAIL — Cross-wave interface broken, circular dependency introduced, tests failing after merge
- WARN — Consumer not covered by tests, potential performance regression, architectural rule bent
- PASS — Area verified clean

If all areas pass, record PASS and proceed to Documentation.
If FAIL findings exist, route to the responsible wave's developer for remediation before proceeding.
