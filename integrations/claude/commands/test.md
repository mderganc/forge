---
name: forge:test
description: Run or author tests (including flows mode).
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

## Graphify

Runs at **ship** only (orge ship --step 1 / $forge:ship). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Test** supports default suite runs or flows-style authoring—confirm which they need and what’s failing or risky.

## What you run (agent)

Run **test** from the repo root at step one; select flows mode only when requested through the launcher. Report results in ordinary language.

---
