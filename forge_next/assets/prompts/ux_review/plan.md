# Phase 2: Review plan

Develop a structured review plan and maintain a coverage checklist while testing.

## Injected context

- **Base URL:** {{BASE_URL}}
- **Orientation:**
```
{{ORIENTATION_JSON}}
```
- **State dir:** {{STATE_DIR}}

## Your task

1. Read `templates/ux-review-coverage-checklist.md` and seed a working checklist (session notes or `.ux-review-coverage.json`).
2. Write `state.custom["review_plan"]` / `.ux-review-plan.json`:

```json
{
  "entry_points": ["..."],
  "journey_order": ["..."],
  "pages": ["..."],
  "journeys": [
    {"name": "...", "role": "...", "steps": ["..."]}
  ],
  "state_matrix": ["empty", "loading", "populated", "validation", "error", "success"],
  "viewports": ["desktop", "768", "375"],
  "out_of_scope": ["..."]
}
```

3. Order: critical journeys first → secondary features → settings/edge.
4. If quick mode, drop non-critical pages and optional viewports explicitly in `out_of_scope`.

## Done when

- [ ] Plan lists pages/journeys and viewports
- [ ] Coverage checklist initialized
- [ ] Base URL still set

**Next:** step 3 — exhaustive browser walkthrough.
