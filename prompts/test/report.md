# Phase 6: Report

Write the final test report and hand off to the next skill.

## Test Summary

**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Results

{{TEST_RESULTS}}

## Orchestrator test execution (step 3)

The orchestrator runs pytest at step 3 unless `FORGE_SKIP_TEST_AUTO_RUN=1`. Include this block verbatim in the written report:

{{TEST_EXECUTION_LOG}}

## Findings

{{FINDINGS}}

## Your Task

### 1. Write the Test Report

Write the report to `{{MEMORY_DIR}}/test-report.md` with this structure:

- **Summary:** total tests, pass/fail/skip counts, coverage percentage
- **Results table:** each test suite with its pass/fail/skip counts
- **Failures:** detailed failure descriptions with root cause analysis
- **Coverage:** per-file coverage breakdown, files below threshold
- **Gaps:** recommended new tests with priority
- **Recommendations:** overall testing improvements
- **Orchestrator execution:** copy the "Orchestrator test execution" section above (command, exit code, counts, output tail)
- **Workflow prompts:** copy the appendix below — full verbatim prompts from each test step

{{WORKFLOW_PROMPTS_APPENDIX}}

### 2. Update Memory

- Update `{{MEMORY_DIR}}/project.md` with test completion status
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
