---
name: forge:diagnose
description: Structured root-cause analysis for bugs and incidents.
---

## What to tell the user first

- **Diagnose** runs a phased investigation: define the problem, gather evidence, break down causes, analyze, propose fixes, validate, report.
- Ask what **symptom** they’re chasing and whether they want **guided**, **autonomous**, or **interactive** pacing (if your launcher exposes `--mode`).
- Offer that you’ll **summarize each phase** before moving on.

**Do not** lead with the literal `forge diagnose …` line.

## What you run (agent)

Run `forge diagnose --step 1` from the repo root; pass `--mode` / `--quick` when the user chooses them. Follow printed next-step commands; translate orchestrator output into normal language for the user.

## Exact CLI (reference)

- Start: `forge diagnose --step 1`
