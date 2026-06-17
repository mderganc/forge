---
description: |
  Meta-workflow chaining diagnose, plan, evaluate, implement, code-review, and
  test with gate polling and loops.
---

# Forge Iterate — Meta-Workflow

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

<invoke cmd="forge iterate" />

| Argument | Purpose |
|----------|---------|
| `--step` | Phase 1–9 |
| `--goal` | Workflow goal text |
| `--target` | Optional scope target |
| `--max-loops` | Loop limit |

Polls `.iterate-gates/*.json` between child skills. See `forge iterate --help` for flags.
