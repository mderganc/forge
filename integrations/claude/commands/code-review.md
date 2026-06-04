---
name: forge:code-review
description: Structured PR-style code review workflow.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

## Graphify

Runs at **ship** only (forge ship --step 1 / $forge:ship). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Code review** selects a mode and runs structured passes through discussion and report.
- Clarify scope (what changed, what matters most).

## What you run (agent)

Run **code-review** from the repo root at step one; recap each major phase without exposing argv.

---
