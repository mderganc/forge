# Phase 5: Issue Documentation

**Lead: QA Reviewer + Doc-writer**

Every failure and notable UX defect becomes a structured issue. Follow **`templates/ux-issue-report.md`**.

## Context

- Results: `state.custom.ux_results`
- Draft stubs: `state.custom.ux_issues`

## Required fields (each issue)

| Field | Requirement |
|-------|-------------|
| `id` | Stable id (`UX-1`, `UX-2`, …) |
| `title` | Short, user-visible symptom |
| `severity` | `critical` \| `high` \| `medium` \| `low` |
| `page` / `feature` | Where it broke |
| `steps` | Numbered reproduction from a clean starting point |
| `expected` | What should have happened (visible) |
| `actual` | What happened |
| `screenshots` | Paths or embedded refs |
| `console_errors` | Relevant console lines (or `[]`) |
| `network_errors` | Failed requests (or `[]`) |
| `scenario_id` | Link back to plan scenario when applicable |

Severity guide:

- **critical** — data loss, security, blocker for primary goal
- **high** — primary workflow broken with no reasonable workaround
- **medium** — workaround exists; wrong/confusing UI
- **low** — polish, copy, minor inconsistency

## Persistence

Write the full array to `state.custom["ux_issues"]` and sidecar `.test-ux-issues.json`.

If the run was clean, persist `"ux_issues": []` explicitly and note that in the session memory.

## Done when

- [ ] Every `failed` scenario has a matching issue (or a justified merge)
- [ ] Each issue has repro steps + expected vs actual + severity
- [ ] Evidence attached where tools allowed capture

**Next:** step 6 — coverage summary and recommendations.
