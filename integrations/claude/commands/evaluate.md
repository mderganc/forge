---
name: forge:evaluate
description: Review work against a plan (evaluate workflow).
---

## Hard rule — what the user sees

**Never show terminal commands.** Do not paste, bullet, or quote anything that looks like a shell invocation for this workflow (no argv, no flags list). Describe actions in plain English only (“Starting evaluate in post mode with your plan,” “Moving on to the completeness phase”).

If they explicitly ask “exact command for my terminal,” answer once, briefly.

## Graphify

Runs at **ship** only (forge ship --step 1 / $forge:ship). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Evaluate** walks through structured review phases (plan understanding, completeness, correctness, quality, operational readiness, discussion, report).
- Help them choose a **mode**: post-implementation, pre-implementation, or branch review without a plan.
- Confirm which **plan** applies (path or keywords), or review-only on the branch.
- After each phase, summarize **what you found** before continuing.

## What you run (agent)

Use your runner to execute the **evaluate** workflow from the repository root: begin at step one, apply the chosen mode and plan selection through the launcher’s normal flags, and advance whenever the orchestrator indicates the next step. Do **not** mirror launcher output that consists of command lines back into chat—paraphrase the next phase instead.

---
