---
description: |
  Multi-mode code review: PR, deep, or architecture. Full agent team.
  Structural probes at step 3. Supports --quick mode.
---

# Forge Code Review — Multi-Mode Review

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

At **step 3**, the orchestrator runs **pyscn** (Python) and **knip** (Node) when applicable and writes `.structural-probes.json`.

**Steps 4–6 are blocked** until required probes have run (`pass` or `fail`, not `skip`). Re-run step 3 or use `--allow-structural-probes-incomplete` with override reason/follow-up to bypass.

<invoke cmd="forge code-review" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Phase 1–6 |
| `--mode` | No | `pr`, `deep`, or `architecture` (auto-detected) |
| `--target` | Step 1 | PR, branch, or file paths |
| `--quick` | No | Quick mode |

Default handoff: **`forge:test`**.
