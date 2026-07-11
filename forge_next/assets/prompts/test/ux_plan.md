# Phase 2: Goal-Based Test Plan

**Lead: QA Reviewer**

Turn the app map into a **practical test plan** grounded in realistic user goals — not code paths or suite coverage.

## Context

- **Base URL:** {{BASE_URL}}
- **Roles:** {{ROLES}}
- **App map (from state):** see `state.custom.app_map` / `.test-ux-app-map.json`

## Planning rules

1. Every scenario starts from a **user goal** ("I need to upload a report and share it with my team"), not a UI widget name.
2. Prefer complete journeys over isolated clicks.
3. Cover, across the plan as a whole:
   - Normal / happy-path usage
   - First-time-user experience
   - Empty states
   - Invalid inputs
   - Cancellations and back-outs
   - Retries after transient failure
   - Edge cases (long text, large files, slow network if feasible)
   - Error recovery (clear message, recoverable state, no silent data loss)
4. For each scenario, define **visible success criteria** (what the user should see) and **persistence checks** (survive navigate-away and refresh when data is saved).

## Scenario schema

Persist `state.custom["ux_plan"]` and sidecar `.test-ux-plan.json`:

```json
{
  "user_goals": ["Upload and share a report", "..."],
  "scenarios": [
    {
      "id": "S1",
      "goal": "Upload and share a report",
      "role": "member",
      "category": "happy_path",
      "priority": "P0",
      "steps": ["Log in", "Open Upload", "Attach clean file", "Submit", "Open share dialog", "Invite teammate"],
      "expected_visible": ["Success toast", "Report appears in list"],
      "persistence_checks": ["Refresh list still shows report", "Open detail after navigate-away"],
      "notes": ""
    }
  ]
}
```

**Categories to include at least once (unless the product truly lacks them):**  
`happy_path` · `first_time` · `empty_state` · `invalid_input` · `cancellation` · `retry` · `edge_case` · `error_recovery`

Prioritize **P0** critical workflows from the app map; mark nice-to-haves **P2**.

## Done when

- [ ] ≥1 scenario per critical workflow (or explicit deferral with reason)
- [ ] Categories above covered or explicitly marked N/A for this product
- [ ] Each scenario has expected_visible + persistence_checks where data is saved
- [ ] Plan written to state + sidecar

**Next:** step 3 — execute core journeys in a real browser.
