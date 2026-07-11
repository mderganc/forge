# Phase 6: Report + Handoff

**Lead: Doc-writer**

Produce a concise UX test report. Do **not** pad with suite coverage percentages — this mode measures **user-goal coverage**, not line coverage.

{{UX_ISSUES_GATE_FAILURES}}

## Report sections (write to `{{MEMORY_DIR}}/ux-test-report.md`)

### 1. Coverage summary

- Goals and scenarios attempted vs planned
- Roles exercised
- Categories covered (`happy_path`, `first_time`, `empty_state`, …)

### 2. Results

| Status | Count |
|--------|-------|
| Passed | from `ux_results` |
| Failed | |
| Blocked | |

List scenario ids under each status.

### 3. Issues

Table of `ux_issues` sorted by severity (critical → low): id, title, page/feature, severity.

### 4. Untested areas

What the plan deferred, blocked (auth, missing env), or never reached — be explicit.

### 5. Major risks

Product risks implied by failures or gaps (e.g. "share flow untested for viewer role").

### 6. Prioritized recommendations

Numbered, actionable, highest severity first. Prefer fixes and follow-up tests over vague advice.

## State

Fill `state.custom["ux_coverage"]`:

```json
{
  "covered": ["..."],
  "untested": ["..."],
  "risks": ["..."],
  "recommendations": ["1. ...", "2. ..."]
}
```

Align `ux_results` totals with the report.

## Handoff

Orchestrator writes `handoff-test.md` on success. Suggest **diagnose** when critical/high issues exist; otherwise ship or return to implement.

## Rubric

Self-check against **`templates/ux-test-criteria.md`** before finishing.
