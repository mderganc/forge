# UX Test Quality Criteria

Canonical rubric for `forge test --mode ux`. Real-browser, goal-based QA — not suite execution and not mock-flow authoring.

| # | Criterion | Summary |
|---|-----------|---------|
| 1 | **App understanding first** | Purpose, features, roles, and critical workflows recorded before deep execution. |
| 2 | **Goal-based plan** | Scenarios start from user goals; categories cover happy, first-time, empty, invalid, cancel, retry, edge, recovery. |
| 3 | **Real browser interaction** | Navigate, click, type, upload, menus/filters via live UI — not code-only inspection or suite runs. |
| 4 | **Visible outcome checks** | Every action judged by what the user sees (and hears, if applicable). |
| 5 | **Persistence verification** | Saved/changed data re-checked after navigate-away and refresh. |
| 6 | **Structured issues** | Failures have repro steps, expected vs actual, severity, page/feature, screenshots, console/network when available. |
| 7 | **Honest coverage report** | Summary includes passed/failed/blocked, untested areas, risks, and prioritized recommendations. |

**Related:** `templates/ux-issue-report.md`, `prompts/test/ux_*.md`.
