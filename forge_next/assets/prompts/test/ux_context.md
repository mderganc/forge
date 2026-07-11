# Phase 1: App Understanding

**Lead: QA Reviewer**

Behave like a real user later — first understand what the product is for. Do **not** run the automated test suite or inspect implementation for coverage metrics. Map the product from the user's point of view.

## Injected context

- **Mode:** {{MODE}}
- **Base URL:** {{BASE_URL}}
- **Roles (detected/override):** {{ROLES}}
- **Entry point hint:** {{ENTRY_POINT}}
- **Target / notes:** {{TARGET}}

{{HANDOFF_CONTENT}}

## Your task

### 1. Confirm the running application

Ask the user for (or infer) a reachable **base URL** if `{{BASE_URL}}` is empty. Prefer a local or staging URL they can exercise now.

Open the app in a **real browser** (Cursor browser MCP, Playwright CLI, or equivalent). Confirm the home/login surface loads.

### 2. Build an application map

From UI copy, nav, docs (`README`, product pages), and light exploration — **not** from reading source to invent features — capture:

| Field | Content |
|-------|---------|
| **Purpose** | One sentence: who it is for and what job it does |
| **Features** | Primary capabilities visible in the product |
| **User roles** | Roles a real person would switch between (use {{ROLES}} as a starting point) |
| **Critical workflows** | End-to-end journeys that deliver the product's value (e.g. sign up → create → share → export) |
| **First-time surfaces** | Onboarding, empty states, permissions prompts |
| **Data that must persist** | Entities the user expects to survive refresh/navigation |

### 3. Persist the map

Write JSON to the session sidecar `.test-ux-app-map.json` beside the state file:

```json
{
  "purpose": "...",
  "features": ["..."],
  "roles": ["..."],
  "critical_workflows": [
    {"name": "...", "steps": ["...", "..."], "primary_role": "..."}
  ],
  "first_time_surfaces": ["..."],
  "persistent_entities": ["..."],
  "base_url": "https://..."
}
```

Also copy the same object into `state.custom["app_map"]` and set `state.custom["base_url"]` if discovered.

## Done when

- [ ] Base URL confirmed and app loads in a real browser
- [ ] Purpose, features, roles, and ≥1 critical workflow recorded
- [ ] Sidecar + state updated

**Next:** step 2 — turn this map into a goal-based test plan.
