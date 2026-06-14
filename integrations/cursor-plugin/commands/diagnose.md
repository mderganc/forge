---
name: forge:diagnose
description: Deep diagnosis workflow for bugs/regressions.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** unless the phase allows it. Follow the active skill's orchestrator output for what may be written.


## Graphify

Runs at **ship** only (`forge ship --step 1`). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Diagnose** runs structured RCA when root cause is unclear.

## What you run (agent)

Run **diagnose** at step one. Follow playbook sidecars and gates.
