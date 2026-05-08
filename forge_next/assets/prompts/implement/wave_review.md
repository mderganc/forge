# Phase 4: Wave Review

Run per-task review loop for Wave {{CURRENT_WAVE}} tasks.

## Review Protocol

For each completed task in Wave {{CURRENT_WAVE}}:

| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Implementing Dev | Match plan? TDD followed? Tests pass? |
| Cross-review | QA Reviewer | Edge cases? Test quality? Coverage? |
| Critic challenge | Critic | Production failure? Untested assumptions? |
| PM validation | PM | Plan adherence? Beads updated? Memory current? |

Per `templates/review-loop.md`, loop until clean.
Record findings in respective memory files.

## Review Checklist per Task

- [ ] Implementation matches plan specification
- [ ] TDD log shows proper Red-Green-Refactor cycles
- [ ] All new tests pass
- [ ] Full test suite passes (no regressions)
- [ ] Code follows project conventions
- [ ] No hardcoded values, secrets, or debug artifacts
- [ ] Beads updated (if available)
- [ ] Memory file updated with task status

### Performance & Efficiency
- [ ] No N+1 queries or database calls inside loops
- [ ] No O(n^2+) algorithms on unbounded inputs
- [ ] Hot paths avoid unnecessary allocations or redundant computation

### Mutation Testing Audit
- [ ] For each critical function: mentally mutate the code (flip a condition, remove a line, change an operator) — verify an existing test would catch each mutation
- [ ] If a mutation would pass undetected, write a test that catches it before proceeding
- [ ] Focus on decision points and boundary conditions — mutations there are highest-value

### Backward Compatibility
- [ ] Public function signatures unchanged (or all callers updated)
- [ ] Data format changes are backward-compatible (or migration provided)
- [ ] Config schema changes have defaults for existing installations
- [ ] No silent behavior changes in shared utilities

### Operational Readiness
- [ ] Error paths produce meaningful messages (no swallowed exceptions)
- [ ] Key decision points and state transitions are logged
- [ ] Resources (files, connections, temp files) properly cleaned up
- [ ] No sensitive data in logs or error messages

### Risk
- [ ] Rollback-safe: changes can be reverted without data loss
- [ ] No implicit dependencies on execution order of other wave tasks

## Quick Mode

{{QUICK_MODE_NOTE}}
