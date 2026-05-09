---
name: forge:test
description: Run or author tests (including flows mode).
---

## What to tell the user first

- **Test** can **run** the suite or, in **flows** mode, scaffold and author end-to-end flows.
- Ask whether they want **default run** coverage work or **flows** authoring, and what failures or areas matter most.

Summarize the strategy before any command dump.

## What you run (agent)

Run `forge test --step 1` from the repo root; use `--mode flows` when they want scenario/flow work. Continue with orchestrator next-step commands; translate results into plain language.

## Exact CLI (reference)

- Run mode: `forge test --step 1`
- Flows mode: `forge test --mode flows --step 1`
