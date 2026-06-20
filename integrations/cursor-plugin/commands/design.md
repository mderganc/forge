---
name: forge:design
description: Investigate, brainstorm solutions, and write a named design spec at docs/forge/specs/ (medium/large).
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** unless the user **explicitly** allows that change. Session memory and `docs/forge/specs/` only when directed.


## Graphify

Runs at **ship** only (`forge ship --step 1`). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Design** explores problems, options, and evidence before formal planning.
- Medium/large scope requires a named spec at `docs/forge/specs/` before handoff.

## What you run (agent)

Run **design** at step one. Summarize phases without quoting invocation lines. When dispatching, use only roles in **`templates/forge-agent-roster.md`** (e.g. **Architect**, **Investigator**) — never invent names like `backend-architect`.
