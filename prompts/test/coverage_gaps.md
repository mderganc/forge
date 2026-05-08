# Phase 5: Coverage Gap Analysis

QA Reviewer and Critic identify untested paths and recommend new tests.

## Current Results

{{TEST_RESULTS}}

## Current Findings

{{FINDINGS}}

## Your Task

### 1. QA Reviewer — Coverage Analysis

Analyze the coverage data to identify gaps:

**File-level gaps:**
- Which files have 0% coverage? Are they important?
- Which files are below the project coverage threshold?
- Which recently changed files have inadequate coverage?

**Function-level gaps:**
- Which public functions/methods have no tests?
- Which complex functions (high cyclomatic complexity) lack tests?
- Which error-handling paths are untested?

**Branch-level gaps:**
- Which conditional branches are not exercised?
- Are edge cases tested (null, empty, boundary values)?
- Are error paths tested (exceptions, error returns)?

**Mutation audit (Level 9 from `templates/verification-protocol.md`):**
- For each critical path with high line coverage: mentally mutate the code
- Flip a condition, change a boundary operator, remove a null guard, swap an argument order
- For each mutation: which specific test would catch it?
- If no test would catch a mutation, flag it as a gap — line coverage alone doesn't guarantee behavioral coverage

### 2. Critic — Untested Assumptions

The Critic should identify:

**Missing test categories:**
- Are there any unit test gaps for core business logic?
- Are integration boundaries tested (API calls, DB queries, file I/O)?
- Are authentication and authorization paths tested?
- Are concurrent/parallel code paths tested?

**Test quality issues:**
- Tests that assert too little (always pass)?
- Tests with hardcoded values that should be parameterized?
- Tests that depend on execution order?
- Tests that depend on external state (network, filesystem, time)?

**Recommended new tests:**
For each gap, recommend a specific test:
- Test name/description
- What it should assert
- Which gap it fills
- Priority (high / medium / low)

### 3. Compile Recommendations

Create a prioritized list of recommended new tests:

| Priority | Test Description | Gap Filled | Effort |
|----------|-----------------|------------|--------|
| high | ... | Untested error path in X | small |
| medium | ... | Missing integration test for Y | medium |

Record findings and recommendations, then proceed to the report.
