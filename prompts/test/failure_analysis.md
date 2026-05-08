# Phase 4: Failure Analysis

For each test failure, the Investigator performs root-cause analysis.

## Current Results

{{TEST_RESULTS}}

## Current Findings

{{FINDINGS}}

## Your Task

### 1. Triage Failures

Categorize each failure:
- **New failure:** Introduced by recent changes (highest priority)
- **Pre-existing failure:** Failed before recent changes (lower priority)
- **Flaky failure:** Intermittent, may pass on re-run (investigate separately)
- **Environment failure:** Setup, dependency, or configuration issue

### 2. Investigator Root-Cause Analysis

For each **new failure**, the Investigator should:

1. **Read the failing test** — understand what it expects
2. **Read the code under test** — understand what it does
3. **Trace the failure path** — from assertion failure back to root cause
4. **Check recent changes** — did a recent change break this?
5. **Determine root cause:**
   - Logic error in production code?
   - Test needs updating for intentional behavior change?
   - Missing dependency or configuration?
   - Race condition or timing issue?
   - Environment-specific issue?

For each **flaky failure**:
- Re-run the test 2-3 times to confirm flakiness
- Check for timing dependencies, external service calls, shared state

### 3. Create Findings

For each analyzed failure, create a finding:
- **ID:** F{n}
- **Severity:** critical (blocks deployment), warning (should fix), suggestion (improvement)
- **Title:** One-line summary
- **Detail:** Root cause, affected code, and recommended fix
- **Status:** open

### 4. Recommend Fixes

For each finding, suggest a specific fix:
- Code change needed (with file and approximate location)
- Whether the fix is in production code or test code
- Effort estimate (trivial / small / medium / large)

Record all findings and proceed to coverage gap analysis.
