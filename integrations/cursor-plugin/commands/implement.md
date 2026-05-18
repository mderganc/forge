---
name: forge:implement
description: Execute an implementation plan in waves with reviews.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

## Hard rule — Graphify

If `graphify-out/` exists: read `graphify-out/GRAPH_REPORT.md` **before** grep/glob/semantic search; follow every **GRAPHIFY** block the orchestrator prints on each step; after code edits run `graphify update .`.

## What to tell the user first

- **Implement** covers branch setup, waves, reviews, integration, documentation, handoff.
- Confirm plan availability (path or handoff) and readiness to execute.

## What you run (agent)

Run **implement** from the repo root beginning at step one; attach plan context when given. Continue stepwise; describe wave outcomes in prose—do not expose launcher argv.

---
