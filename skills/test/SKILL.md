---
description: |
  Run tests, analyze coverage and failures. Modes: run (default) and flows
  (mock-flow authoring). QA Reviewer lead.
---

# Forge Test — Execution & Coverage

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

## Modes

- **`run`** (default): 6-step detect → execute → analyze → report
- **`flows`**: 7-step mock-flow authoring — see `templates/mock-flow-types.md` and `templates/test-flow-criteria.md`

<invoke cmd="forge test" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | 1–6 (run) or 1–7 (flows) |
| `--mode` | No | `run` or `flows` |
| `--target` | No | Test command/path (run mode) |
| `--flow-type` | No | `scenario`, `bdd`, `http-replay`, `workflow-dryrun` |
| `--framework` / `--entry-point` / `--roles` / `--no-db` / `--re-record` | No | Flows overrides |

Default handoff: **`forge:diagnose`** (on failures) or **`forge:ship`**.
