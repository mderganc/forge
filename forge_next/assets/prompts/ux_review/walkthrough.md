# Phase 3: Browser walkthrough

Walk through the application in a real browser as an actual user would. Visit every accessible page and state, click every relevant button, link, menu, tab, filter, and control, and exercise each available feature and workflow.

## Injected context

- **Base URL:** {{BASE_URL}}
- **Plan:**
```
{{REVIEW_PLAN_JSON}}
```
- **Coverage so far:**
```
{{COVERAGE_JSON}}
```

{{PLAN_GATE_FAILURES}}

## Hard rules

- Prefer primary navigation and visible labels over URL guessing
- Prefer **cursor-ide-browser** MCP; Playwright only if needed
- Keep the coverage checklist live — do not invent completeness later
- Do **not** fix product code unless the user asks

## Your task

1. Lock the browser tab; snapshot before meaningful actions; fresh snapshot after UI changes.
2. For each in-scope page/journey:
   - Follow nav, menus, breadcrumbs, tabs, sidebars, in-page CTAs
   - Open modals/drawers/popovers; dismiss and re-open once
   - Submit forms valid, invalid, and empty-required
   - Exercise filters, sorts, search, pagination, row actions
   - Stop before irreversible prod deletes unless the user approves
3. Capture screenshots of every page and important intermediate state. Name like `03-settings-form.png`.
4. Update `state.custom["coverage"]` / `.ux-review-coverage.json` continuously (pages, controls, workflows, skips with reason).

Read `templates/ux-review-criteria.md` for evaluation dimensions while walking — note candidates for step 5.

## Done when

- [ ] In-scope pages and workflows exercised or skipped with reason
- [ ] Relevant controls clicked
- [ ] Screenshots captured
- [ ] Coverage checklist current

**Next:** step 4 — empty/loading/error/success states and viewports.
