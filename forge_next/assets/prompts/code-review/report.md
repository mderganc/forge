# Phase 6: Report

Write the final code review report and hand off to the test skill.

## Review Summary

**Mode:** {{MODE}} ({{MODE_DISPLAY}})
**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Final Findings

{{FINDINGS}}

## Your Task

### 1. Write the Code Review Report

Write the report to `.codex/forge-codex/memory/code-review-report.md` with this structure:

- Summary section with mode, target, date, reviewers
- Findings table: ID, Severity, Title, Status
- Detailed findings: each with severity, source reviewer, file:line, detail, recommendation
- High-level recommendations
- Handoff notes for the test skill (areas needing test attention, edge cases found)

### 2. Update Memory

- Update `.codex/forge-codex/memory/project.md` with code review completion status
- Record the finding count and severity breakdown

### 3. Prepare Handoff

The handoff file will be written automatically. Ensure the findings are
recorded in the state so the test skill knows what to focus on.

### 4. Present Dashboard

Show the user:
- Total findings by severity
- Open vs dismissed vs resolved
- Suggested next step: `test`
