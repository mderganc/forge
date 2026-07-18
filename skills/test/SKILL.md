---
description: |
  Run tests, analyze coverage and failures. Modes: run (default) and flows
  (mock-flow authoring). For real-browser product UX audits use forge ux-review.
  QA Reviewer lead.
---

# Forge Test — Execution & Coverage

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

## Modes

- **`run`** (default): 6-step detect → execute → analyze → report
- **`flows`**: 7-step mock-flow authoring — see `templates/mock-flow-types.md` and `templates/test-flow-criteria.md`

Real-browser product UX audits live in **`forge ux-review`** (not a test mode). `forge test --mode ux` exits with a redirect.

## Simplicity

Preamble § Simplicity (YAGNI). Test behavior needed now—not hypothetical scaffolding.

<invoke cmd="forge test" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | 1–6 (run) or 1–7 (flows) |
| `--mode` | No | `run` or `flows` (`ux` exits with redirect to `forge ux-review`) |
| `--target` | No | Test command/path (run mode) |
| `--flow-type` | No | `scenario`, `bdd`, `http-replay`, `workflow-dryrun` |
| `--framework` / `--entry-point` / `--roles` / `--no-db` / `--re-record` | No | Flows overrides |

Default handoff: **`forge:ship`** when the run is green, **`forge:diagnose`** when there are failures.
