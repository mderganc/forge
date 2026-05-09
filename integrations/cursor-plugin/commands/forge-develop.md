---
name: forge:develop
description: Investigate the problem space before planning.
---

## What to tell the user first

- **Develop** explores the problem, options, and evidence before a formal plan.
- Ask what outcome they want (bug understanding, feature direction, tradeoffs) and whether **quick mode** is OK for a lighter pass.

Lead with goals and questions, not the shell line.

## What you run (agent)

Run `forge develop --step 1` from the repo root; add `--quick` when requested. Follow printed next-step commands and summarize each phase for the user.

## Exact CLI (reference)

- Start: `forge develop --step 1`
- Quick: `forge develop --step 1 --quick`
