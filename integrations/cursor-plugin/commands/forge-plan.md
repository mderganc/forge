---
name: forge:plan
description: Turn direction into a detailed implementation plan.
---

## What to tell the user first

- **Plan** builds an implementation plan: architecture, tasks, waves, risks, rollback, and documentation scope.
- Confirm they want to start a **new planning session** (or resume — point them at **forge:resume** if they already have state).
- Set expectations: you’ll work through **phased prompts**; you’ll recap outcomes between steps.

**Lead with** what they’ll get and the first decision (e.g. quick vs full review), **not** with a shell command.

## What you run (agent)

Run `forge plan --step 1` from the repo root (add `--quick` if they want abbreviated reviews). Continue with the **next command** the orchestrator prints until the workflow completes or they pause.

## Exact CLI (reference)

- Start: `forge plan --step 1`
- Quick: `forge plan --step 1 --quick`
