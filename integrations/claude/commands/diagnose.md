---
name: forge:diagnose
description: Structured root-cause analysis for bugs and incidents.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow. Speak in outcomes and phase names only.

## Graphify

Runs at **ship** only (forge ship --step 1 / $forge:ship). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Diagnose** phases through definition, evidence, decomposition, analysis, solutions, optional validation, report.
- Capture the **symptom** and pacing preference (guided / autonomous / interactive when available).

## What you run (agent)

Run **diagnose** from the repo root at step one; carry pacing flags only through the launcher. Summarize orchestrator content—never forward raw launcher command lines to the user.

---
