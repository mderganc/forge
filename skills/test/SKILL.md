---
description: |
  Run tests, analyze coverage and failures. Modes: run (default), flows
  (mock-flow authoring), and ux (real-browser user QA). QA Reviewer lead.
---

# Forge Test — Execution & Coverage

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

## Modes

- **`run`** (default): 6-step detect → execute → analyze → report
- **`flows`**: 7-step mock-flow authoring — see `templates/mock-flow-types.md` and `templates/test-flow-criteria.md`
- **`ux`**: 6-step real-browser QA as a user — understand the app, plan goal-based journeys, click through the live UI, document issues — see `templates/ux-test-criteria.md`

## Simplicity

Preamble § Simplicity (YAGNI). Test behavior needed now—not hypothetical scaffolding.

<invoke cmd="forge test" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | 1–6 (run/ux) or 1–7 (flows) |
| `--mode` | No | `run`, `flows`, or `ux` |
| `--target` | No | Test command/path (run mode) |
| `--base-url` | No | App URL for UX mode (e.g. `http://localhost:3000`) |
| `--flow-type` | No | `scenario`, `bdd`, `http-replay`, `workflow-dryrun` |
| `--framework` / `--entry-point` / `--roles` / `--no-db` / `--re-record` | No | Flows / UX overrides |

Default handoff: **`forge:diagnose`** (on failures) or **`forge:ship`**.
