---
description: |
  Multi-mode code review: PR, deep, or architecture. Full agent team.
  Structural probes at step 3. Supports --quick mode.
---

# Forge Code Review — Multi-Mode Review

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

At **step 3**, read `.structural-probes.json` and `templates/structural-quality-probes.md` when a structural-probes banner is shown.

<invoke cmd="forge code-review" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Phase 1–6 |
| `--mode` | No | `pr`, `deep`, or `architecture` (auto-detected) |
| `--target` | Step 1 | PR, branch, or file paths |
| `--quick` | No | Quick mode |

Default handoff: **`forge:test`**.
