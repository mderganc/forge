---
name: forge:design
description: Investigate the problem space and write a named design spec before planning.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** (code, `agents/`, `prompts/`, integrations, etc.) unless the user **explicitly** allows that specific change. Use design for read-only exploration and for writing **only** where the phase directs session memory (e.g. `.codex/forge/memory/`; legacy `.codex/forge-codex/memory/`) or the named design spec at `docs/forge/specs/`. If unsure, ask first.

## Graphify

Runs at **ship** only (forge ship --step 1 / $forge:ship). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Design** explores problems, options, and evidence before formal planning.
- Medium/large scope requires a **named** spec at `docs/forge/specs/YYYY-MM-DD-<slug>-design.md` before handoff.
- Clarify goals and whether they want a lighter pacing option.

## What you run (agent)

Run **design** from the repo root at step one; honor pacing preferences via the launcher only. Summarize each phase without quoting invocation lines.

---
