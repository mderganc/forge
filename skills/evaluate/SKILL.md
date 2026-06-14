---
description: |
  Plan critique (pre) and implementation audit (post). Path or keyword plan lookup.
  Use before implement or after to compare work to plan. Review mode deprecated — use code-review.
---

# Evaluate — Plan Analysis & Critique

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

**Modes:** `pre` (7 steps), `post` (8 steps). **`--mode review` is deprecated** — use **`forge code-review`** for full-team review.

In **post** step 4, read `.structural-probes.json` when a structural-probes banner is shown.

<invoke cmd="forge evaluate --step 1 --plan '<plan path or keywords>'" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Phase (7 pre, 8 post) |
| `--plan` | Step 1 (pre/post) | Plan path or keywords |
| `--mode` | No | `pre` or `post` (auto-detected) |
| `--team` | No | Team dispatch in pre/post |

Default handoff (pre): **`forge:implement`**. Default handoff (post): varies — see orchestrator menu.
