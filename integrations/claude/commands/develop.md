---
name: forge:develop
description: Investigate the problem space before planning.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** (code, `agents/`, `prompts/`, integrations, etc.) unless the user **explicitly** allows that specific change. Use develop for read-only exploration and for writing **only** where the phase directs session memory (e.g. `.codex/forge/memory/` or legacy `.codex/forge-codex/memory/`). If unsure, ask first.

**Medium/large scope** may require a formal design spec and `.develop-spec-gate.json` before step 7; follow phase output.

## What to tell the user first

- **Develop** explores problems, options, and evidence before formal planning.
- Clarify goals and whether they want a lighter pacing option.
- **Routing:** Prefer develop when the shape of the work is still unclear; if the user already has a single approved approach, they may be ready for plan instead. Unclear incidents or test failures → diagnose / test before big planning.

## What you run (agent)

Run **develop** from the repo root at step one; honor pacing preferences via the launcher only. Summarize each phase without quoting invocation lines.

---
