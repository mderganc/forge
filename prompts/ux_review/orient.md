# Phase 1: Orient

Begin by understanding the app’s purpose, intended users, information architecture, major features, and critical user journeys.

## Injected context

- **Base URL:** {{BASE_URL}}
- **Roles:** {{ROLES}}
- **Quick mode:** {{QUICK}}
- **State:** {{STATE_PATH}}

## Your task

1. Confirm a reachable base URL (ask if empty). Open the app in a **real browser** (Cursor browser MCP preferred).
2. From UI copy, nav, and light exploration — not from inventing features via source — capture:

| Field | Content |
|-------|---------|
| **Purpose** | Who it is for and what job it does |
| **Intended users** | Personas / roles |
| **Information architecture** | Primary nav, sections, object model |
| **Major features** | Capabilities users would expect to exercise |
| **Critical user journeys** | Top 3–7 happy paths |

3. Persist JSON to session sidecar `.ux-review-orientation.json` beside the state file, and copy into `state.custom["orientation"]`. Set `state.custom["base_url"]` and `state.custom["roles"]` when known.

```json
{
  "purpose": "...",
  "users": ["..."],
  "information_architecture": ["..."],
  "features": ["..."],
  "critical_journeys": [
    {"name": "...", "steps": ["..."], "primary_role": "..."}
  ],
  "base_url": "..."
}
```

If `{{QUICK}}` is `yes`, limit journeys to the top 3 value paths.

## Done when

- [ ] App loads in a real browser
- [ ] Purpose, users, IA, features, and ≥1 critical journey recorded
- [ ] Sidecar + state updated

**Next:** step 2 — structured review plan + coverage checklist.
