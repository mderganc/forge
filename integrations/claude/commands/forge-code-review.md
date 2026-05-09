---
name: forge:code-review
description: Structured PR-style code review workflow.
---

## What to tell the user first

- **Code review** runs mode selection and structured passes (diff, deep dive, architecture, security, discussion, report).
- Ask what they’re reviewing (PR scope, branch, critical paths) and what risk they care about.

Lead with that framing, not the binary invocation.

## What you run (agent)

Run `forge code-review --step 1` from the repo root and follow orchestrator next-step commands. Give the user a concise recap after each major phase.

## Exact CLI (reference)

- Start: `forge code-review --step 1`
