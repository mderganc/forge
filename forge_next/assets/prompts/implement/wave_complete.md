# Phase 5: Wave Completion

Complete Wave {{CURRENT_WAVE}} and prepare for next.

## Merge Protocol

For each task sub-branch (in dependency order):

1. `git checkout {{FEATURE_BRANCH_PATTERN}}`
2. `git merge {{TASK_BRANCH_PATTERN}} --no-ff`
3. Run full test suite after each merge
4. If conflict: assign to owning agent, critic reviews resolution
5. If tests fail: assign to responsible agent, fix before next merge

Branch guardrail: merge only branches that match the configured conventional prefix; never create or merge `forge/*` branches.

## Wave Status

Waves completed: {{WAVES_COMPLETED}} of {{TOTAL_WAVES}}

## Wave Summary

Record in `{{MEMORY_DIR}}/project.md`:

```
## Wave {{CURRENT_WAVE}} -- Complete
- Tasks merged: [list]
- Test suite: [N passed, 0 failed]
- Open issues: [none | list]
```

## Next

{{NEXT_WAVE_OR_PROCEED}}
