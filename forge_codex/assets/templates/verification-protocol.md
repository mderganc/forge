# Verification Protocol

Used by the test skill and evaluate review mode. Defines the validation ladder and Swiss Cheese defense layers that must be executed before any work is considered complete.

## Core Principle

> A fix that isn't verified is a hypothesis. Verification transforms a hypothesis into a fact.

## Validation Ladder

Eight levels of verification. Execute every applicable level. Skip a level only if it is genuinely not applicable — and document why.

### Level 1: Unit Tests

- Run unit tests for the modified module.
- Confirm new tests exist for the changed behavior.
- Confirm tests are meaningful (not just `assert True`).

```
Result: [N passed, M failed] — [pass/fail]
```

### Level 2: Integration Tests

- Run integration tests if the project has them.
- If the change affects cross-module interaction, integration tests are mandatory.
- If no integration tests exist and the change is cross-module, flag this as a gap.

```
Result: [N passed, M failed] — [pass/fail]
Skip reason: [if skipped — e.g., "project has no integration tests"]
```

### Level 3: Regression (Full Test Suite)

- Run the complete test suite across the entire project.
- Any new failure is a regression caused by this change until proven otherwise.

```
Result: [N passed, M failed, K skipped] — [pass/fail]
New failures: [none | list with investigation notes]
```

### Level 4: Reproduction

- Re-run the original reproduction case from the investigation.
- Confirm the original bug no longer triggers.
- For feature work: confirm the feature's primary use case works end-to-end.

```
Repro steps: [from investigation or plan]
Expected: [correct behavior]
Actual: [observed behavior]
Result: [pass/fail]
Skip reason: [if skipped — e.g., "new feature, no prior bug to reproduce"]
```

### Level 5: Static Analysis

- Run the project's linter with existing configuration.
- Run the type checker if the project uses one.
- Run SAST tools if configured.
- No new warnings or errors introduced by this change.

```
Linter: [tool] — [pass/fail, N warnings]
Type checker: [tool] — [pass/fail]
SAST: [tool] — [pass/fail]
Skip reason: [if any tool skipped — e.g., "no SAST configured"]
```

### Level 6: Performance

- Applicable when the change is performance-related, touches hot paths, or modifies data structures.
- Run benchmarks if they exist.
- If no benchmarks exist and performance matters, create a simple before/after measurement.

```
Benchmark: [tool/method]
Before: [measurement]
After: [measurement]
Verdict: [acceptable/regression]
Skip reason: [if skipped — e.g., "change is UI-only, no performance impact"]
```

### Level 7: Edge Cases

- Test boundary conditions identified during implementation (from `templates/tdd-protocol.md` edge case checklist).
- Confirm edge case tests exist and pass.

```
Edge cases tested:
- [case]: [pass/fail]
- [case]: [pass/fail]
Skip reason: [if skipped]
```

### Level 8: Adversarial

- Applicable for security-sensitive, data-handling, or input-processing changes.
- Try to break the implementation with unexpected, malformed, or malicious inputs.
- Test: SQL injection, XSS, path traversal, oversized inputs, null bytes, Unicode edge cases — whichever apply.

```
Adversarial tests:
- [attack vector]: [result]
- [attack vector]: [result]
Skip reason: [if skipped — e.g., "change is internal refactor, no user-facing input"]
```

### Level 9: Mutation Audit

- Applicable for critical code paths, especially those with high line coverage but uncertain behavioral coverage.
- For each critical function or conditional: mentally "mutate" the code (flip a condition, change an operator, remove a null check, swap a boundary) and ask: "Which specific test would catch this mutation?"
- If no test would catch a mutation, that's a **coverage gap** even if line coverage is 100%.

```
Mutation audit:
- [location]: [mutation] → caught by [test name] | NOT CAUGHT — gap
- [location]: [mutation] → caught by [test name] | NOT CAUGHT — gap
Skip reason: [if skipped — e.g., "trivial code with no conditionals"]
```

## Validation Ladder Summary

After executing all levels, produce a summary:

```
## Validation Ladder Summary
| Level | Status | Notes |
|-------|--------|-------|
| 1. Unit tests | PASS | 23/23 passed |
| 2. Integration tests | PASS | 8/8 passed |
| 3. Regression | PASS | 142/142 passed |
| 4. Reproduction | PASS | Original bug no longer triggers |
| 5. Static analysis | PASS | Linter clean, types clean |
| 6. Performance | SKIP | Not performance-related |
| 7. Edge cases | PASS | 5 edge case tests added and passing |
| 8. Adversarial | SKIP | Internal refactor, no user input |
| 9. Mutation audit | PASS | 3 critical mutations, all caught |

**Levels executed:** 7/9
**Levels passed:** 7/7
**Verdict:** VERIFIED
```

## Swiss Cheese Verification

Multiple defense layers, like slices of Swiss cheese — each has holes, but stacked together they catch what individual layers miss.

### Defense Layers

| Layer | Check | Question |
|-------|-------|----------|
| Layer 1: Code correctness | Fix applied correctly | Does the code change actually address the root cause? |
| Layer 2: Type system / linter | Static catches | Would the type system or linter catch this class of bug? |
| Layer 3: Unit tests | Test coverage | Is there a test that would fail if this bug were reintroduced? |
| Layer 4: Integration tests | Cross-module coverage | Is the interaction path tested end-to-end? |
| Layer 5: Monitoring / alerting | Runtime detection | Would monitoring detect if this bug recurred in production? |
| Layer 6: Code review checks | Human/agent review | Would a reviewer catch this class of issue? |

### Swiss Cheese Assessment

For each layer, record whether it covers this specific change:

```
## Swiss Cheese Assessment
- Layer 1 (Code correctness): YES — fix directly addresses root cause
- Layer 2 (Type system): YES — added type annotation that would catch wrong type
- Layer 3 (Unit tests): YES — regression test added
- Layer 4 (Integration tests): NO — no integration test covers this path
- Layer 5 (Monitoring): NO — no alerting for this error class
- Layer 6 (Code review): YES — added to review checklist

**Layers verified:** 4/6
```

### Coverage Rule

**If fewer than 3 layers are verified, recommend adding more defenses.** Specifically:

- If Layer 3 (unit test) is missing → add a regression test. This is the minimum bar.
- If Layer 2 (type/lint) is missing → consider if a type annotation or lint rule could catch the class of bug.
- If Layer 5 (monitoring) is missing → flag for ops team awareness (not blocking, but recorded).

## Acceptance Criteria Checklist

Pull the acceptance criteria from the plan or task description and verify each one:

```
## Acceptance Criteria
- [ ] [criterion from plan] — VERIFIED: [evidence]
- [ ] [criterion from plan] — VERIFIED: [evidence]
- [ ] Tests pass — VERIFIED: [test suite output summary]
- [ ] No regressions — VERIFIED: [full suite output summary]
```

Every criterion must have evidence. "Looks good" is not evidence.

## Rollback Verification

Confirm the rollback strategy from the plan is still viable:

- [ ] Rollback steps are still accurate (no new dependencies or data changes that invalidate them).
- [ ] If data migrations were applied, reversal was tested or confirmed reversible.
- [ ] Rollback trigger conditions are documented.

```
Rollback viable: [yes/no]
Notes: [any changes to rollback strategy needed]
```

## Rules

1. **No level is optional by default.** Every level is assumed applicable unless explicitly skipped with documented reason.
2. **Skipping a level is not failing it.** A skipped level with valid reason is fine. A failed level is a blocker.
3. **Verification must use actual commands and actual output.** "I checked and it looks fine" is not verification.
4. **The Validation Ladder Summary is required.** It goes into the review and the handoff file.
5. **Swiss Cheese assessment is required for bugfix tasks.** For features, it's recommended but not blocking.
