# Phase 5: Findings

Evaluate functional correctness, ease of use, navigation, discoverability, accessibility, visual hierarchy, content clarity, feedback, error prevention and recovery, responsiveness, and consistency across the application. Identify broken controls, dead ends, confusing interactions, missing states, inconsistent patterns, and unnecessary friction.

## Injected context

- **Findings so far ({{FINDINGS_COUNT}}):**
```
{{FINDINGS_JSON}}
```
- **Coverage:**
```
{{COVERAGE_JSON}}
```

## Your task

1. Read `templates/ux-review-criteria.md` severity guide.
2. Deduplicate recurring patterns into one finding with multiple locations when appropriate.
3. Persist `state.custom["findings"]` / `.ux-review-findings.json`. Each finding **must** include:

| Field | Required |
|-------|----------|
| `id` | e.g. F1 |
| `title` | short |
| `location` | page / component / route |
| `severity` | blocker \| high \| medium \| low \| nit |
| `impact` | who is affected and how |
| `steps` | numbered reproduction |
| `evidence` | screenshot path / description |
| `recommendation` | actionable, specific |

Empty findings list is allowed only for a genuinely clean review — note that explicitly in `coverage`.

## Done when

- [ ] All observed issues captured with required fields
- [ ] Severities assigned
- [ ] Sidecar + state updated

**Next:** step 6 — prioritized report + handoff.
