# Phase 3: Correctness Review (Post-Implementation)

You are verifying that the implementation does what the plan intended.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Previous Findings

{{PREVIOUS_FINDINGS}}

## Your Task

For each implemented component:

1. **Read the actual code** carefully.
2. **Trace the logic** — Does it produce the correct output for expected inputs?
3. **Check for common errors:**
   - Off-by-one errors in loops or slicing
   - Wrong comparison operators (< vs <=, == vs is)
   - Missing null/None checks where data could be absent
   - Incorrect string formatting or regex patterns
   - Wrong variable used (copy-paste errors)
   - Logic inversions (condition should be negated)
4. **Check concurrency correctness:**
   - Race conditions in shared state access?
   - Missing locks, atomics, or synchronization for concurrent access?
   - Unsafe concurrent collection modification?
   - Async/await pitfalls: missing await, fire-and-forget without error handling, deadlock potential?
5. **Check resource lifecycle:**
   - Are resources acquired and released in the correct order?
   - Are there code paths that skip cleanup (early returns, exceptions before cleanup)?
6. **Verify against the plan** — Does the code do what the plan says it should?

For each issue found, create a finding with the specific file, line, and what is wrong.
Severity:
- "critical" — Will produce wrong results or crash
- "warning" — Could cause issues in some cases
- "suggestion" — Works but could be clearer or more robust

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool:

```json
[
  {"phase": "correctness", "severity": "critical|warning|suggestion", "title": "...", "detail": "..."}
]
```

Write `[]` if none.
