# Phase 4: Edge Cases & Persistence

**Lead: QA Reviewer**

Continue as a real user. Exercise **adversarial and recovery** scenarios, then prove saved data survives navigation and refresh.

## Categories to run now

From `ux_plan.scenarios`, execute (if present):  
`empty_state` · `invalid_input` · `cancellation` · `retry` · `edge_case` · `error_recovery`

Also revisit any happy-path scenario that **saved data** and run its `persistence_checks`.

## Interaction checklist

For each scenario, use real UI controls:

- [ ] Navigate via menus, tabs, breadcrumbs, and in-app links
- [ ] Submit and clear forms; trigger validation deliberately
- [ ] Upload files where relevant (clean + messy if fixtures exist)
- [ ] Apply filters/sorts/search and confirm list results update
- [ ] Cancel mid-flow (close dialog, Back, Escape) and confirm no corrupt state
- [ ] Retry after a forced error when the product supports retry
- [ ] Confirm error messages are visible and actionable — not blank screens or silent failures

## Persistence protocol

When a scenario claims data was saved:

1. Note the visible record (name, id, status).
2. Navigate to a different section.
3. Return to the list/detail — still correct?
4. Hard refresh (or re-open the URL) — still correct?
5. If multi-role: log in as another authorized role and confirm shared visibility rules.

Record pass/fail under `ux_results.scenarios` (append or update). Attach screenshots for persistence failures.

## Evidence

On failure, capture:

- Screenshot of the broken state
- Console errors (if available)
- Failed/network 4xx/5xx requests (if available)
- Exact UI path (page title / URL / feature name)

## Done when

- [ ] Adversarial categories from the plan attempted or marked N/A with reason
- [ ] Persistence checks run for scenarios that mutate data
- [ ] `ux_results` totals accurate

**Next:** step 5 — finish structured issue records.
