# Phase 3: Browser Journey Execution

**Lead: QA Reviewer**

Execute **P0/P1 happy-path and first-time** scenarios by behaving like a real user in a **real browser**. Do not substitute code inspection or `pytest` for this phase.

## Context

- **Base URL:** {{BASE_URL}}
- **Plan:** `state.custom.ux_plan` / `.test-ux-plan.json`

{{UX_PLAN_GATE_FAILURES}}

## Browser tooling (pick what is available)

| Environment | Prefer |
|-------------|--------|
| Cursor | `cursor-ide-browser` MCP — navigate, snapshot, click, type, fill, upload, screenshots |
| Codex / CLI | Playwright skill / `playwright-cli` |
| Fallback | Document blocker and ask the user to open the URL; do not fake results |

**Hard rules**

- Click **actual** buttons and links from the live DOM (use refs/snapshots), not guessed coordinates from stale screenshots.
- Complete forms, use menus/filters, upload files when the journey requires it.
- After every meaningful action, confirm the **visible** result matches `expected_visible`.
- Capture a screenshot on failure and on each scenario completion when evidence helps.
- Collect console errors and failed network requests when the browser tools expose them.

## Execution loop

For each scenario with `category` in `{happy_path, first_time}` and priority P0/P1:

1. Reset or use a clean session appropriate to the role (incognito / logout as needed).
2. Follow `steps` in order as a user would.
3. Mark **pass** / **fail** / **blocked** with a one-line note.
4. On fail: stop that scenario, capture evidence, continue to the next scenario (do not abandon the whole plan).

Update `state.custom["ux_results"]` as you go:

```json
{
  "passed": 0,
  "failed": 0,
  "blocked": 0,
  "total": 0,
  "scenarios": [
    {
      "id": "S1",
      "status": "pass",
      "notes": "",
      "screenshots": ["path/or/artifact"],
      "console_errors": [],
      "network_errors": []
    }
  ]
}
```

Draft issue stubs into `state.custom["ux_issues"]` for failures (full write-up is step 5) — at minimum `title`, `severity`, `page`/`feature`, and failing `steps`.

## Done when

- [ ] All P0 happy_path / first_time scenarios attempted
- [ ] Visible outcomes checked per scenario
- [ ] `ux_results` updated; failures have issue stubs

**Next:** step 4 — empty states, invalid input, cancel, retry, edge cases, recovery, and persistence.
