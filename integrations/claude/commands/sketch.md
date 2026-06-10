---
name: forge:sketch
description: Organize thoughts and open decisions before design.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** unless the phase allows it (session memory always; `CONTEXT.md` / `docs/adr/` only when domain-docs mode is on). **Do not** write `docs/forge/specs/` design specs — design does that.

## Graphify

Runs at **ship** only. This workflow does not print GRAPHIFY per step.

## What to tell the user first

- **Sketch** clarifies what they want before design investigates and proposes solutions.
- Optional: domain glossary (`CONTEXT.md`) and ADRs when they need shared language captured in-repo.

## What you run (agent)

Run **sketch** from the repo root at step one. One question at a time with a recommended answer each turn. Summarize phases without quoting invocation lines.

Default next after sketch: **design** (which produces the design spec for medium/large scope).
