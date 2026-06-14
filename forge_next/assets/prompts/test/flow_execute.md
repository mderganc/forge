# Phase 6: Execution + Iteration

**Lead: QA**

Run the mock flow and verify green (GREEN phase). Fix app bugs or return to step 5 for test issues.

## Checklist

- [ ] Run pytest on the flow file: `-v --tb=short --maxfail=1 --strict-markers` — expect **PASS**.
- [ ] Log pass/fail counts and per-role results (if parameterized).
- [ ] On failure: app bug → fix code and re-run; test issue → return to step 5 authoring.
- [ ] **Determinism (criterion 8):** run pytest twice, `diff` outputs — fix unpatched `time`/`random`/UUID before advancing.
- [ ] **HTTP replay only (`{{FLOW_TYPE}}`):** check cassette mtimes — warn > 30d, fail > 90d; use `--re-record` if stale.
- [ ] Bounded retries: max 3 re-runs on the same failure before escalating.
- [ ] Targeted run first (`test_<scope>.py`, optional `-k`); full suite after seam is stable.

**Next:** step 7 report — audit against **`templates/test-flow-criteria.md`**.
