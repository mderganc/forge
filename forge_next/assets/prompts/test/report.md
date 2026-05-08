# Phase 6: Report

Write the final test report and hand off to the next skill.

## Test Summary

**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Results

{{TEST_RESULTS}}

## Findings

{{FINDINGS}}

## Your Task

### 1. Write the Test Report

Write the report to `.codex/forge-codex/memory/test-report.md` with this structure:

- **Summary:** total tests, pass/fail/skip counts, coverage percentage
- **Results table:** each test suite with its pass/fail/skip counts
- **Failures:** detailed failure descriptions with root cause analysis
- **Coverage:** per-file coverage breakdown, files below threshold
- **Gaps:** recommended new tests with priority
- **Recommendations:** overall testing improvements

### 2. Update Memory

- Update `.codex/forge-codex/memory/project.md` with test completion status
- Record pass/fail counts and coverage metrics

### 3. Prepare Handoff

The handoff file will be written automatically with test results context.

If there are failures:
- The handoff will suggest `diagnose` as the next step
- Include failure details so diagnose can start immediately

If all tests pass:
- The handoff will indicate the flow is complete
- Note any coverage gaps for future work

### 4. Present Dashboard

Show the user:
- Pass/fail/skip summary
- Coverage percentage
- Open findings count
- Suggested next step
