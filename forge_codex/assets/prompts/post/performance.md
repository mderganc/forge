# Phase 5: Performance Review (Post-Implementation)

You are reviewing the implementation for performance issues and scalability concerns.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Previous Findings

{{PREVIOUS_FINDINGS}}

## Your Task

Read the implemented code and check for:

### 1. Algorithmic Complexity

- Are there O(n^2) or worse patterns where O(n) or O(n log n) is achievable?
- Nested loops over collections that grow with input size?
- Repeated linear scans that could use a lookup table or index?
- Sorting or searching where a more efficient data structure would help?

### 2. N+1 Query Detection

- Database or API calls inside loops (fetch one record per iteration instead of batching)?
- Repeated fetches for the same data without caching the result?
- Missing batch operations where the underlying API supports them?
- ORM lazy-loading that triggers a query per related object?

### 3. Hot Path Analysis

- Are frequently-called code paths optimized? Check request handlers, event loops, and inner loops.
- Unnecessary object allocations on every call (creating objects that could be reused)?
- Redundant computation that could be memoized or cached?
- Missing caching for expensive operations that produce stable results?

### 4. Memory Patterns

- Large objects held in memory longer than needed?
- Unbounded collections that grow without limit (e.g., appending to a list in a long-running process)?
- Missing pagination for large result sets?
- Loading entire files or datasets into memory when streaming would work?

### 5. I/O Efficiency

- Synchronous blocking calls where async is available and appropriate?
- Missing connection pooling for databases, HTTP clients, or other persistent connections?
- Unbatched writes (many small writes instead of fewer large ones)?
- Missing compression for large data transfers?

Focus on issues that matter at realistic scale. Don't flag micro-optimizations that have no measurable impact.

For each issue found, create a finding with the specific file, line, and what the performance concern is.

Severity:
- "critical" — O(n^2+) on unbounded input, N+1 queries in request path, unbounded memory growth
- "warning" — Suboptimal but bounded performance issue, missing caching opportunity on hot path
- "suggestion" — Minor optimization opportunity, premature but worth noting for later

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool:

```json
[
  {"phase": "performance", "severity": "critical|warning|suggestion", "title": "...", "detail": "..."}
]
```

Write `[]` if none.
