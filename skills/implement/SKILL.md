---
description: |
  Execute a plan in parallel waves with per-task review, integration verification,
  documentation gate, and handoff. Supports --quick and docs-gate overrides.
---

# Forge Implement — Code Execution

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

<invoke cmd="forge implement" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Phase 1–8 |
| `--plan` | Step 1 only | Plan path (auto from handoff if omitted) |
| `--quick` | No | Quick mode |
| `--allow-docs-incomplete` | Step 8 only | Bypass documentation gate |
| `--docs-override-reason` | With bypass | Recorded in handoff |
| `--docs-override-follow-up` | With bypass | Required follow-up |
| `--docs-override-requested-by` | Optional | Who requested override |

Step 8: documentation gate — plan Documentation skeleton + `.implement-documentation-gate.json` or override.

Default handoff: **`forge:code-review`**.
