---
name: forge:implement
description: Execute an implementation plan in waves with reviews.
---

## What to tell the user first

- **Implement** drives branch setup, parallel **waves** of work, reviews, integration checks, documentation, and handoff.
- Confirm they have a **plan file** (or will detect it from handoff) and are ready to execute.
- Explain you’ll report **wave outcomes** and blockers in prose between steps.

**Do not** open with the raw start command.

## What you run (agent)

Run `forge implement --step 1` from the repo root; pass `--plan` on step 1 if they gave a path. Continue with orchestrator **next command** lines until done.

## Exact CLI (reference)

- Start: `forge implement --step 1`
