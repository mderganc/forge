# Phase 3: Test Execution

Run test suites, collect results and metrics.

## Context

**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}
**Discovered suites:** {{TEST_SUITES}}

## Current Results

{{TEST_RESULTS}}

## Your Task

### 1. Execute Tests

Follow the `templates/verification-protocol.md` for structured test execution.

Run the tests in the planned order:
1. **Targeted tests first** (if specific files/areas were identified)
2. **Unit tests** (fast, broad coverage)
3. **Integration tests** (component interactions)
4. **End-to-end tests** (if not in quick mode)

For each test run, capture:
- Command executed
- Exit code
- Number of tests: passed, failed, skipped, errored
- Execution time
- Any warnings or deprecation notices

### 2. Collect Coverage Metrics

If a coverage tool is available:
- Run tests with coverage enabled
- Record overall coverage percentage
- Record per-file coverage
- Identify files with 0% coverage
- Identify files with coverage below project threshold

### 3. Categorize Results

Organize results into:

**Passing tests:** Count and list suites
**Failing tests:** For each failure, record:
- Test name and file
- Error message / assertion failure
- Stack trace
- Whether this is a new failure or pre-existing

**Skipped tests:** Reason for each skip
**Errored tests:** Setup/teardown failures, import errors, etc.

### 4. Update State

Update `state.custom["test_results"]` with:
- `passed`: total passing count
- `failed`: total failing count
- `skipped`: total skipped count
- `total`: total test count
- `coverage_pct`: overall coverage percentage

If there are failures, proceed to failure analysis.
If all tests pass, you may skip step 4 (failure analysis) and proceed to coverage gaps.
