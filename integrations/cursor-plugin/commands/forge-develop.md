---
name: forge:develop
description: Investigate the problem space before planning.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** (code, `agents/`, `prompts/`, integrations, etc.) unless the user **explicitly** allows that specific change. Use develop for read-only exploration and for writing **only** where the phase directs session memory (e.g. `.codex/forge-codex/memory/`). If unsure, ask first.

## What to tell the user first

- **Develop** explores problems, options, and evidence before formal planning.
- Clarify goals and whether they want a lighter pacing option.

## What you run (agent)

Run **develop** from the repo root at step one; honor pacing preferences via the launcher only. Summarize each phase without quoting invocation lines.

---
