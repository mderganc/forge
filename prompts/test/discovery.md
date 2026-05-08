# Phase 2: Test Discovery

QA Reviewer identifies all test suites, coverage tools, and relevant test paths.

## Context

**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}
**Known test suites:** {{TEST_SUITES}}

## Your Task

### 1. Discover Test Suites

The QA Reviewer should identify all test suites in the project:

- **Unit tests:** Tests for individual functions/classes/modules
- **Integration tests:** Tests for component interactions
- **End-to-end tests:** Tests for full user workflows
- **Performance tests:** Benchmarks if they exist
- **Property-based tests:** Fuzzing or property testing if configured

For each suite found, record:
- Suite name and location
- How to run it (command)
- Estimated run time (if known)
- What it covers

### 2. Identify Coverage Tools

Check for coverage configuration:
- Python: `coverage`, `pytest-cov`, `.coveragerc`
- JavaScript: `istanbul`, `c8`, `jest --coverage`
- Go: `go test -cover`
- Other: look for coverage-related config files

### 3. Plan Test Execution

Based on the scope and target:

**If targeted (from handoff or user argument):**
- Identify the specific test files/suites for the changed areas
- Plan to run those first, then the full suite for regression

**If full suite:**
- Plan execution order: fast unit tests first, then integration, then e2e
- Identify any tests that can run in parallel

**If quick mode:**
- Run only the most relevant tests for the changed areas
- Skip long-running integration/e2e tests unless directly relevant

### 4. Record Discoveries

Update the state with:
- List of discovered test suites
- Recommended execution order
- Expected coverage targets

Proceed to test execution.
