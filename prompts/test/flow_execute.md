# Phase 6: Execution + Iteration

**Lead: QA**

You will run the mock flow and verify it passes. This is the "GREEN" phase of TDD: run the test and make sure it passes against the actual implementation. The orchestrator will also check determinism via a double-run.

## Your Task

### 1. Run the Flow

Execute the test suite using the verification protocol:

```
cd /path/to/project
python -m pytest tests/<scenarios|features|cassettes|orchestration>/test_<scope>.py -v --tb=short --maxfail=1 --strict-markers
```

**Expected:** PASS (all test cases green).

If any test fails:
- **Review the failure message** \u2014 does it indicate a real bug in the app, or a test-authoring issue?
- **If app bug:** Fix the app code, re-run, and confirm green.
- **If test issue:** Go back to step 5 (authoring) to fix the test.

Log the output:
```
Result: [N passed, M failed] \u2014 [pass/fail]
Failures (if any): [paste error messages]
```

### 2. Per-Role Pass/Fail

If your flow tests multiple roles, confirm each role:

- **Admin:** [pass/fail]
- **Member:** [pass/fail]
- **Viewer:** [pass/fail]

Each role should pass its role-specific assertions. If a role fails unexpectedly, re-run that role's test with `-v` and debug.

### 3. Double-Run Determinism Check

The orchestrator will run your flow twice and diff the outputs. Non-determinism (e.g., test passes once, fails the second time; or output differs) aborts back to step 5.

**Automated check:** The orchestrator runs this. If it detects non-determinism, it will re-prompt step 5 with a corrective message (e.g., "found `time.time()` calls in test; use fixed timestamps instead").

**Manual verification:** You can also verify locally:
```
# Run twice
python -m pytest tests/.../test_<scope>.py --tb=short > run1.txt
python -m pytest tests/.../test_<scope>.py --tb=short > run2.txt

# Compare
diff run1.txt run2.txt
# Expected: no output (identical)
```

### 4. HTTP Replay: Cassette Freshness

If {{FLOW_TYPE}} is `http-replay`:

- Check cassette file modification times:
  ```
  exec_command ls -lah tests/cassettes/data/<scope>/*.yaml
  ```

- **> 30 days old:** Warning printed. Consider re-recording.
- **> 90 days old:** FAIL \u2014 cassettes must be refreshed.
  ```
  python -m pytest tests/cassettes/test_<scope>.py --record-mode=once
  ```
  Or use `--re-record` flag when invoking the skill.

### 5. Loop with Bounded Retries

If the test fails:

- **1st failure:** Investigate and fix the app or test (unlikely if authoring was solid).
- **2nd failure on same step:** Escalate to the plan; this may indicate a scope issue.
- **Bounded by failure_count:** Maximum 3 re-runs before aborting (prevents infinite loops).

Once green, advance to step 7 (Report).

## Fast Feedback (No Full Sweep Required)

- First validate the seam with a targeted run (`test_<scope>.py`, optional `-k "<journey>"`).
- Use `pytest --lf` after a failure to iterate quickly on the same failing case.
- Run full-suite/regression only after the targeted seam is stable and deterministic.

## Codex Runtime Instructions

1. **Read the scope and files:** Understand what's being tested and where the test files live.

2. **Run the test:** Execute pytest with verbose output and short traceback:
   ```
   exec_command cd /path/to/project && python -m pytest tests/.../test_<scope>.py -v --tb=short --maxfail=1 --strict-markers
   ```

3. **Parse the output:** Extract:
   - Pass count
   - Fail count
   - Per-role results (if parameterized)
   - Error messages (if any)

4. **For failures:** Decide: app bug or test issue?
   - **App bug:** Fix the code, re-run, confirm green.
   - **Test issue:** Return to step 5 authoring prompt.

5. **Determinism check:** If the orchestrator flags non-determinism, look for:
   - `time.time()`, `time.now()`, `random.random()` in test or fixture code
   - `uuid.uuid4()` called during test (not test data)
   - External service calls that return different results
   - Database state not reset between runs
   
   Fix any of these and re-run step 5 to re-author the test.

6. **Cassette freshness (HTTP replay only):** Check mtime and warn/fail as needed. Suggest `--re-record` if too old.

7. **State update:** Log the pass/fail result to state. Once all tests green and deterministic, advance to step 7.

The next step (Report) will audit the flow against the 8 criteria and document it in the project memory.
