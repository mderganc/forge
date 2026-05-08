# TDD Protocol

Used by the implement skill and dev agents. Defines the test-driven development discipline required for all implementation tasks.

## Core Principle

> Write the test first. Watch it fail. Write the minimum code to make it pass. Then clean up. No exceptions.

## The Red-Green-Refactor Cycle

Every unit of implementation follows this cycle:

### Step 1: RED — Write the Failing Test

Write a test that describes the desired behavior. Run it. It must fail.

```
Action: Write test in [test file]
Run: [test command]
Expected: FAIL — [describe the expected failure]
Actual: [paste actual test output]
```

**Critical check:** The test must fail for the **right reason**. Acceptable failures:
- Assertion failure (expected value doesn't match)
- Function/class/module not found (it doesn't exist yet)
- Method not implemented (returns wrong value or throws "not implemented")

**Unacceptable failures** (fix these before proceeding):
- Syntax error in the test itself
- Import error for an existing module (typo, wrong path)
- Test framework configuration error
- Timeout or environment issue

If the test passes immediately, either the behavior already exists (no implementation needed) or the test is wrong.

### Step 2: GREEN — Write the Minimum Implementation

Write just enough code to make the failing test pass. No more.

```
Action: Implement in [source file]
Run: [test command]
Expected: PASS
Actual: [paste actual test output]
```

**Minimum implementation means:**
- If the test expects a function to return `42`, it's valid to write `return 42` at this stage.
- Don't add error handling, edge cases, or optimizations that aren't tested yet.
- The next Red phase will drive those additions.

### Step 3: REFACTOR — Clean Up

With the test green, improve the code without changing behavior:

- Remove duplication.
- Improve naming.
- Extract functions/methods if too long.
- Simplify logic.

```
Action: Refactor [describe what was cleaned up]
Run: [test command]
Expected: PASS (still)
Actual: [paste actual test output]
```

### Step 4: REGRESSION CHECK — Run Full Suite

After each Red-Green-Refactor cycle, run the full test suite.

```
Run: [full test suite command]
Expected: All tests pass
Actual: [summary — N passed, M failed, K skipped]
```

If any existing test fails, fix the regression before starting the next cycle. The new code broke something — this is the most important signal TDD provides.

## Test Naming Conventions

Tests should read as behavior specifications. Name them to describe **what the system does**, not how it's implemented.

**Good:**
- `test_login_returns_token_for_valid_credentials`
- `test_login_rejects_expired_password`
- `test_upload_limits_file_size_to_10mb`
- `should return 404 when user does not exist`

**Bad:**
- `test_login` (too vague)
- `test_function_calls_database` (tests implementation, not behavior)
- `test1`, `test2` (meaningless)

## Edge Case Identification

Before writing tests, work through this checklist to identify edge cases. Not every item applies to every feature — skip inapplicable items.

| Category | Cases to Consider |
|----------|------------------|
| **Empty inputs** | Empty string, empty array, empty object, null, undefined |
| **Boundary values** | Zero, one, max int, max length, off-by-one |
| **Type edge cases** | Negative numbers, floating point precision, Unicode, very long strings |
| **Null / undefined** | Missing optional fields, null where object expected, undefined properties |
| **Concurrent access** | Simultaneous reads, simultaneous writes, read-during-write |
| **Large data** | Input at or beyond expected scale — 1M rows, 100MB payload |
| **Error paths** | Network failure, disk full, permission denied, timeout |
| **State transitions** | Uninitialized → initialized, valid → invalid, retry after failure |

Write a test for every applicable edge case. Each edge case is its own Red-Green-Refactor cycle.

## Equivalence Partitioning & Boundary Value Analysis

Before writing edge case tests, systematically derive test cases from input domains. This replaces ad-hoc edge case guessing with formal test design.

### Equivalence Partitioning

For each input parameter, identify **equivalence classes** — groups of inputs that should be treated identically by the code:

1. **Valid classes:** Groups of valid inputs (e.g., positive integers, valid email formats, in-range dates)
2. **Invalid classes:** Groups of invalid inputs (e.g., negative numbers, empty strings, null)
3. **Special classes:** Inputs with special handling (e.g., zero, admin users, default values)

Write **one test per equivalence class**. If a test passes for one value in the class, it should pass for all values in that class.

### Boundary Value Analysis

For each equivalence class boundary, test:
- The value **at** the boundary
- The value **just inside** the boundary
- The value **just outside** the boundary

Example: if valid range is 1-100:
- Test 0 (just below), 1 (at boundary), 2 (just inside)
- Test 99 (just inside), 100 (at boundary), 101 (just above)

## Property-Based Testing

After specific test cases, identify **invariants** — properties that must hold for ALL valid inputs, not just the specific cases you tested.

### How to Identify Properties

Ask:
- "What must ALWAYS be true about the output, regardless of input?" (e.g., sorted output is same length as input)
- "What relationship exists between input and output?" (e.g., encoding then decoding returns original)
- "What should NEVER happen?" (e.g., balance never goes negative, no duplicate IDs)

### Writing Property Tests

If the project has a property-based testing framework (Hypothesis for Python, fast-check for JS, QuickCheck for Haskell):

```
# Python with Hypothesis
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_preserves_length(xs):
    assert len(sorted(xs)) == len(xs)

@given(st.text())
def test_encode_decode_roundtrip(s):
    assert decode(encode(s)) == s
```

If no framework is available, write at least one property test manually with a loop over representative inputs.

### When to Use Property-Based Testing

- Functions with clear input/output contracts (serialization, parsing, math)
- Functions that must preserve invariants (collections, state machines)
- Functions where edge cases are hard to enumerate (string processing, date math)

## Unit Tests vs Integration Tests

| Write a Unit Test When | Write an Integration Test When |
|----------------------|------------------------------|
| Testing a single function's logic | Testing interaction between modules |
| Testing pure computation | Testing database queries with real/test DB |
| Testing input validation | Testing API endpoints end-to-end |
| Testing error handling branches | Testing authentication/authorization flow |
| Fast feedback needed | Testing file system or network I/O |

**Default to unit tests.** They're faster, more reliable, and easier to debug. Write integration tests when the interaction between components is the thing being tested.

## TDD Session Log

Each TDD session produces a log that goes into the task's review:

```
## TDD Log — Task [N]

### Cycle 1: [behavior being implemented]
- RED: Wrote test `test_name` — FAIL (function not found) ✓
- GREEN: Implemented `function_name` — PASS ✓
- REFACTOR: Extracted helper `helper_name` — PASS ✓
- REGRESSION: Full suite 47/47 passed ✓

### Cycle 2: [next behavior]
- RED: Wrote test `test_name` — FAIL (assertion: expected 200, got null) ✓
- GREEN: Added return value — PASS ✓
- REFACTOR: None needed
- REGRESSION: Full suite 48/48 passed ✓
```

## Rules

1. **Never write implementation before the test.** If you catch yourself implementing first, stop, delete the implementation, write the test.
2. **Never skip the RED step.** If you can't make the test fail, the test isn't testing new behavior.
3. **Never skip the regression check.** It's the safety net that makes TDD sustainable.
4. **One behavior per cycle.** Don't write 10 tests then implement everything at once. One test, one implementation, one refactor.
5. **Tests are production code.** Apply the same quality standards to test code — readable, maintainable, no duplication.
6. **If the existing project has no tests,** create the test infrastructure (test directory, config, runner) as the first task before any TDD cycles.
