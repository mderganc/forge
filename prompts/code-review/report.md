# Phase 6: Report

Write the final code review report and hand off to the test skill.

## Review Summary

**Mode:** {{MODE}} ({{MODE_DISPLAY}})
**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Final Findings

{{FINDINGS}}

## Structural probes (orchestrator-filled)

{{STRUCTURAL_PROBES_SUMMARY}}

## Your Task

### 1. Write the Code Review Report

Write the report to `{{MEMORY_DIR}}/code-review-report.md` with this structure:

- Summary section with mode, target, date, reviewers, fixed point, spec source
- **`## Pass A — Spec`** — findings verbatim or lightly cleaned (intent/requirements axis)
- **`## Pass B — Standards`** — findings verbatim or lightly cleaned; include structural probes
- **`## Summary`** — per-axis counts and worst finding within each axis (no single cross-axis winner):
  - Pass A: N findings; worst: …
  - Pass B: N findings; worst: …
- Findings table: ID, **Pass** (`A` | `B`), Severity, Title, Status
- Detailed findings: each with pass, severity, source reviewer, file:line, detail, recommendation
- High-level recommendations
- Handoff notes for the test skill (areas needing test attention, edge cases found)
- **Workflow prompts:** copy the appendix below — verbatim orchestrator prompts from each code-review step

**Structural probes (Pass B):** paste `{{STRUCTURAL_PROBES_SUMMARY}}` verbatim under Pass B (from step 3 sidecar — do not re-run pyscn/knip/madge/skylos).

{{WORKFLOW_PROMPTS_APPENDIX}}

### 2. Update Memory

- Update `{{MEMORY_DIR}}/project.md` with code review completion status
- Record finding counts by pass and severity breakdown

### 3. Prepare Handoff

The handoff file will be written automatically. Ensure the findings are
recorded in the state so the test skill knows what to focus on.

### 4. Present Dashboard

Show the user:
- Total findings by pass (A vs B) and by severity
- Open vs dismissed vs resolved
- Worst finding per axis (not a merged ranking)
- Suggested next step: `test`
