# Phase 2: Completeness Audit (Post-Implementation)

You are auditing whether the plan was fully implemented.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Your Task

Go through each step in the plan systematically:

1. **Read the plan step** — What was supposed to happen?
2. **Read the actual code** — Use Read, Grep, and Glob to find the implementation.
3. **Compare:**
   - COMPLETE — Step was fully implemented as described
   - PARTIAL — Step was started but incomplete or modified
   - MISSING — Step was not implemented at all
   - EXTRA — Implementation includes work not in the plan

For each PARTIAL or MISSING item, create a finding with:
- What was planned
- What was actually done (or not done)
- Whether this matters (some plan deviations are improvements)

Severity:
- "critical" — Core functionality is missing
- "warning" — Partial implementation that may cause issues
- "suggestion" — Minor omission or acceptable deviation

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool:

```json
[
  {"phase": "completeness_audit", "severity": "critical|warning|suggestion", "title": "...", "detail": "..."}
]
```

Write `[]` if none.
