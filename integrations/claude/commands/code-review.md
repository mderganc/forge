---
name: forge:code-review
description: Structured PR-style code review workflow.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

## Hard rule — Graphify

If `graphify-out/` exists: read `graphify-out/GRAPH_REPORT.md` **before** grep/glob/semantic search; follow every **GRAPHIFY** block the orchestrator prints on each step; after code edits run `graphify update .`.

## What to tell the user first

- **Code review** selects a mode and runs structured passes through discussion and report.
- Clarify scope (what changed, what matters most).

## What you run (agent)

Run **code-review** from the repo root at step one; recap each major phase without exposing argv.

---
