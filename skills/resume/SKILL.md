---
description: |
  Resume in-progress Forge workflows. Detects sessions, outputs exact resume
  command. Supports --cleanup for stale state.
---

# Forge Resume

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md) (tooling only).

State lifecycle and auto-close: [AGENTS.md](../../AGENTS.md) § State Lifecycle, [docs/sessions.md](../../docs/sessions.md).

<invoke cmd="forge resume" />

| Command | Purpose |
|---------|---------|
| `forge resume` | Resume active session or suggest next skill |
| `forge resume --cleanup` | Dry-run stale session removal |
| `forge resume --cleanup --force` | Delete stale sessions |

Run the script output immediately — do not analyze first.
