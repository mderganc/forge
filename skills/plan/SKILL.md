---
description: |
  Create implementation plans with task breakdown, parallelization, TDD, and risks.
  From approved design direction or standalone request. Supports --quick mode.
---

# Forge Plan — Implementation Planning

Routing: [AGENTS.md](../../AGENTS.md) § Process-first.

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

## Safety guardrails

Planning-only: no product source edits. No git mutation commands (`git add`, `commit`, `push`, `reset`, `rebase`, `checkout`, `restore`, `merge`, `stash`, `tag`). Never `--no-verify`.

<invoke cmd="forge plan --step 1" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Phase 1–7 |
| `--quick` | No | Quick mode: minimal reviews |

Default handoff: **`forge:evaluate --mode pre`**.
