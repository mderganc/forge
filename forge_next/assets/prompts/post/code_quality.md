# Phase 4: Code Quality Review (Post-Implementation)

You are reviewing the implementation for structural quality.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Previous Findings

{{PREVIOUS_FINDINGS}}

## Your Task

Review the implemented code for:

1. **Structure:** Are files and functions well-organized? Is each function doing one thing? Are there functions that are too long or too complex?
2. **Naming:** Are variables, functions, and classes named clearly? Would a new reader understand what they do?
3. **Duplication:** Is there repeated code that should be extracted? Are there near-identical blocks that differ in small ways?
4. **Dead code:** Are there unused imports, unreachable branches, commented-out code, or vestigial functions?
5. **Test quality:** Do tests exist? Do they test behavior (not implementation details)? Are edge cases covered? Are test names descriptive?
6. **Performance anti-patterns:** Are there N+1 queries (database calls inside loops)? String concatenation in tight loops instead of join/builder? Redundant serialization/deserialization cycles? Unnecessary deep copies where shallow copies or references suffice?

Focus on issues that matter — things that would make the code harder to maintain, extend, or debug. Do not flag style preferences or minor formatting issues.

Severity:
- "critical" — Major structural problem (e.g., untested critical path, massive function)
- "warning" — Should be cleaned up (e.g., duplication, unclear naming)
- "suggestion" — Nice to have (e.g., could extract a helper)

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool:

```json
[
  {"phase": "code_quality", "severity": "critical|warning|suggestion", "title": "...", "detail": "..."}
]
```

Write `[]` if none.
