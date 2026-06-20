---
name: forge:sketch
description: Organize intent and open decisions before design (optional CONTEXT.md/ADRs).
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** unless the phase allows it (session memory always; `CONTEXT.md` / `docs/adr/` only when domain-docs mode is on). **Do not** write `docs/forge/specs/` design specs.


## Graphify

Runs at **ship** only (`forge ship --step 1`). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Sketch** is an **iterative conversation** — reflect, confirm, revise — before design investigates solutions.
- Optional: domain glossary (`CONTEXT.md`) and ADRs when domain-docs mode is on.

## What you run (agent)

Run **sketch** at step one. **Dialogue only** — do not spawn Forge agents or Task sub-agents. Synthesis every few exchanges; re-run step 2 to continue; step 3 only after the user confirms ready for design.
