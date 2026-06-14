---
name: forge:test
description: Run tests or author mock flows (run/flows modes).
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** unless the phase allows it. Follow the active skill's orchestrator output for what may be written.


## Graphify

Runs at **ship** only (`forge ship --step 1`). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- Run the **test** workflow from the repo root.
- Follow orchestrator phase output.

## What you run (agent)

Run **test** at step one. Summarize phases without quoting invocation lines.
