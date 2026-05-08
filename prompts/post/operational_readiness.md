# Phase 6: Operational Readiness (Post-Implementation)

You are verifying that the implementation is ready for production operation.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Previous Findings

{{PREVIOUS_FINDINGS}}

## Your Task

Review the implemented code for production readiness:

### 1. Error Handling Completeness

- Are all error paths handled? Follow each code path that can fail — does it surface a meaningful error or silently swallow the exception?
- Are error messages actionable? Could an operator diagnose the problem from the error alone?
- No bare `except:` or `catch(e)` that swallows errors without logging or re-raising?
- External calls (APIs, databases, file I/O) have appropriate retry logic or fallback behavior?
- Error responses include enough context to debug but no sensitive internal details?

### 2. Logging Adequacy

- Could you debug a production issue from logs alone, without attaching a debugger?
- Are key decision points logged? (e.g., "Chose path A because condition X was true")
- Are state transitions logged? (e.g., "Order status changed from pending to processing")
- Are log levels appropriate? (DEBUG for verbose detail, INFO for normal operations, WARN for recoverable issues, ERROR for failures)
- No sensitive data in logs — no passwords, tokens, PII, or full request bodies containing secrets?

### 3. Resource Management

- Are file handles, database connections, network sockets, and temp files properly cleaned up?
- Are there `finally`/`with`/`defer`/`using` blocks where needed to guarantee cleanup on error paths?
- Are connection pools configured with reasonable limits?
- Are temporary resources cleaned up even when exceptions occur mid-operation?

### 4. Deployment Readiness

- Are all required configuration changes documented? (environment variables, config files, feature flags)
- Are database migrations present, tested, and reversible?
- Are feature flags in place for gradual rollout of risky changes?
- Are there any hardcoded values that should be configurable? (URLs, timeouts, limits, thresholds)

### 5. Graceful Degradation

- Does the system handle downstream service failures without cascading? (e.g., if a cache is down, does it fall back to the database?)
- Are there timeouts on all external calls? (HTTP requests, database queries, file operations on network drives)
- Are circuit breaker patterns used where appropriate for unreliable dependencies?
- Can the system start up and shut down cleanly? Are there initialization and cleanup hooks?

Focus on issues that would cause production incidents or make them harder to diagnose. Don't flag theoretical concerns that don't apply to this codebase's operational context.

For each issue found, create a finding with the specific file, line, and what the operational concern is.

Severity:
- "critical" — Swallowed exceptions hiding failures, resource leaks in request path, missing migration for schema change
- "warning" — Insufficient logging for new code path, missing cleanup in error edge case, no timeout on external call
- "suggestion" — Could add structured logging, could improve error message clarity, nice-to-have monitoring hook

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool:

```json
[
  {"phase": "operational_readiness", "severity": "critical|warning|suggestion", "title": "...", "detail": "..."}
]
```

Write `[]` if none.
