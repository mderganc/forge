---
name: forge:implement
description: Execute an implementation plan in waves with reviews.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

## Graphify

Runs at **ship** only (orge ship --step 1 / $forge:ship). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Implement** covers branch setup, waves, reviews, integration, documentation, handoff.
- Confirm plan availability (path or handoff) and readiness to execute.

## What you run (agent)

Run **implement** from the repo root beginning at step one; attach plan context when given. Continue stepwise; describe wave outcomes in prose—do not expose launcher argv.

---
