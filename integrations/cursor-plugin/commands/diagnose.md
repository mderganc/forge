---
name: forge:diagnose
description: Structured root-cause analysis for bugs and incidents.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow. Speak in outcomes and phase names only.

## Hard rule — Graphify

If `graphify-out/` exists: read `graphify-out/GRAPH_REPORT.md` **before** grep/glob/semantic search; follow every **GRAPHIFY** block the orchestrator prints on each step; after code edits run `graphify update .`.

## What to tell the user first

- **Diagnose** phases through definition, evidence, decomposition, analysis, solutions, optional validation, report.
- Capture the **symptom** and pacing preference (guided / autonomous / interactive when available).

## What you run (agent)

Run **diagnose** from the repo root at step one; carry pacing flags only through the launcher. Summarize orchestrator content—never forward raw launcher command lines to the user.

---
