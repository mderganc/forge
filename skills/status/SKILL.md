---
description: |
  Read-only dashboard: skill completion, open findings, beads, suggested next step.
---

# Forge Status — Flow Dashboard

Routing for suggested next: [AGENTS.md](../../AGENTS.md) § Process-first.

Runtime root: `.codex/forge/` (legacy `.codex/forge-codex/`).

## Report format

| Skill | Status | Key output |
|-------|--------|------------|
| sketch / design / plan / evaluate / implement / code-review / test / diagnose | COMPLETE / IN_PROGRESS / NOT_STARTED | From handoff + session state |

**COMPLETE:** `handoff-{skill}.md` or session `handoff.md`. **IN_PROGRESS:** active `session.json` without handoff.

Collect open findings from state sidecars. Present beads summary from `project.md`.

<invoke cmd="forge status" />
