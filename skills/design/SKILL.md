---
description: |
  Investigate, brainstorm, and evaluate solutions. Spawns agent team for
  investigation, solution evaluation, and user approval. Autonomy --auto1/2/3,
  --quick. Writes docs/forge/specs/*-design.md for medium/large scope.
---

# Forge Design — Investigation & Ideation

Routing: [AGENTS.md](../../AGENTS.md) § Process-first.

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md). Agent roster: [templates/forge-agent-roster.md](../../templates/forge-agent-roster.md).

## No repo edits without permission

Do **not** modify tracked project files unless the user explicitly authorizes. Session memory and `docs/forge/specs/` only when the orchestrator directs.

## Spec gate (medium/large)

After step 2: `design-scope.json` in memory (legacy `develop-scope.json` still read). Medium/large: complete design spec + `.design-spec-gate.json` before step 7. See `prompts/develop/scope.md`.

<invoke cmd="forge design" />

| Argument | When | Description |
|----------|------|-------------|
| `--step` | Always | Phase 1–7 |
| `--auto1` / `--auto2` / `--auto3` | Any | Autonomy level |
| `--quick` | Step 1+ | Quick mode |
| `--allow-spec-incomplete` | Step 7 only | Bypass spec gate (requires override fields) |
| `--spec-override-reason` | With bypass | Recorded in handoff |
| `--spec-override-follow-up` | With bypass | Required follow-up |
| `--spec-override-requested-by` | Optional | Who requested bypass |

Default handoff: **`forge:plan`**.
