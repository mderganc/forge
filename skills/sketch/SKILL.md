---
description: |
  Iterative conversational intent dialogue before design. Synthesis checkpoints,
  loop-back on revised decisions; optional CONTEXT.md/ADRs with --with-domain-docs.
  Design (not sketch) writes docs/forge/specs design specs.
---

# forge sketch — Pre-design intent

Iterative pair-thinking: reflect, confirm, revise — not a checklist. See `templates/sketch-protocol.md`.

Routing and sketch vs design boundary: [AGENTS.md](../../AGENTS.md) § Process-first.

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

<invoke cmd="forge sketch" />

| Argument | When | Description |
|----------|------|-------------|
| `--step` | Always | 1 startup, 2 session (re-invokable), 3 handoff |
| `--with-domain-docs` | Step 1+ | Allow `CONTEXT.md` glossary and sparse `docs/adr/` |
| `--state` | Resume | Path to sketch state file |

Re-run **`forge sketch --step 2`** to continue the conversation until ready for handoff.

Default next: **`forge:design`**.
