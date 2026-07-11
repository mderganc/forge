---
name: forge:test
description: Run tests or author mock flows (run/flows modes). For live UI audits use forge:ux-review.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** unless the phase allows it. Follow the active skill's orchestrator output for what may be written.


## Graphify

Runs at **ship** only (`forge ship --step 1`). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- Run the **test** workflow from the repo root.
- Follow orchestrator phase output.
- Real-browser product UX audits use **`/forge:ux-review`**, not test modes.

## What you run (agent)

Run **test** at step one. Summarize phases without quoting invocation lines.
