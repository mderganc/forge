# Phase 2: Feasibility Analysis (Pre-Implementation)

You are evaluating whether this plan can be implemented as described.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Your Task

For each significant step in the plan:

1. **Read the relevant existing code** using Read, Grep, and Glob tools.
2. **Assess feasibility:**
   - Can this step be done as described?
   - Are there technical blockers (missing APIs, incompatible data structures, etc.)?
   - Are there missing dependencies that the plan doesn't mention?
   - Does the plan underestimate the complexity of any step?
3. **Check performance feasibility:**
   - Will any step hit performance walls? (e.g., full-table scans on large tables, O(n^2) algorithms on large inputs, synchronous calls to slow external services)
   - Are there resource constraints that could block implementation? (memory limits, disk space, network bandwidth, API rate limits)
4. **Rate each step:** FEASIBLE / RISKY / BLOCKED

For each RISKY or BLOCKED item, create a finding with:
- A clear title describing the issue
- Detail explaining what the blocker is and why
- Severity: "critical" for BLOCKED, "warning" for RISKY

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool. The orchestrator will ingest this file on the next step and the discussion phase will surface each finding with an ID.

```json
[
  {
    "phase": "feasibility",
    "severity": "critical",
    "title": "Short title describing the issue",
    "detail": "Full explanation of what's wrong and why."
  }
]
```

Severities: `critical`, `warning`, `suggestion`. If you have no findings to record, write an empty array `[]` so the sidecar is created and the orchestrator knows you ran.
