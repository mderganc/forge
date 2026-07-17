# Phase 3: Completeness Analysis (Pre-Implementation)

You are checking whether the plan covers everything it needs to.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Previous Findings

{{PREVIOUS_FINDINGS}}

## Structural focus (this step)
Does the plan encode charter Verify steps and avoid complexity/clone/cycle/speculative-export debt? Flag gaps where tasks would grow hot functions, copy logic, create cycles, or add unused public surfaces. See `templates/structural-build-charter.md`.

## Your Task

Look for gaps in the plan:

1. **Error handling:** Does the plan address what happens when things go wrong? Missing try/catch, missing validation, unhandled edge cases?
2. **Edge cases:** What inputs, states, or conditions could break the planned implementation? Empty inputs, concurrent access, large data, missing files?
3. **Unstated assumptions:** What does the plan take for granted that might not be true? Does it assume certain data shapes, API behaviors, or system states?
4. **Test coverage:** Does the plan include tests? Do the tests cover the interesting cases or just the happy path?
5. **Missing steps:** Are there steps that logically need to happen but aren't in the plan? Migrations, config changes, documentation updates?
6. **Operational requirements:** Does the plan account for logging, monitoring, and alerting needs? Are there observability gaps for new code paths that would make production debugging difficult?
7. **Deployment steps:** Are there missing deployment-related steps? Environment variables, feature flags, config changes, database migrations, cache invalidation?

For each gap found, create a finding with severity:
- "critical" — Will cause failures if not addressed
- "warning" — Should be addressed but won't break things
- "suggestion" — Would improve the plan but not required

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool:

```json
[
  {"phase": "completeness", "severity": "critical|warning|suggestion", "title": "...", "detail": "..."}
]
```

Write `[]` if you have no findings — the orchestrator uses presence of this file to confirm the step ran.
